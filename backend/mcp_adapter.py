"""
mcp_adapter.py
~~~~~~~~~~~~~~

• Avvia un server MCP (Notion, in stdio tramite `npx`) e lo mantiene vivo
• Converte i tool MCP (JSON-Schema) in `BaseTool` LangChain asynchroni
• Cache localmente un'unica sessione per prestazioni
• Chiude tutto elegantemente con AsyncExitStack

Requisiti:
  pip install "langchain-core>=0.2" "mcp>=0.4" anyio python-dotenv
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import signal
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any, Coroutine, Dict, List, Type

from dotenv import load_dotenv
from langchain.tools import Tool
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, create_model, Field

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --------------------------------------------------------------------------- #
# Config & logging                                                            #
# --------------------------------------------------------------------------- #

load_dotenv()  # legge .env se presente

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("mcp-adapter")

MCP_STARTUP_TIMEOUT = float(os.getenv("MCP_STARTUP_TIMEOUT", 30.0))

# --------------------------------------------------------------------------- #
# Globals                                                                    #
# --------------------------------------------------------------------------- #

_MCP_SESSION: ClientSession | None = None
_EXIT_STACK: AsyncExitStack | None = None
_MCP_LOCK = asyncio.Lock()

# --------------------------------------------------------------------------- #
# Helper: avvia il processo MCP (una sola volta)                              #
# --------------------------------------------------------------------------- #


async def _create_session() -> ClientSession:
    """Lancia il server MCP via stdio e inizializza la sessione."""
    
    # 1. carico l'env del plugin dal file di config
    cfg_path = pathlib.Path("~/.codeium/windsurf/mcp_config.json").expanduser()
    env = json.loads(cfg_path.read_text())["mcpServers"]["notion-mcp-server"]["env"]

    # 2. preparo i parametri del processo stdio, passando un ambiente ISOLATO
    # Invece di aggiornare l'ambiente corrente, lo sostituiamo completamente
    # con quello definito nel file JSON per evitare conflitti.
    params = StdioServerParameters(
        command="/opt/homebrew/opt/node@20/bin/npx",
        args=["-y", "@notionhq/notion-mcp-server"],
        env=env.copy()  # Usare .copy() isola l'ambiente
    )

    logger.info("🐣  Lancio server Notion MCP (stdio)…")

    # gestiamo il CM correttamente con ExitStack
    global _EXIT_STACK
    if _EXIT_STACK is None:
        _EXIT_STACK = AsyncExitStack()

    # Entriamo nei contesti di stdio_client e ClientSession usando l'ExitStack
    # in modo che rimangano attivi per tutta la durata dell'applicazione.
    read, write = await _EXIT_STACK.enter_async_context(stdio_client(params))
    session = await _EXIT_STACK.enter_async_context(ClientSession(read, write))

    # L'inizializzazione viene gestita da ClientSession.__aenter__
    logger.info("🔗  Sessione MCP inizializzata")
    return session


@asynccontextmanager
async def get_mcp_session() -> ClientSession:
    """Ritorna la sessione cache-ata; se non esiste la crea in maniera thread-safe."""
    global _MCP_SESSION
    async with _MCP_LOCK:
        if _MCP_SESSION is None:
            _MCP_SESSION = await _create_session()

    try:
        yield _MCP_SESSION
    finally:
        # la lasciamo viva finché non chiudiamo ExitStack a fine processo
        pass


# --------------------------------------------------------------------------- #
# JSON-Schema ➜ Pydantic                                                      #
# --------------------------------------------------------------------------- #

_JSON_TYPE_MAP: Dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _schema_to_args_model(tool_name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
    if not schema:
        return create_model(f"{tool_name}Args")

    fields: Dict[str, tuple] = {}
    for name, props in schema.get("properties", {}).items():
        py_type = _JSON_TYPE_MAP.get(props.get("type", "string"), Any)
        default = props.get("default", ...)
        fields[name] = (py_type, default)
    return create_model(f"{tool_name}Args", **fields)


# --------------------------------------------------------------------------- #
# MCP ➜ LangChain                                                             #
# --------------------------------------------------------------------------- #


# Whitelist dei tool MCP da caricare per ridurre il context
_MCP_TOOL_WHITELIST = [
    "API-post-search",
    "API-patch-block-children",
    "API-retrieve-a-page",
    "API-patch-page",
]

# Descrizioni migliorate per i tool MCP
_TOOL_DESCRIPTION_OVERRIDES = {
    "API-post-search": "Use this tool to search for a page in Notion by its title. Perfect for when the user asks to find or search for a specific page. This is the first step before trying to modify a page.",
    "API-patch-page": "Use this tool to update the properties of a specific page, like its title, icon, or cover. You MUST provide a valid 'page_id'. If you don't have the page_id, use the 'API-post-search' tool first.",
    "API-patch-block-children": "Use this tool to add content (as blocks) to a specific page. This is the correct tool for adding notes or text. You MUST provide a valid 'page_id' for the parent page. If you don't have the page_id, use the 'API-post-search' tool first.",
}

class NotionSearchArgsSchema(BaseModel):
    """Input schema for the Notion search tool."""
    query: str = Field(description="The title of the page to search for in Notion.")

def _mcp_tool_to_langchain(defn: Dict[str, Any]) -> BaseTool:
    tool_name = defn.get("name", "unnamed")
    
    # Usa una descrizione migliorata se disponibile, altrimenti usa quella di default
    base_description = _TOOL_DESCRIPTION_OVERRIDES.get(tool_name, defn.get("description", "No description"))
    
    description = base_description
    
    # Log per debug
    if tool_name == "API-post-search":
        logger.info("Tool '%s' ha descrizione migliorata: '%s'", tool_name, description)
    
    ArgsModel = _schema_to_args_model(tool_name, defn.get("parameters", {}))

    async def tool_coroutine(**kwargs) -> Any:  # noqa: D401
        logger.debug("⚙️  Invoco %s con %s", tool_name, kwargs)
        try:
            async with get_mcp_session() as session:
                # La funzione call_tool si aspetta il dizionario di argomenti, non gli argomenti spacchettati.
                return await session.call_tool(tool_name, kwargs)
        except Exception as exc:
            logger.exception("Errore in %s", tool_name)
            # Restituisce un messaggio di errore chiaro e non ambiguo per l'LLM.
            # Questo evita che l'agente interpreti un JSON di errore come un risultato valido.
            return f"ERROR: The tool {tool_name} failed to execute. Please inform the user that there was a technical problem and they should try again later."

    # Se il tool è quello di ricerca, usa lo schema di argomenti specifico e robusto.
    # Altrimenti, usa il modello generato dinamicamente.
    schema = NotionSearchArgsSchema if tool_name == "API-post-search" else ArgsModel

    return StructuredTool.from_function(
        name=tool_name,
        description=description,
        args_schema=schema,
        coroutine=tool_coroutine,  # Usa la coroutine per l'esecuzione asincrona
    )


# --------------------------------------------------------------------------- #
# API pubblica                                                                 #
# --------------------------------------------------------------------------- #


async def load_mcp_tools() -> List[BaseTool]:
    """Carica i tool disponibili dal server MCP, filtrandoli con una whitelist."""
    logger.info("🛠️  Caricamento tool MCP...")
    try:
        async with get_mcp_session() as session:
            all_tools_response = await session.list_tools()
            all_tools_raw = all_tools_response.tools

            if not all_tools_raw:
                logger.warning("⚠️  Nessun tool MCP trovato.")
                return []

            # Filtra i tool in base alla whitelist per ridurre il context
            filtered_tools = [tool for tool in all_tools_raw if tool.name in _MCP_TOOL_WHITELIST]
            logger.info(f"🎁  Trovati {len(all_tools_raw)} tool MCP, caricati {len(filtered_tools)} dopo il filtro.")

            langchain_tools = [_mcp_tool_to_langchain(tool.model_dump()) for tool in filtered_tools]
            return langchain_tools

    except Exception as e:
        logger.error(f"💥 Errore durante il caricamento dei tool MCP: {e}")
        return []


# --------------------------------------------------------------------------- #
# Diagnostica standalone                                                       #
# --------------------------------------------------------------------------- #


async def _diagnostic() -> None:
    tools = await load_mcp_tools()
    for t in tools:
        logger.info("• %s | args=%s", t.name, list(t.args_schema.model_fields.keys()))

    # test facoltativo se esiste 'get-self'
    get_self = next((t for t in tools if t.name == "get-self"), None)
    if get_self:
        res = await get_self.arun({})
        logger.info("Risultato 'get-self': %s", res)


# --------------------------------------------------------------------------- #
# Graceful shutdown                                                            #
# --------------------------------------------------------------------------- #


def _setup_signal_handlers(loop: asyncio.AbstractEventLoop):
    def _handler(sig):
        logger.warning("Ricevuto %s: chiusura pulita…", sig.name)
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: _handler(s))


def _run_with_cleanup(coro: Coroutine[Any, Any, Any]):
    loop = asyncio.new_event_loop()
    _setup_signal_handlers(loop)
    try:
        loop.run_until_complete(coro)
    except asyncio.CancelledError:
        pass
    finally:
        if _EXIT_STACK is not None:
            loop.run_until_complete(_EXIT_STACK.aclose())
        loop.close()


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    _run_with_cleanup(_diagnostic())

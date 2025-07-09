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
from langchain_core.tools import BaseTool
from pydantic import BaseModel, create_model

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
    print(await session.list_tools())
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


def _mcp_tool_to_langchain(defn: Dict[str, Any]) -> BaseTool:
    tool_name = defn.get("name", "unnamed")
    description = defn.get("description", "No description")

    ArgsModel = _schema_to_args_model(tool_name, defn.get("parameters", {}))

    async def tool_coroutine(**kwargs) -> Any:  # noqa: D401
        logger.debug("⚙️  Invoco %s con %s", tool_name, kwargs)
        try:
            async with get_mcp_session() as session:
                return await session.invoke(tool_name, **kwargs)
        except Exception as exc:
            logger.exception("Errore in %s", tool_name)
            return f"Errore nell'esecuzione di {tool_name}: {exc}"

    return Tool(
        name=tool_name,
        description=description,
        func=tool_coroutine,
        coroutine=tool_coroutine,  # Specifichiamo anche la coroutine per l'esecuzione asincrona
        args_schema=ArgsModel,
    )


# --------------------------------------------------------------------------- #
# API pubblica                                                                 #
# --------------------------------------------------------------------------- #


async def load_mcp_tools() -> List[BaseTool]:
    """Ritorna la lista dei tool MCP convertiti in LangChain."""
    async with get_mcp_session() as session:
        # session.list_tools() ritorna un oggetto con un attributo .tools
        list_tools_response = await session.list_tools()
        tool_definitions = list_tools_response.tools
        
        # Convertiamo le definizioni dei tool in dizionari
        defs = [tool.model_dump() for tool in tool_definitions if tool]
    logger.info("🎁  Trovati %d tool MCP", len(defs))
    return [_mcp_tool_to_langchain(d) for d in defs]


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

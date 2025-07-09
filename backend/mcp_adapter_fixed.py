"""
mcp_adapter.py
~~~~~~~~~~~~~~

Questo modulo gestisce l'integrazione con i server MCP (Meta-Controller Protocol).

Funzionalità principali:
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
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, create_model, Field

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

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

_MCP_SESSION: Optional[ClientSession] = None
_SESSION_LOCK = asyncio.Lock()

# --------------------------------------------------------------------------- #
# Helper: avvia il processo MCP (una sola volta)                              #
# --------------------------------------------------------------------------- #

def _load_mcp_env_vars() -> Dict[str, str]:
    """Carica e adatta le variabili d'ambiente dal file mcp_config.json locale."""
    # Usa il file di configurazione locale invece di quello globale
    cfg_path = pathlib.Path(__file__).parent / "mcp_config.json"
    logger.info(f"Tentativo di caricare la configurazione MCP da: {cfg_path}")

    if not cfg_path.is_file():
        logger.error(f"File di configurazione non trovato al percorso: {cfg_path}")
        raise FileNotFoundError(f"Il file di configurazione MCP non è stato trovato in {cfg_path}")

    try:
        config_data = json.loads(cfg_path.read_text())
        logger.info("File di configurazione locale letto con successo.")

        # Legge la configurazione specifica dell'utente
        notion_api_config = config_data["mcpServers"]["notionApi"]["env"]
        headers_str = notion_api_config.get("OPENAPI_MCP_HEADERS", "{}")
        headers = json.loads(headers_str)
        auth_header = headers.get("Authorization", "")
        
        # Estrae il token Bearer
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            logger.info("NOTION_TOKEN estratto con successo da OPENAPI_MCP_HEADERS.")
            # Restituisce l'ambiente nel formato atteso dal resto del codice
            return {"NOTION_TOKEN": token}
        else:
            logger.error("Token di autorizzazione non trovato o in formato non valido.")
            raise ValueError("Authorization Bearer token non trovato in OPENAPI_MCP_HEADERS")

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Errore nella lettura o parsing del file {cfg_path}: {e}")
        raise



# --------------------------------------------------------------------------- #
# Entrypoint: gestione sessione e tool                                        #
# --------------------------------------------------------------------------- #

@asynccontextmanager
async def get_mcp_session() -> AsyncGenerator[ClientSession, None]:
    """Fornisce una sessione MCP globale, creandola se non esiste."""
    global _MCP_SESSION
    async with _SESSION_LOCK:
        if _MCP_SESSION and not _MCP_SESSION.is_closed:
            yield _MCP_SESSION
            return

        env = _load_mcp_env_vars()
        if not env.get("NOTION_TOKEN"):
            raise ValueError(
                "La variabile d'ambiente NOTION_TOKEN non è impostata. "
                "Impostala nel file ~/.codeium/windsurf/mcp_config.json"
            )

        # Legge il comando e gli argomenti dalla configurazione dell'utente
        notion_api_config = json.loads((pathlib.Path(__file__).parent / "mcp_config.json").read_text())["mcpServers"]["notionApi"]
        command = notion_api_config.get("command")
        args = notion_api_config.get("args", [])

        logger.info(f"Avvio del server MCP con: {command} {' '.join(args)}")

        params = StdioServerParameters(
            command=command,
            args=args,
            env=env,
            startup_timeout=MCP_STARTUP_TIMEOUT,
        )

        # Usa 'async with' per gestire il ciclo di vita del client e della sessione
        # come da documentazione ufficiale MCP.
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                _MCP_SESSION = session
                try:
                    yield session
                finally:
                    logger.info("Contesto get_mcp_session terminato. La sessione è gestita internamente.")


async def close_mcp_session():
    """Chiude la sessione MCP se esiste ed è aperta."""
    global _MCP_SESSION
    async with _SESSION_LOCK:
        if _MCP_SESSION and not _MCP_SESSION.is_closed:
            logger.info("Chiusura esplicita della sessione MCP...")
            await _MCP_SESSION.close()
            _MCP_SESSION = None
            logger.info("Sessione MCP chiusa esplicitamente.")

# Whitelist dei tool MCP da caricare per ridurre il context e migliorare la precisione
MCP_TOOL_WHITELIST = [
    "/API-post-search",
    "/API-patch-block-children",
    "/API-retrieve-a-page",
    "/API-patch-page",
]

# Mappa per rinominare i tool con nomi più intuitivi per l'LLM
RENAMED_TOOLS = {
    "API_post_search": "notion_search",
    "API_patch_block_children": "notion_add_content",
}

# Override delle descrizioni per migliorare la selezione da parte dell'LLM
_TOOL_DESCRIPTION_OVERRIDES = {
    "API-post-search": "Searches for pages in Notion. Use this to find the ID of a page before trying to modify it.",
    "API-patch-block-children": "Appends content to a specific Notion page. You MUST use this tool AFTER you have the page ID from a search. This tool requires the 'block_id' (the page_id) and 'children' (the content to add). You must ask the user for the content to add.",
}

class NotionSearchArgsSchema(BaseModel):
    """Input schema for the Notion search tool."""
    query: str = Field(..., description="The text to search for in Notion page titles.")

class NotionPatchArgsSchema(BaseModel):
    """Input schema for the Notion patch (add content) tool."""
    block_id: str = Field(..., description="The ID of the page (block) to which content should be added. This ID must be obtained from the search tool.")
    children: list = Field(..., description="A list of block objects to append as children. For simple text, you can pass a string which will be converted automatically.")


_TOOL_SCHEMA_OVERRIDES = {
    "API-post-search": NotionSearchArgsSchema,
    "API-patch-block-children": NotionPatchArgsSchema,
}

def _create_tool_from_mcp_definition(
    client: ClientSession,
    tool_name: str,
    defn: dict[str, Any],
) -> BaseTool:
    """Crea un BaseTool LangChain da una definizione di tool MCP."""

    def _create_pydantic_model(properties: dict) -> Type[BaseModel]:
        fields = {
            prop_name: (prop_info.get("type", "string"), Field(description=prop_info.get("description")))
            for prop_name, prop_info in properties.items()
        }
        return create_model(f"{tool_name}Args", **fields)

    original_tool_name = defn.get("operationId", "").replace("-", "_")
    tool_name = RENAMED_TOOLS.get(original_tool_name, original_tool_name)
    base_description = _TOOL_DESCRIPTION_OVERRIDES.get(original_tool_name, defn.get("description", "No description"))
    description = f"{base_description} Input schema: {json.dumps(defn.get('properties', {}))}"

    ArgsModel = _create_pydantic_model(defn.get("properties", {}))
    
    # Applica schemi Pydantic specifici per migliorare l'affidabilità
    schema = _TOOL_SCHEMA_OVERRIDES.get(original_tool_name, ArgsModel)

    def _wrapper(func):
        async def _wrapped_func(**kwargs):
            # Questo wrapper converte una semplice stringa per 'children' nel formato corretto che l'API di Notion si aspetta.
            if func.__name__ == 'API-patch-block-children' and 'children' in kwargs and isinstance(kwargs['children'], str):
                content = kwargs['children']
                kwargs['children'] = [
                    {
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        },
                    }
                ]
            
            # Log per debug richiesto dall'utente
            if func.__name__ == 'API-patch-block-children':
                logger.info(f"Executing tool '{func.__name__}' with payload: {kwargs}")

            return await func(**kwargs)
        _wrapped_func.__name__ = func.__name__
        return _wrapped_func

    async def tool_coro(**kwargs):
        return await client.execute(tool_name, kwargs)
    tool_coro.__name__ = tool_name

    wrapped_coro = _wrapper(tool_coro)

    return StructuredTool.from_function(
        name=tool_name,
        description=description,
        args_schema=schema,
        coroutine=wrapped_coro,
    )

async def get_mcp_tools() -> list[BaseTool]:
    """Carica i tool disponibili dal server MCP, filtrandoli con una whitelist."""
    logger.info("Caricamento tool MCP...")
    try:
        async with get_mcp_session() as session:
            all_tools_response = await session.list_tools()
            all_tools_raw = all_tools_response.tools

            if not all_tools_raw:
                logger.warning("Nessun tool MCP trovato.")
                return []

            # Filtra i tool in base alla whitelist per ridurre il context
            # La whitelist ora usa i nomi corretti, es: 'API-post-search'
            filtered_tools = [tool for tool in all_tools_raw if tool.name in _MCP_TOOL_WHITELIST]
            logger.info(f"Trovati {len(all_tools_raw)} tool MCP, caricati {len(filtered_tools)} dopo il filtro.")

            langchain_tools = []
            for tool in filtered_tools:
                tool_def = tool.model_dump()
                schema_override = _TOOL_SCHEMA_OVERRIDES.get(tool.name)
                langchain_tools.append(_mcp_tool_to_langchain(tool_def, schema_override=schema_override))
            
            return langchain_tools

    except Exception as e:
        logger.error(f"Errore durante il caricamento dei tool MCP: {e}", exc_info=True)
        return []

# Esempio di utilizzo e cleanup
async def main():
    print("Ottenimento dei tool MCP...")
    try:
        tools = await get_mcp_tools()
        print(f"Tool caricati ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
    finally:
        await close_mcp_session()

if __name__ == "__main__":
    # Gestione del segnale di interruzione (Ctrl+C)
    loop = asyncio.get_event_loop()
    main_task = loop.create_task(main())

    def signal_handler(sig, frame):
        print("Interruzione ricevuta, chiusura in corso...")
        asyncio.create_task(close_mcp_session())
        main_task.cancel()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        loop.run_until_complete(main_task)
    except asyncio.CancelledError:
        print("Task principale annullato.")

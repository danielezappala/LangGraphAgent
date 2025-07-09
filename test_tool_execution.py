# test_tool_execution.py

import asyncio
import logging
from typing import List

from langchain_core.messages import AIMessage, ToolCall
from langgraph.prebuilt import ToolNode

from backend.mcp_adapter import load_mcp_tools, _STACK

# Configura il logging per vedere i nostri messaggi
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
log = logging.getLogger("test")

async def main():
    """Test di esecuzione isolato per il ToolNode."""
    log.info("--- Inizio Test di Esecuzione ToolNode ---")

    try:
        # 1. Carichiamo i tool MCP, proprio come farebbe il grafo
        log.info("Caricamento tool MCP...")
        mcp_tools = await load_mcp_tools()
        if not mcp_tools:
            log.error("Nessun tool MCP caricato. Test fallito.")
            return
        log.info(f"{len(mcp_tools)} tool caricati con successo.")

        # 2. Creiamo un ToolNode, il componente di LangGraph che esegue i tool
        tool_node = ToolNode(mcp_tools)

        # 3. Simuliamo l'output dell'LLM: una richiesta di chiamare il nostro tool
        # Questo è l'input che il ToolNode riceverebbe nel grafo reale.
        fake_tool_call = ToolCall(
            name="API-post-search",
            args={"query": "Cose interessanti"},
            id="test_call_123"
        )
        input_message = AIMessage(content="", tool_calls=[fake_tool_call])

        log.info(f"Simulazione invocazione del ToolNode con: {input_message}")

        # 4. Invochiamo il ToolNode
        # Questa è l'operazione che sta fallendo silenziosamente nel chatbot.
        # Qui, vedremo l'errore esatto o il log di successo.
        # LangGraph nodes expect the graph's state (a dict) as input, not a single message.
        # The state contains the list of messages.
        graph_state_input = {"messages": [input_message]}
        result = tool_node.invoke(graph_state_input)

        log.info(f"--- Risultato del ToolNode ---")
        log.info(result)
        log.info("---------------------------------")

    except Exception as e:
        log.exception("!!! Test fallito con un'eccezione inattesa !!!")
    finally:
        # Pulizia delle risorse MCP
        if _STACK:
            log.info("Chiusura stack MCP...")
            await _STACK.aclose()
        log.info("--- Fine Test ---")

if __name__ == "__main__":
    asyncio.run(main())

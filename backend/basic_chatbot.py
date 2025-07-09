import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Carica le variabili d'ambiente
# Load environment variables
# Specifica il percorso del file .env nella stessa directory dello script
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)
api_key = os.getenv("OPENAI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")
if not api_key or not tavily_key:
    raise RuntimeError("Ensure OPENAI_API_KEY and TAVILY_API_KEY are in the .env file")
os.environ["OPENAI_API_KEY"] = api_key
os.environ["TAVILY_API_KEY"] = tavily_key

# Importa le definizioni del grafo e del checkpointer
from .graph_definition import build_graph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from .config import SQLITE_PATH

import asyncio

def main():
    asyncio.run(async_main())

async def async_main():
    """Main asynchronous function to run the chatbot CLI."""
    print("LangGraph Chatbot with TavilySearch tool and persistent memory.")
    print("Type 'exit' to quit.")

    # SqliteSaver.from_conn_string() restituisce un context manager.
    # Il grafo deve essere costruito e usato all'interno del blocco 'with'.
    # SqliteSaver.from_conn_string() returns a context manager.
    # The graph must be built and used within the 'with' block.
    async with AsyncSqliteSaver.from_conn_string(SQLITE_PATH) as checkpointer:
        
        # Il grafo viene costruito con il checkpointer attivo
        # The graph is built with the active checkpointer
        graph = await build_graph(checkpointer=checkpointer)

        # Imposta un ID di conversazione per la persistenza
        # Set a conversation ID for persistence
        thread_id = "1" # Start or continue conversation with ID "1"
        config = {"configurable": {"thread_id": thread_id}}

        while True:
            user_input = input(f"\n[{thread_id}] User: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break

            # L'input al grafo deve corrispondere alla struttura dello Stato
            # The input to the graph must match the State structure
            input_state = {"messages": [HumanMessage(content=user_input)]}
            
            print("--- Inizio esecuzione Grafo ---")
            # Usiamo stream_mode='updates' per avere un log dettagliato di ogni nodo eseguito
            async for update in graph.astream(input_state, config, stream_mode="updates"):
                for node_name, node_output in update.items():
                    print(f"[GRAFO] Eseguito nodo: '{node_name}'")
                    # Prettify e stampa l'output del nodo per chiarezza
                    if isinstance(node_output, dict) and 'messages' in node_output:
                        for message in node_output['messages']:
                            message.pretty_print()
                    else:
                        print(f"        Output: {node_output}")
                print("---")
            
            # L'output finale lo recuperiamo invocando lo stato finale del grafo
            final_state = await graph.aget_state(config)

            # Stampa la risposta finale dell'assistente
            # Print the final assistant response
            if final_state:
                final_messages = final_state.values.get("messages", [])
                if final_messages and isinstance(final_messages[-1], AIMessage) and final_messages[-1].content:
                    tool_name = None
                    # Controlla se un tool è stato usato prima del messaggio finale dell'AI
                    if len(final_messages) > 1 and isinstance(final_messages[-2], ToolMessage):
                        tool_name = final_messages[-2].name
                    
                    assistant_label = f"Assistant with {tool_name}" if tool_name else "Assistant"

                    print(f"[{thread_id}] {assistant_label}: {final_messages[-1].content}", flush=True)



if __name__ == "__main__":
    # L'adapter MCP usa il suo gestore di segnali per una chiusura pulita.
    # Per evitare conflitti, non usiamo il nostro _run_with_cleanup qui,
    # ma ci affidiamo al fatto che l'event loop di asyncio gestirà i segnali.
    main()

import os
from IPython.display import Image
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
from .helpers import pretty_print_messages

import asyncio
import os
import uuid

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
        graph = await build_graph(checkpointer=checkpointer)

        # Imposta un ID di conversazione per la persistenza
        thread_id = "1"  # Start or continue conversation with ID "1"
        config = {"configurable": {"thread_id": thread_id}}

        # Stampa la cronologia all'avvio
        try:
            if os.path.exists(SQLITE_PATH) and os.path.getsize(SQLITE_PATH) > 0:
                db_size_bytes = os.path.getsize(SQLITE_PATH)
                db_size_kb = db_size_bytes / 1024
                print(f"\n--- Cronologia Conversazione (Dimensione DB: {db_size_kb:.2f} KB) ---")
                
                history_state = await graph.aget_state(config)
                if history_state and history_state.values:
                    messages = history_state.values.get('messages')
                    if messages:
                        pretty_print_messages(messages)
                else:
                    print("Nessuna cronologia trovata per questo thread.")
                print("-----------------------------------------------------------------\n")
            else:
                print("\n--- Nessun file di cronologia trovato. Inizio una nuova conversazione. ---\n")
        except Exception as e:
            print(f"\nErrore nel caricamento della cronologia: {e}\n")

        # Ciclo di interazione con l'utente
        while True:
            user_input = input(f"\n[{thread_id}] User: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break

            # Esegui il grafo con l'input dell'utente
            input_state = {"messages": [HumanMessage(content=user_input)]}
            await graph.ainvoke(input_state, config)

            # Recupera lo stato finale e stampa l'ultimo messaggio dell'assistente
            # Stampa solo l'ultimo blocco di messaggi (la risposta finale)
            final_state = await graph.aget_state(config)
            if final_state and final_state.values:
                all_messages = final_state.values.get('messages', [])
                # Trova l'indice dell'ultimo HumanMessage
                last_human_message_index = -1
                for i in range(len(all_messages) - 1, -1, -1):
                    if isinstance(all_messages[i], HumanMessage):
                        last_human_message_index = i
                        break
                # Stampa dal penultimo messaggio umano in poi, se esiste
                if last_human_message_index != -1:
                    pretty_print_messages(all_messages[last_human_message_index:])
            
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

                    # print(f"[{thread_id}] {assistant_label}: {final_messages[-1].content}", flush=True)



if __name__ == "__main__":
    # L'adapter MCP usa il suo gestore di segnali per una chiusura pulita.
    # Per evitare conflitti, non usiamo il nostro _run_with_cleanup qui,
    # ma ci affidiamo al fatto che l'event loop di asyncio gestirà i segnali.
    main()

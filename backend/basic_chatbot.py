import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Carica le variabili d'ambiente
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")
if not api_key or not tavily_key:
    raise RuntimeError("Assicurati che OPENAI_API_KEY e TAVILY_API_KEY siano nel file .env")
os.environ["OPENAI_API_KEY"] = api_key
os.environ["TAVILY_API_KEY"] = tavily_key

# Importa le definizioni del grafo e del checkpointer
from .graph_definition import build_graph
from langgraph.checkpoint.sqlite import SqliteSaver
from .config import SQLITE_PATH

def main():
    """Funzione principale per eseguire la CLI del chatbot."""
    print("Chatbot LangGraph con tool TavilySearch e memoria persistente.")
    print("Scrivi 'exit' per uscire.")

    # SqliteSaver.from_conn_string() restituisce un context manager.
    # Il grafo deve essere costruito e usato all'interno del blocco 'with'.
    with SqliteSaver.from_conn_string(SQLITE_PATH) as checkpointer:
        
        # Il grafo viene costruito con il checkpointer attivo
        graph = build_graph(checkpointer=checkpointer)

        # Imposta un ID di conversazione per la persistenza
        thread_id = "1" # Inizia o continua la conversazione con ID "1"
        config = {"configurable": {"thread_id": thread_id}}

        while True:
            user_input = input(f"\n[{thread_id}] Utente: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Arrivederci!")
                break

            # L'input al grafo deve corrispondere alla struttura dello Stato
            input_state = {"messages": [HumanMessage(content=user_input)]}
            
            final_state = None
            # Esegui il grafo in streaming per vedere i passaggi intermedi
            for event in graph.stream(input_state, config, stream_mode="values"):
                messages = event.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if isinstance(last_message, AIMessage) and last_message.tool_calls:
                        print(f"[GRAFO] L'assistente ha deciso di usare un tool...", flush=True)
                    elif isinstance(last_message, ToolMessage):
                        print(f"[GRAFO]   -> Eseguito tool: '{last_message.name}'", flush=True)
                final_state = event

            # Stampa la risposta finale dell'assistente
            if final_state:
                final_messages = final_state.get("messages", [])
                if final_messages and isinstance(final_messages[-1], AIMessage) and final_messages[-1].content:
                    print(f"[{thread_id}] Assistente: {final_messages[-1].content}", flush=True)

if __name__ == "__main__":
    main()

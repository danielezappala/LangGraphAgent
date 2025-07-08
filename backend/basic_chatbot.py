import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Carica le variabili d'ambiente
# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")
if not api_key or not tavily_key:
    raise RuntimeError("Ensure OPENAI_API_KEY and TAVILY_API_KEY are in the .env file")
os.environ["OPENAI_API_KEY"] = api_key
os.environ["TAVILY_API_KEY"] = tavily_key

# Importa le definizioni del grafo e del checkpointer
from .graph_definition import build_graph
from langgraph.checkpoint.sqlite import SqliteSaver
from .config import SQLITE_PATH

def main():
    """Main function to run the chatbot CLI."""
    print("LangGraph Chatbot with TavilySearch tool and persistent memory.")
    print("Type 'exit' to quit.")

    # SqliteSaver.from_conn_string() restituisce un context manager.
    # Il grafo deve essere costruito e usato all'interno del blocco 'with'.
    # SqliteSaver.from_conn_string() returns a context manager.
    # The graph must be built and used within the 'with' block.
    with SqliteSaver.from_conn_string(SQLITE_PATH) as checkpointer:
        
        # Il grafo viene costruito con il checkpointer attivo
        # The graph is built with the active checkpointer
        graph = build_graph(checkpointer=checkpointer)

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
            
            final_state = None
            # Esegui il grafo in streaming per vedere i passaggi intermedi
            # Stream the graph to see intermediate steps
            for event in graph.stream(input_state, config, stream_mode="values"):
                messages = event.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if isinstance(last_message, AIMessage) and last_message.tool_calls:
                        print(f"[GRAPH] Assistant decided to use a tool...", flush=True)
                    elif isinstance(last_message, ToolMessage):
                        print(f"[GRAPH]   -> Executed tool: '{last_message.name}'", flush=True)
                final_state = event

            # Stampa la risposta finale dell'assistente
            # Print the final assistant response
            if final_state:
                final_messages = final_state.get("messages", [])
                if final_messages and isinstance(final_messages[-1], AIMessage) and final_messages[-1].content:
                    print(f"[{thread_id}] Assistant: {final_messages[-1].content}", flush=True)

if __name__ == "__main__":
    main()

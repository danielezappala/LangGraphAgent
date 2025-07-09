import asyncio
import logging

from backend.mcp_adapter import load_mcp_tools

# Configura il logging per vedere i messaggi INFO
logging.basicConfig(level=logging.INFO)

async def main():
    """Carica i tool e testa direttamente API-post-search."""
    print("--- Inizio Test Singolo Tool ---")
    
    # Carichiamo tutti i tool
    all_tools = await load_mcp_tools()
    
    # Troviamo il nostro tool specifico
    search_tool = next((t for t in all_tools if t.name == "API-post-search"), None)
    
    if not search_tool:
        print("ERRORE: Tool 'API-post-search' non trovato.")
        return

    print(f"Trovato tool: {search_tool.name}")
    print("Invocazione diretta del tool...")
    
    # Invochiamo direttamente il metodo _arun, bypassando l'agente
    try:
        result = await search_tool._arun(query="Cose interessanti")
        print("\n--- RISULTATO DEL TEST ---")
        print(result)
        print("------------------------")
    except Exception as e:
        print(f"\n--- ERRORE DURANTE IL TEST ---")
        logging.exception(e)
        print("-----------------------------")

if __name__ == "__main__":
    asyncio.run(main())

# Agente Conversazionale con LangGraph, FastAPI e Notion

Questo progetto implementa un agente conversazionale avanzato utilizzando un'architettura moderna basata su LangGraph per la logica dell'agente, FastAPI per il backend e un'interfaccia React per il frontend. L'agente è in grado di utilizzare tool esterni, inclusa un'integrazione con Notion tramite MCP (Model Context Protocol).

---

## Architettura del Progetto

La codebase è suddivisa in due componenti principali: `backend` e `frontend`.

### Backend

Il backend è un'applicazione FastAPI che orchestra la logica dell'agente.

```
backend/
├── server.py               # Entry point del server FastAPI, gestisce il ciclo di vita e l'endpoint /chat.
├── graph_definition.py     # Cuore dell'agente: definisce lo stato, i nodi e la struttura del grafo LangGraph.
├── tools.py                # Definisce i tool statici a disposizione dell'agente (es. Tavily Search).
├── mcp_config.json         # Configurazione per i server MCP (es. Notion) per caricare tool dinamici.
├── chatbot_memory.sqlite   # Database SQLite per la persistenza della cronologia delle conversazioni.
└── .env                    # File per le variabili d'ambiente (API keys).
```

### Frontend

Il frontend è un'applicazione React che fornisce l'interfaccia utente per la chat (dettagli omessi).

---

## Avvio Rapido

### 1. Prerequisiti

- Python 3.9+
- Node.js e npm

### 2. Configurazione Backend

1.  **Crea le variabili d'ambiente**: Nella directory `backend`, crea un file `.env` e aggiungi le tue API key:
    ```
    OPENAI_API_KEY="sk-..."
    TAVILY_API_KEY="tvly-..."
    
    # Esempio per Notion MCP
    OPENAPI_MCP_HEADERS='{"notionApi": {"Authorization": "Bearer SECRET_...", "Notion-Version": "2022-06-28"}}'
    ```

2.  **Installa le dipendenze Python**: Dalla root del progetto, esegui:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Avvia il server backend**: Dalla root del progetto, esegui:
    ```bash
    uvicorn backend.server:app --reload
    ```
    Il server sarà in ascolto su `http://127.0.0.1:8000`.

### 3. Configurazione Frontend

1.  **Installa le dipendenze Node.js**: Spostati nella directory `frontend`:
    ```bash
    cd frontend
    npm install
    ```

2.  **Avvia il server di sviluppo**: 
    ```bash
    npm start
    ```
    L'interfaccia sarà accessibile su `http://localhost:3000`.

---

## Concetti Chiave

- **LangGraph**: La logica dell'agente è modellata come un grafo di stati. Questo permette un controllo preciso sul flusso della conversazione e sull'esecuzione dei tool.
- **FastAPI**: Fornisce un server web asincrono, robusto e performante per esporre l'agente tramite un'API REST.
- **Persistenza**: La cronologia delle conversazioni è salvata in un database SQLite tramite il checkpointer `AsyncSqliteSaver` di LangGraph, garantendo che lo stato venga mantenuto tra le sessioni.
- **MCP (Model Context Protocol)**: Utilizzato per caricare dinamicamente tool esterni, come quelli per Notion, basandosi su un file di configurazione `mcp_config.json`. 
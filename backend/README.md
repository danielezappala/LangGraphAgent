# Agente Conversazionale con LangGraph, FastAPI e Notion

Questo progetto implementa un agente conversazionale avanzato utilizzando un'architettura moderna basata su LangGraph per la logica dell'agente, FastAPI per il backend e un'interfaccia React per il frontend. L'agente è in grado di utilizzare tool esterni, inclusa un'integrazione con Notion tramite MCP (Model Context Protocol).

---

## Architettura del Progetto

La codebase è suddivisa in due componenti principali: `backend` e `frontend`.

### Backend

Il backend è un'applicazione FastAPI che orchestra la logica dell'agente.

```
backend/
├── run.py                       # Entry point per avvio server
├── database.py                  # Layer di compatibilità database
├── version.py                   # Informazioni versione
├── mcp_config.json             # Configurazione server MCP
├── requirements.txt            # Dipendenze Python
├── api/                       # Endpoint FastAPI
│   ├── providers.py           # Gestione provider LLM
│   └── history.py             # Cronologia chat
├── core/                      # Logica di business principale
│   ├── app.py                 # Applicazione FastAPI principale
│   ├── env_loader.py          # Configurazione ambiente
│   ├── database/              # Core database
│   │   └── unified_database.py # Implementazione database unificato
│   ├── langgraph/             # Workflow LangGraph
│   │   └── graph_definition.py # Definizione grafo agente
│   └── tools/                 # Tool LangChain
│       └── tools.py           # Implementazione tool
├── services/                  # Servizi business
│   ├── bootstrap_service.py   # Bootstrap applicazione
│   └── provider_service.py    # Gestione provider
├── tests/                     # Suite di test
│   ├── unit/                  # Test unitari
│   ├── integration/           # Test integrazione
│   └── performance/           # Test performance
├── utils/                     # Funzioni utility
└── data/                      # File database
    └── unified_app.sqlite     # Database principale
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
- **MCP (Model Context Protocol)**: Utilizzato per caricare dinamicamente tool esterni, come quelli per Notion, basandosi su un file di configurazione `mcp_config.json`. Al momento i server MCP vengono lanciati in Windsurf tramite il comando `python -m langgraph.mcp.server`
Se il server non si avvia prova questa procedura:
Crea un link simbolico a quel file nella cartella /usr/local/bin/. Copia e incolla questo comando:

Bash

    sudo ln -s "$(which node)" /usr/local/bin/node


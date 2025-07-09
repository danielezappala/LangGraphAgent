import asyncio
import os
import sqlite3
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime, timezone

# Importa i router API
from .api import history as history_router

from .graph_definition import build_graph
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "chatbot_memory.sqlite")
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import HumanMessage



def init_db():
    """Inizializza il database SQLite con le tabelle necessarie."""
    db_path = os.path.join(os.path.dirname(__file__), "chatbot_memory.sqlite")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crea tabella delle conversazioni
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Crea tabella dei messaggi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    )
    """)
    
    # Crea indici per migliorare le prestazioni
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
    
    conn.commit()
    conn.close()

# --- Gestione del ciclo di vita dell'app (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Codice eseguito all'avvio
    print("Avvio del server in corso...")
    
    # Inizializza il database
    init_db()
    print("Database inizializzato.")
    
    # Inizializza il checkpointer come un context manager asincrono
    async with AsyncSqliteSaver.from_conn_string(SQLITE_PATH) as checkpointer:
        # Inizializza il grafo e lo salva nello stato dell'app
        app.state.graph = await build_graph(checkpointer=checkpointer)
        print("Grafo inizializzato e pronto.")
        yield
    # Codice eseguito allo spegnimento (opzionale)
    print("Server in fase di spegnimento.")

# --- App FastAPI ---
app = FastAPI(
    title="LangGraph Chatbot Server",
    version="1.0",
    description="API server for the LangGraph chatbot with Notion integration.",
    lifespan=lifespan  # Registra la funzione di lifespan
)

# --- CORS Middleware ---
# Permette al frontend (es. http://localhost:3000) di comunicare con questo server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Per debug, accetta tutte le origini
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modelli Pydantic per le richieste/risposte ---
class ChatRequest(BaseModel):
    message: str
    thread_id: str = "1" # Usiamo un thread_id fisso per ora

class ChatResponse(BaseModel):
    response: str

# --- Endpoint API ---
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    """
    Riceve un messaggio dall'utente, lo processa con il grafo LangGraph
    e restituisce la risposta dell'assistente.
    """
    try:
        # Ottieni il grafo dallo stato dell'app
        graph = request.app.state.graph
        
        # Lo stato contiene solo i messaggi; la configurazione della chiamata contiene il thread_id
        input_state = {"messages": [{"role": "user", "content": chat_request.message}]}
        config = {"configurable": {"thread_id": chat_request.thread_id}}
        
        print(f"INVOKING GRAPH with thread_id: {chat_request.thread_id}")
        
        # Esegui il grafo in modo asincrono passando lo stato e la configurazione
        result = await graph.ainvoke(input_state, config)
        
        # Estrai l'ultimo messaggio dell'assistente
        last_message = result["messages"][-1]
        
        # Salva la conversazione nel database
        await save_conversation("default_conversation", [
            {"role": "user", "content": chat_request.message, "timestamp": datetime.now(timezone.utc).isoformat()},
            {"role": "assistant", "content": last_message.content, "timestamp": datetime.now(timezone.utc).isoformat()}
        ])
        
        return {"response": last_message.content}
        
    except Exception as e:
        return {"response": f"Si è verificato un errore: {str(e)}"}

# --- Funzioni di utilità per la gestione della cronologia ---

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), "chatbot_memory.sqlite")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

async def save_conversation(conversation_id: str, messages: List[dict]):
    """Salva una conversazione nel database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Inserisci o aggiorna la conversazione
        cursor.execute(
            """
            INSERT INTO conversations (id, title, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                updated_at = excluded.updated_at
            """,
            (conversation_id, messages[0]["content"][:100], datetime.now(timezone.utc).isoformat())
        )
        
        # Inserisci i messaggi
        for msg in messages:
            cursor.execute(
                """
                INSERT INTO messages (conversation_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (conversation_id, msg["role"], msg["content"], msg["timestamp"])
            )
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Errore nel salvataggio della conversazione: {e}")
        return False
    finally:
        conn.close()

# Includi i router API
app.include_router(history_router.router)

# --- Esecuzione del server ---
# Per eseguire: uvicorn backend.server:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

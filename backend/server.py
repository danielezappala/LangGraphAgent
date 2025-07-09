import asyncio
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from .graph_definition import build_graph
from .config import SQLITE_PATH
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import HumanMessage



# --- Gestione del ciclo di vita dell'app (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Codice eseguito all'avvio
    print("Avvio del server in corso...")
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
async def chat_endpoint(request: Request):
    """
    Riceve un messaggio dall'utente, lo processa con il grafo LangGraph
    e restituisce la risposta dell'assistente.
    """
    chat_request = ChatRequest.model_validate(await request.json())
    graph = request.app.state.graph
    
    config = {"configurable": {"thread_id": chat_request.thread_id}}
    input_state = {"messages": [HumanMessage(content=chat_request.message)]}
    
    # Esegui il grafo
    await graph.ainvoke(input_state, config)
    
    # Recupera lo stato finale
    final_state = await graph.aget_state(config)
    
    if final_state and final_state.values:
        final_messages = final_state.values.get('messages', [])
        if final_messages:
            last_message = final_messages[-1]
            return ChatResponse(response=last_message.content)
            
    return ChatResponse(response="Sorry, I couldn't get a response.")

# --- Esecuzione del server ---
# Per eseguire: uvicorn backend.server:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

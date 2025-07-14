import os
from contextlib import asynccontextmanager
import pathlib
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import sys

# Import dei moduli API
from api import chat, ping, history
from api.version_router import router as version_router

# Import relativi standard per un'applicazione FastAPI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from version import __version__
from graph_definition import build_graph

# --- Configurazione dell'applicazione FastAPI ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestisce l'avvio e lo spegnimento del server."""
    print("Avvio del server in corso...")
    load_dotenv(dotenv_path=pathlib.Path(__file__).parent / '.env')

    # Inizializza il checkpointer per la persistenza del database SQLite.
    db_path = pathlib.Path(__file__).parent / "data" / "chatbot_memory.sqlite"
    db_path.parent.mkdir(exist_ok=True)

    # Crea il context manager per il checkpointer
    checkpointer_cm = AsyncSqliteSaver.from_conn_string(str(db_path))

    # Entra nel contesto del checkpointer e lo rende disponibile per tutta la durata dell'app
    async with checkpointer_cm as checkpointer:
        app.state.checkpointer = checkpointer
        
        # Costruisce il grafo con il checkpointer attivo
        graph = await build_graph(checkpointer)
        app.state.graph = graph
        
        print(f"Backend version: {__version__}")
        print("Grafo e checkpointer inizializzati e pronti.")
        
        yield

    print("Server in fase di spegnimento.")

app = FastAPI(
    title="LangGraph Chatbot Server",
    description="API server for the LangGraph chatbot with Notion integration.",
    version=__version__,
    lifespan=lifespan
)

# --- Configurazione CORS ---
# Definisce le origini autorizzate a effettuare richieste al backend.
# Questo è fondamentale per permettere al frontend (in esecuzione su localhost:9002) di comunicare.
origins = [
    "http://localhost:9002",
    "http://127.0.0.1:9002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configurazione e Inclusione dei Router API ---

# Creiamo un router principale per l'API con il prefisso /api
api_router = APIRouter(prefix="/api")

# Includiamo i router specifici nel router principale
# Questo approccio (router nidificati) è la best practice per evitare conflitti.
api_router.include_router(ping.router)       # ping.py non ha un prefisso, quindi la rotta sarà /api/ping
api_router.include_router(history.router)     # history.py ha il prefisso /history
api_router.include_router(chat.router)        # chat.py ha il prefisso /chat
api_router.include_router(version_router)     # version_router.py ha il prefisso /version

# Infine, includiamo il router principale nell'applicazione
app.include_router(api_router)

# Gestore globale delle eccezioni
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    print("--- Inizio Traceback Errore Globale ---")
    traceback.print_exc()
    print("--- Fine Traceback Errore Globale ---")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": f"Errore interno del server: {exc}"},
    )

# Print key environment information at startup
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

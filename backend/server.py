import os
from contextlib import asynccontextmanager
import pathlib
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Request, status, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import sys
from sqlalchemy.orm import Session

# Import database models to create tables
from database import engine, Base, get_db

# Import dei moduli API
from api import chat, ping, history
from api.version_router import router as version_router
from api.config import router as config_router
from api.providers import router as providers_router, get_active_provider_config, update_environment_vars

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

    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Initialize database session
    db = next(get_db())
    
    # Check if we have an active provider, if not, try to set one
    active_provider = get_active_provider_config(db)
    if active_provider:
        print(f"Active provider: {active_provider.name} ({active_provider.provider_type})")
        update_environment_vars(active_provider)
    else:
        print("Warning: No active provider configured. Please set up a provider in the settings.")
    
    # Close the database session
    db.close()

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
    title="LangGraph Agent API",
    description="API for the LangGraph Agent application.",
    version=__version__,
    lifespan=lifespan,
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configurazione e Inclusione dei Router API ---

# Includi i router delle API
app.include_router(version_router)
app.include_router(config_router)
app.include_router(providers_router, prefix="/api/providers", tags=["providers"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(ping.router, prefix="/api/ping", tags=["ping"])
app.include_router(history.router, prefix="/api/history", tags=["history"])

# Add database middleware
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    """Middleware to manage database sessions for each request."""
    response = None
    try:
        request.state.db = next(get_db())
        response = await call_next(request)
    except Exception as e:
        print(f"Database error: {e}")
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error - database connection failed"}
        )
    finally:
        if hasattr(request.state, 'db'):
            request.state.db.close()
    return response
    print(f"Errore durante l'inclusione dei router: {e}")
    raise

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

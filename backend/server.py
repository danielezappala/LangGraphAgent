import os
from contextlib import asynccontextmanager
import pathlib

# Load environment variables using centralized loader
from core.env_loader import EnvironmentLoader
EnvironmentLoader.load_environment()
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sys

# Import unified database system
from unified_database import get_unified_db, UnifiedAsyncSqliteSaver

# Import dei moduli API
from api import chat, ping, history
from api.version_router import router as version_router

from api.providers import router as providers_router

from version import __version__
from graph_definition import build_graph

# --- Helper Functions ---

def _update_runtime_env_vars(provider_config: dict):
    """Update environment variables for LLM runtime compatibility."""
    try:
        os.environ["LLM_PROVIDER"] = provider_config['provider_type']
        
        if provider_config['provider_type'] == "openai":
            os.environ["OPENAI_API_KEY"] = provider_config['api_key']
            if provider_config.get('model'):
                os.environ["OPENAI_MODEL"] = provider_config['model']
        elif provider_config['provider_type'] == "azure":
            os.environ["AZURE_OPENAI_API_KEY"] = provider_config['api_key']
            if provider_config.get('endpoint'):
                os.environ["AZURE_OPENAI_ENDPOINT"] = provider_config['endpoint']
            if provider_config.get('deployment'):
                os.environ["AZURE_OPENAI_DEPLOYMENT"] = provider_config['deployment']
            if provider_config.get('model'):
                os.environ["AZURE_OPENAI_MODEL"] = provider_config['model']
            if provider_config.get('api_version'):
                os.environ["AZURE_OPENAI_API_VERSION"] = provider_config['api_version']
        
        print(f"Runtime environment variables updated for {provider_config['provider_type']} provider")
        
    except Exception as e:
        print(f"Error updating runtime environment variables: {e}")

# --- Configurazione dell'applicazione FastAPI ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestisce l'avvio e lo spegnimento del server."""
    print("Avvio del server in corso...")

    # Initialize unified database system
    unified_db = get_unified_db()
    print(f"Unified database initialized at: {unified_db.db_path}")
    
    # Initialize database session using unified database
    db = unified_db.get_session()
    
    try:
        # Run bootstrap process if needed (Database-First approach)
        from services.bootstrap_service import get_bootstrap_service
        bootstrap_service = get_bootstrap_service(db)
        bootstrap_service.run_bootstrap_if_needed()
        
        # Get active provider from database (single source of truth)
        from services.provider_service import get_provider_service
        provider_service = get_provider_service(db)
        active_provider_config = provider_service.get_active_provider()
        
        if active_provider_config:
            print(f"Active provider: {active_provider_config['name']} ({active_provider_config['provider_type']})")
            # Update environment variables for LLM runtime compatibility
            _update_runtime_env_vars(active_provider_config)
        else:
            print("Warning: No active provider configured. Please set up a provider in the settings.")
    
    finally:
        # Close the database session
        db.close()

    # Initialize unified checkpointer using the same database
    checkpointer = UnifiedAsyncSqliteSaver(unified_db)
    print("Unified checkpointer initialized using unified database")

    # Store checkpointer and unified database in app state
    app.state.checkpointer = checkpointer
    app.state.unified_db = unified_db
    
    # Costruisce il grafo con il checkpointer attivo
    graph = await build_graph(checkpointer)
    app.state.graph = graph
    
    print(f"Backend version: {__version__}")
    print("Grafo e checkpointer inizializzati e pronti con unified database.")
    
    yield

    print("Server in fase di spegnimento.")
    # Clean up unified database connections
    unified_db.close()

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
app.include_router(version_router, prefix="/api/version", tags=["version"])

app.include_router(providers_router, prefix="/api/providers", tags=["providers"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(ping.router, prefix="/api/ping", tags=["ping"])
app.include_router(history.router, prefix="/api/history", tags=["history"])

# Add database middleware
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    """Middleware to manage database sessions for each request using unified database."""
    response = None
    try:
        # Use unified database for session management
        unified_db = get_unified_db()
        request.state.db = unified_db.get_session()
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

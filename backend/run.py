#!/usr/bin/env python3
"""
Script di avvio personalizzato per il server FastAPI.
Utilizza le variabili d'ambiente per la configurazione.
"""
import os
from dotenv import load_dotenv
import uvicorn
from server import app

if __name__ == "__main__":
    # Carica le variabili d'ambiente
    # Prima carica il file .env nella directory principale (condiviso)
    load_dotenv()
    # Poi sovrascrivi con le variabili specifiche del backend
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)
    
    # Leggi la configurazione con valori di default
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    
    print(f"Avvio backend su {host}:{port}")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

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
    load_dotenv()
    
    # Leggi la configurazione con valori di default
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "30010"))
    
    print(f"Avvio backend su {host}:{port}")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

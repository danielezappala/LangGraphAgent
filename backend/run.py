#!/usr/bin/env python3
"""
Script di avvio personalizzato per il server FastAPI.
Utilizza le variabili d'ambiente per la configurazione.
"""
import uvicorn
from core.env_loader import EnvironmentLoader

if __name__ == "__main__":
    # Load environment variables using centralized loader
    EnvironmentLoader.load_environment()
    
    # Get API configuration
    api_config = EnvironmentLoader.get_api_config()
    host = api_config['host']
    port = api_config['port']
    
    print(f"Avvio backend su {host}:{port}")
    
    uvicorn.run(
        "core.app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

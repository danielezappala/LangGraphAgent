#!/usr/bin/env python3
"""
Script per sincronizzare le variabili d'ambiente tra i vari file .env

Utilizzo:
    python sync_env.py [--dry-run] [--force]

Opzioni:
    --dry-run   Mostra le modifiche che verrebbero apportate senza modificarle
    --force     Forza la sovrascrittura dei file esistenti
"""
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

# Percorsi dei file
ROOT_DIR = Path(__file__).parent
ROOT_ENV = ROOT_DIR / ".env"
ROOT_ENV_EXAMPLE = ROOT_DIR / ".env.example"
BACKEND_ENV = ROOT_DIR / "backend" / ".env"
BACKEND_ENV_EXAMPLE = ROOT_DIR / "backend" / ".env.example"
FRONTEND_ENV = ROOT_DIR / "frontend" / ".env"
FRONTEND_ENV_EXAMPLE = ROOT_DIR / "frontend" / ".env.example"

# Mappa delle variabili per ogni file
ENV_VARIABLES = {
    "root": {
        "file": ROOT_ENV,
        "example": ROOT_ENV_EXAMPLE,
        "variables": {
            "NEXT_PUBLIC_API_BASE_URL": "http://localhost:8000",
            "BACKEND_PORT": "8000",
            "FRONTEND_PORT": "9002",
        },
    },
    "backend": {
        "file": BACKEND_ENV,
        "example": BACKEND_ENV_EXAMPLE,
        "variables": {
            "LLM_PROVIDER": "azure",
            "OPENAI_API_KEY": "your_openai_api_key_here",
            "AZURE_OPENAI_API_KEY": "your_azure_openai_key_here",
            "AZURE_OPENAI_ENDPOINT": "your_azure_openai_endpoint_here",
            "AZURE_OPENAI_DEPLOYMENT": "your_deployment_name_here",
            "AZURE_OPENAI_API_VERSION": "2024-12-01-preview",
            "TAVILY_API_KEY": "your_tavily_api_key_here",
            "NOTION_API_KEY": "your_notion_api_key_here",
        },
    },
    "frontend": {
        "file": FRONTEND_ENV,
        "example": FRONTEND_ENV_EXAMPLE,
        "variables": {
            "NEXT_PUBLIC_APP_NAME": "LangGraph Agent",
            "NEXT_PUBLIC_APP_ENV": "development",
            "NEXT_PUBLIC_ENABLE_ANALYTICS": "false",
            "NEXT_PUBLIC_GOOGLE_ANALYTICS_ID": "",
            "NEXT_PUBLIC_DEFAULT_MODEL": "",
            "NEXT_PUBLIC_DEFAULT_API_VERSION": "",
        },
    },
}

def parse_env_file(file_path: Path) -> Dict[str, str]:
    """Analizza un file .env e restituisce un dizionario con le variabili."""
    if not file_path.exists():
        return {}
    
    env_vars = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Ignora commenti e righe vuote
            if not line or line.startswith('#') or '=' not in line:
                continue
            
            # Dividi la riga in chiave e valore
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip().strip('"\'')
    
    return env_vars

def write_env_file(file_path: Path, variables: Dict[str, str], example: bool = False):
    """Scrive un file .env con le variabili specificate."""
    if example and file_path.exists() and not example:
        # Crea un backup del file esistente
        backup_path = file_path.with_suffix('.env.bak')
        shutil.copy2(file_path, backup_path)
        print(f"  - Backup creato: {backup_path}")
    
    with open(file_path, 'w') as f:
        for key, value in variables.items():
            # Se è un file di esempio, usa i valori di esempio
            if example:
                value = ENV_VARIABLES.get(file_path.parent.name, {}).get("variables", {}).get(key, value)
            
            # Scrivi la variabile nel file
            f.write(f"{key}={value}\n")
    
    print(f"  - File {'example ' if example else ''}aggiornato: {file_path}")

def sync_env(dry_run: bool = False, force: bool = False):
    """Sincronizza i file .env in base alla configurazione."""
    print("Sincronizzazione file .env...")
    
    # Per ogni ambiente, verifica e aggiorna i file .env
    for env_name, env_data in ENV_VARIABLES.items():
        print(f"\n=== {env_name.upper()} ===")
        env_file = env_data["file"]
        example_file = env_data["example"]
        
        # Crea il file .env.example se non esiste
        if not example_file.exists() or force:
            print(f"Creazione file di esempio: {example_file}")
            if not dry_run:
                write_env_file(example_file, env_data["variables"], example=True)
        
        # Crea il file .env se non esiste o se forzato
        if (not env_file.exists() or force) and not dry_run:
            print(f"Creazione file: {env_file}")
            # Usa i valori esistenti se il file esiste, altrimenti i valori di default
            if env_file.exists():
                existing_vars = parse_env_file(env_file)
                # Mantieni i valori esistenti, aggiungi quelli mancanti
                for key, value in env_data["variables"].items():
                    if key not in existing_vars:
                        existing_vars[key] = value
                write_env_file(env_file, existing_vars)
            else:
                write_env_file(env_file, env_data["variables"])
        elif dry_run and not env_file.exists():
            print(f"[DRY RUN] Creerebbe il file: {env_file}")
        else:
            print(f"Il file esiste già: {env_file}")
    
    print("\nSincronizzazione completata!")

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    
    if dry_run:
        print("=== MODALITÀ DRY RUN - Nessuna modifica verrà apportata ===\n")
    
    sync_env(dry_run=dry_run, force=force)
    
    if dry_run:
        print("\n=== FINE DRY RUN - Nessuna modifica è stata apportata ===")
    else:
        print("\nPer applicare le modifiche, esegui nuovamente lo script senza --dry-run")

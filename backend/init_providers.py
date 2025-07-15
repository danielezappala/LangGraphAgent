"""Initialize the database with default LLM providers."""
import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database import SessionLocal, DBProvider

def init_providers() -> None:
    """Initialize the database with default providers."""
    db = SessionLocal()
    
    try:
        # Check if we already have any providers
        existing_providers = db.query(DBProvider).count()
        if existing_providers > 0:
            print("Providers already exist in the database. Skipping initialization.")
            return
        
        # Default providers to create
        default_providers: List[Dict[str, Any]] = [
            {
                "name": "OpenAI",
                "provider_type": "openai",
                "is_active": True,
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "model": "gpt-4o",
                "endpoint": None,
                "deployment": None,
                "api_version": None
            },
            {
                "name": "Azure OpenAI",
                "provider_type": "azure",
                "is_active": False,
                "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
                "model": "gpt-4o",
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
                "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
            }
        ]
        
        # Add default providers to the database
        for provider_data in default_providers:
            provider = DBProvider(**provider_data)
            db.add(provider)
        
        # Commit the transaction
        db.commit()
        print("Successfully initialized default providers.")
        
        # Print the list of providers
        providers = db.query(DBProvider).all()
        print("\nCurrent providers in the database:")
        for provider in providers:
            print(f"- {provider.name} ({'active' if provider.is_active else 'inactive'})")
            
    except Exception as e:
        print(f"Error initializing providers: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_providers()

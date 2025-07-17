"""Initialize the database with default LLM providers."""
from typing import List, Dict, Any
from database import SessionLocal, DBProvider

# Load environment variables using centralized loader
from core.env_loader import EnvironmentLoader
EnvironmentLoader.load_environment()

def init_providers() -> None:
    """Initialize the database with default providers."""
    db = SessionLocal()
    
    try:
        # Check if we already have any providers
        existing_providers = db.query(DBProvider).count()
        if existing_providers > 0:
            print("Providers already exist in the database. Skipping initialization.")
            return
        
        # Get configuration from centralized environment loader
        openai_config = EnvironmentLoader.get_openai_config()
        azure_config = EnvironmentLoader.get_azure_config()
        
        # Default providers to create
        default_providers: List[Dict[str, Any]] = [
            {
                "name": "OpenAI",
                "provider_type": "openai",
                "is_active": True,
                "api_key": openai_config['api_key'] or "",
                "model": openai_config['model'],
                "endpoint": None,
                "deployment": None,
                "api_version": None
            },
            {
                "name": "Azure OpenAI",
                "provider_type": "azure",
                "is_active": False,
                "api_key": azure_config['api_key'] or "",
                "model": azure_config['model'],
                "endpoint": azure_config['endpoint'] or "",
                "deployment": azure_config['deployment'] or "",
                "api_version": azure_config['api_version']
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

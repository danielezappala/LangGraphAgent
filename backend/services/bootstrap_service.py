"""Bootstrap service for one-time .env import to database."""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database import DBProvider
from config import get_llm_config


class BootstrapService:
    """Service for handling one-time bootstrap of .env configuration to database."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def is_first_startup(self) -> bool:
        """Check if this is the first startup (no providers in database)."""
        try:
            provider_count = self.db.query(DBProvider).count()
            return provider_count == 0
        except Exception as e:
            print(f"Error checking first startup: {e}")
            return True  # Assume first startup on error
    
    def import_env_to_database(self) -> bool:
        """Import .env configuration to database as the initial provider."""
        try:
            # Check if we have environment configuration
            env_config = self._get_env_config()
            if not env_config:
                print("No environment configuration found to import")
                return False
            
            # Check if this provider already exists
            existing = self.db.query(DBProvider).filter(
                DBProvider.name == env_config['name']
            ).first()
            
            if existing:
                print(f"Provider '{env_config['name']}' already exists in database")
                return True
            
            # Create new provider from environment
            new_provider = DBProvider(
                name=env_config['name'],
                provider_type=env_config['provider_type'],
                api_key=env_config['api_key'],
                model=env_config.get('model'),
                endpoint=env_config.get('endpoint'),
                deployment=env_config.get('deployment'),
                api_version=env_config.get('api_version'),
                is_active=True,
                is_from_env=True,  # Mark as imported from env
                is_valid=True,
                connection_status='untested'
            )
            
            # Deactivate any other providers (shouldn't be any, but just in case)
            self.db.query(DBProvider).update({DBProvider.is_active: False})
            
            # Add the new provider
            self.db.add(new_provider)
            self.db.commit()
            
            print(f"Successfully imported environment provider: {env_config['name']}")
            return True
            
        except Exception as e:
            print(f"Error importing environment to database: {e}")
            self.db.rollback()
            return False
    
    def _get_env_config(self) -> Optional[Dict[str, Any]]:
        """Extract provider configuration from environment variables."""
        try:
            llm_config = get_llm_config()
            
            if llm_config.provider == "openai" and llm_config.openai:
                return {
                    'name': 'Environment OpenAI',
                    'provider_type': 'openai',
                    'api_key': llm_config.openai.api_key,
                    'model': llm_config.openai.model
                }
            elif llm_config.provider == "azure" and llm_config.azure:
                return {
                    'name': 'Environment Azure OpenAI',
                    'provider_type': 'azure',
                    'api_key': llm_config.azure.api_key,
                    'model': llm_config.azure.model,
                    'endpoint': llm_config.azure.endpoint,
                    'deployment': llm_config.azure.deployment,
                    'api_version': llm_config.azure.api_version
                }
            
            return None
            
        except Exception as e:
            print(f"Error reading environment config: {e}")
            return None
    
    def mark_bootstrap_complete(self) -> None:
        """Mark bootstrap as completed (for future use if needed)."""
        # For now, we consider bootstrap complete when we have at least one provider
        # In the future, we could add a separate bootstrap_status table
        pass
    
    def run_bootstrap_if_needed(self) -> bool:
        """Run bootstrap process if this is the first startup."""
        if self.is_first_startup():
            print("First startup detected, importing environment configuration...")
            success = self.import_env_to_database()
            if success:
                self.mark_bootstrap_complete()
                print("Bootstrap completed successfully")
            else:
                print("Bootstrap failed or no environment configuration found")
            return success
        else:
            print("Bootstrap not needed, providers already exist in database")
            return True


def get_bootstrap_service(db: Session) -> BootstrapService:
    """Get a BootstrapService instance."""
    return BootstrapService(db)
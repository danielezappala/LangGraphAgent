"""Bootstrap service for one-time .env import to database."""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from database import DBProvider
from config import get_llm_config
from core.env_loader import EnvironmentLoader


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
        """Extract provider configuration from environment variables using centralized loader."""
        try:
            # Try the new centralized environment loader first
            provider = EnvironmentLoader.get_llm_provider()
            if provider:
                if provider.lower() == "openai":
                    openai_config = EnvironmentLoader.get_openai_config()
                    if openai_config['api_key']:
                        return {
                            'name': 'Environment OpenAI',
                            'provider_type': 'openai',
                            'api_key': openai_config['api_key'],
                            'model': openai_config['model']
                        }
                elif provider.lower() == "azure":
                    azure_config = EnvironmentLoader.get_azure_config()
                    if azure_config['api_key'] and azure_config['endpoint']:
                        return {
                            'name': 'Environment Azure OpenAI',
                            'provider_type': 'azure',
                            'api_key': azure_config['api_key'],
                            'model': azure_config['model'],
                            'endpoint': azure_config['endpoint'],
                            'deployment': azure_config['deployment'],
                            'api_version': azure_config['api_version']
                        }
            
            # Fallback to legacy config system if centralized loader doesn't have provider
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
            except Exception as legacy_e:
                print(f"Legacy config system also failed: {legacy_e}")
            
            return None
            
        except Exception as e:
            print(f"Error reading environment config: {e}")
            return None
    
    def mark_bootstrap_complete(self) -> None:
        """Mark bootstrap as completed (for future use if needed)."""
        # For now, we consider bootstrap complete when we have at least one provider
        # In the future, we could add a separate bootstrap_status table
        pass
    
    def create_default_providers(self) -> bool:
        """Create default providers from environment configuration."""
        try:
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
                    "api_version": None,
                    "is_from_env": True,
                    "is_valid": bool(openai_config['api_key']),
                    "connection_status": 'untested'
                },
                {
                    "name": "Azure OpenAI",
                    "provider_type": "azure",
                    "is_active": False,
                    "api_key": azure_config['api_key'] or "",
                    "model": azure_config['model'],
                    "endpoint": azure_config['endpoint'] or "",
                    "deployment": azure_config['deployment'] or "",
                    "api_version": azure_config['api_version'],
                    "is_from_env": True,
                    "is_valid": bool(azure_config['api_key'] and azure_config['endpoint']),
                    "connection_status": 'untested'
                }
            ]
            
            # Add default providers to the database
            for provider_data in default_providers:
                # Check if provider already exists
                existing = self.db.query(DBProvider).filter(
                    DBProvider.name == provider_data['name']
                ).first()
                
                if not existing:
                    provider = DBProvider(**provider_data)
                    self.db.add(provider)
                    print(f"Created default provider: {provider_data['name']}")
                else:
                    print(f"Default provider already exists: {provider_data['name']}")
            
            # Commit the transaction
            self.db.commit()
            print("Successfully initialized default providers.")
            
            return True
            
        except Exception as e:
            print(f"Error creating default providers: {e}")
            self.db.rollback()
            return False
    
    def run_bootstrap_if_needed(self) -> bool:
        """Run bootstrap process if this is the first startup."""
        if self.is_first_startup():
            print("First startup detected, running bootstrap process...")
            
            # Try to import environment configuration first
            env_success = self.import_env_to_database()
            
            # If no environment config, create default providers
            if not env_success:
                print("No environment configuration found, creating default providers...")
                default_success = self.create_default_providers()
                if default_success:
                    self.mark_bootstrap_complete()
                    print("Bootstrap completed with default providers")
                    return True
                else:
                    print("Bootstrap failed - could not create default providers")
                    return False
            else:
                self.mark_bootstrap_complete()
                print("Bootstrap completed with environment configuration")
                return True
        else:
            print("Bootstrap not needed, providers already exist in database")
            return True


def get_bootstrap_service(db: Session) -> BootstrapService:
    """Get a BootstrapService instance."""
    return BootstrapService(db)
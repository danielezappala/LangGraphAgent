"""Provider service for managing LLM provider CRUD operations."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import DBProvider
from .config_service import ConfigService, ValidationResult
import requests
import json
import time


class TestResult(BaseModel):
    """Result of provider connection test."""
    success: bool
    message: str
    response_time_ms: Optional[int] = None
    error_details: Optional[str] = None


class ProviderService:
    """Service for managing LLM provider CRUD operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)
    
    def list_all_providers(self) -> List[Dict[str, Any]]:
        """List all providers from database (Database-First approach)."""
        try:
            # Get all database providers
            db_providers = self.db.query(DBProvider).all()
            providers = []
            
            for provider in db_providers:
                providers.append({
                    'id': provider.id,
                    'name': provider.name,
                    'provider_type': provider.provider_type,
                    'api_key': provider.api_key,
                    'model': provider.model,
                    'endpoint': provider.endpoint,
                    'deployment': provider.deployment,
                    'api_version': provider.api_version,
                    'is_active': provider.is_active,
                    'is_from_env': provider.is_from_env,
                    'is_valid': provider.is_valid,
                    'connection_status': provider.connection_status,
                    'last_tested': provider.last_tested.isoformat() if provider.last_tested else None,
                    'created_at': provider.created_at.isoformat() if provider.created_at else None,
                    'updated_at': provider.updated_at.isoformat() if provider.updated_at else None
                })
            
            return providers
            
        except Exception as e:
            print(f"Error listing providers: {e}")
            return []
    
    def get_active_provider(self) -> Optional[Dict[str, Any]]:
        """Get the currently active provider."""
        try:
            return self.config_service.get_active_provider()
            
        except Exception as e:
            print(f"Error getting active provider: {e}")
            return None
    
    def create_provider(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new provider configuration."""
        try:
            # Validate configuration
            validation = self.config_service.validate_provider_config(config)
            if not validation.is_valid:
                raise ValueError(f"Invalid configuration: {', '.join(validation.errors)}")
            
            # If this provider should be active, deactivate others
            if config.get('is_active', False):
                self.db.query(DBProvider).update({DBProvider.is_active: False})
            
            # Create new provider
            new_provider = DBProvider(
                name=config['name'],
                provider_type=config['provider_type'],
                api_key=config['api_key'],
                model=config.get('model'),
                endpoint=config.get('endpoint'),
                deployment=config.get('deployment'),
                api_version=config.get('api_version'),
                is_active=config.get('is_active', False)
            )
            
            self.db.add(new_provider)
            self.db.commit()
            self.db.refresh(new_provider)
            
            # No need to sync to env - Database-First approach
            
            return {
                'id': new_provider.id,
                'name': new_provider.name,
                'provider_type': new_provider.provider_type,
                'api_key': new_provider.api_key,
                'model': new_provider.model,
                'endpoint': new_provider.endpoint,
                'deployment': new_provider.deployment,
                'api_version': new_provider.api_version,
                'is_active': new_provider.is_active,
                'is_from_env': False
            }
            
        except IntegrityError as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError("A provider with this name already exists")
            raise ValueError(f"Database error: {str(e)}")
        except Exception as e:
            self.db.rollback()
            print(f"Error creating provider: {e}")
            raise ValueError(f"Failed to create provider: {str(e)}")
    
    def update_provider(self, provider_id: int, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing provider configuration."""
        try:
            provider = self.db.query(DBProvider).filter(DBProvider.id == provider_id).first()
            if not provider:
                raise ValueError("Provider not found")
            
            # Validate configuration
            validation = self.config_service.validate_provider_config(config)
            if not validation.is_valid:
                raise ValueError(f"Invalid configuration: {', '.join(validation.errors)}")
            
            # If this provider should be active, deactivate others
            if config.get('is_active', False) and not provider.is_active:
                self.db.query(DBProvider).update({DBProvider.is_active: False})
            
            # Update provider fields
            provider.name = config['name']
            provider.provider_type = config['provider_type']
            provider.api_key = config['api_key']
            provider.model = config.get('model')
            provider.endpoint = config.get('endpoint')
            provider.deployment = config.get('deployment')
            provider.api_version = config.get('api_version')
            provider.is_active = config.get('is_active', False)
            
            self.db.commit()
            self.db.refresh(provider)
            
            # No need to sync to env - Database-First approach
            
            return {
                'id': provider.id,
                'name': provider.name,
                'provider_type': provider.provider_type,
                'api_key': provider.api_key,
                'model': provider.model,
                'endpoint': provider.endpoint,
                'deployment': provider.deployment,
                'api_version': provider.api_version,
                'is_active': provider.is_active,
                'is_from_env': False
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"Error updating provider: {e}")
            raise ValueError(f"Failed to update provider: {str(e)}")
    
    def delete_provider(self, provider_id: int) -> bool:
        """Delete a provider configuration."""
        try:
            provider = self.db.query(DBProvider).filter(DBProvider.id == provider_id).first()
            if not provider:
                raise ValueError("Provider not found")
            
            # Check if this is the active provider
            if provider.is_active:
                raise ValueError("Cannot delete the active provider. Please activate another provider first.")
            
            self.db.delete(provider)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting provider: {e}")
            raise ValueError(f"Failed to delete provider: {str(e)}")
    
    def set_active_provider(self, provider_id: int) -> Optional[Dict[str, Any]]:
        """Set a provider as the active one."""
        try:
            provider = self.db.query(DBProvider).filter(DBProvider.id == provider_id).first()
            if not provider:
                raise ValueError("Provider not found")
            
            # Validate provider configuration before activating
            provider_config = {
                'name': provider.name,
                'provider_type': provider.provider_type,
                'api_key': provider.api_key,
                'model': provider.model,
                'endpoint': provider.endpoint,
                'deployment': provider.deployment,
                'api_version': provider.api_version
            }
            
            validation = self.config_service.validate_provider_config(provider_config)
            if not validation.is_valid:
                raise ValueError(f"Cannot activate invalid provider: {', '.join(validation.errors)}")
            
            # Deactivate all providers
            self.db.query(DBProvider).update({DBProvider.is_active: False})
            
            # Activate the selected provider
            provider.is_active = True
            self.db.commit()
            self.db.refresh(provider)
            
            # No need to sync to env - Database-First approach
            
            return {
                'id': provider.id,
                'name': provider.name,
                'provider_type': provider.provider_type,
                'api_key': provider.api_key,
                'model': provider.model,
                'endpoint': provider.endpoint,
                'deployment': provider.deployment,
                'api_version': provider.api_version,
                'is_active': provider.is_active,
                'is_from_env': False
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"Error setting active provider: {e}")
            raise ValueError(f"Failed to set active provider: {str(e)}")
    
    def test_provider_connection(self, config: Dict[str, Any]) -> TestResult:
        """Test connection to a provider."""
        print(f"=== PROVIDER SERVICE TEST CONNECTION ===")
        print(f"Config: {config}")
        
        try:
            import time
            start_time = time.time()
            
            if config['provider_type'] == 'openai':
                print("Testing OpenAI connection...")
                return self._test_openai_connection(config, start_time)
            elif config['provider_type'] == 'azure':
                print("Testing Azure connection...")
                return self._test_azure_connection(config, start_time)
            else:
                print(f"Unsupported provider type: {config['provider_type']}")
                return TestResult(
                    success=False,
                    message="Unsupported provider type",
                    error_details=f"Provider type '{config['provider_type']}' is not supported"
                )
                
        except Exception as e:
            print(f"Exception in test_provider_connection: {e}")
            return TestResult(
                success=False,
                message="Connection test failed",
                error_details=str(e)
            )
    
    def _test_openai_connection(self, config: Dict[str, Any], start_time: float) -> TestResult:
        """Test OpenAI API connection."""
        try:
            headers = {
                'Authorization': f'Bearer {config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            # Simple API call to test connection
            response = requests.get(
                'https://api.openai.com/v1/models',
                headers=headers,
                timeout=10
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                return TestResult(
                    success=True,
                    message="Connection successful",
                    response_time_ms=response_time
                )
            else:
                return TestResult(
                    success=False,
                    message=f"API returned status {response.status_code}",
                    response_time_ms=response_time,
                    error_details=response.text
                )
                
        except requests.exceptions.Timeout:
            return TestResult(
                success=False,
                message="Connection timeout",
                error_details="Request timed out after 10 seconds"
            )
        except requests.exceptions.RequestException as e:
            return TestResult(
                success=False,
                message="Connection failed",
                error_details=str(e)
            )
    
    def _test_azure_connection(self, config: Dict[str, Any], start_time: float) -> TestResult:
        """Test Azure OpenAI API connection."""
        try:
            headers = {
                'api-key': config['api_key'],
                'Content-Type': 'application/json'
            }
            
            # Build Azure API URL for a simple test
            endpoint = config['endpoint'].rstrip('/')
            api_version = config.get('api_version', '2023-05-15')
            deployment = config.get('deployment')
            
            if not deployment:
                return TestResult(
                    success=False,
                    message="Deployment name is required for Azure OpenAI",
                    error_details="No deployment name configured"
                )
            
            # Use a simple completions endpoint test with minimal payload
            url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
            
            # Simple test payload
            test_payload = {
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
                "temperature": 0
            }
            
            print(f"Testing Azure connection to: {url}")
            print(f"Using deployment: {deployment}")
            print(f"API version: {api_version}")
            print(f"Headers: {headers}")
            print(f"Payload: {test_payload}")
            
            response = requests.post(url, headers=headers, json=test_payload, timeout=15)
            response_time = int((time.time() - start_time) * 1000)
            
            # Azure returns 200 for successful API calls
            if response.status_code == 200:
                return TestResult(
                    success=True,
                    message="Connection successful",
                    response_time_ms=response_time
                )
            # Handle authentication errors specifically
            elif response.status_code == 401:
                return TestResult(
                    success=False,
                    message="Authentication failed - check API key",
                    response_time_ms=response_time,
                    error_details="Invalid API key or insufficient permissions"
                )
            # Handle other client errors
            elif response.status_code == 404:
                return TestResult(
                    success=False,
                    message="Deployment not found - check deployment name",
                    response_time_ms=response_time,
                    error_details=f"Deployment '{deployment}' not found"
                )
            else:
                return TestResult(
                    success=False,
                    message=f"API returned status {response.status_code}",
                    response_time_ms=response_time,
                    error_details=response.text[:200] if response.text else "No error details"
                )
                
        except requests.exceptions.Timeout:
            return TestResult(
                success=False,
                message="Connection timeout",
                error_details="Request timed out after 15 seconds"
            )
        except requests.exceptions.RequestException as e:
            return TestResult(
                success=False,
                message="Connection failed",
                error_details=str(e)
            )


def get_provider_service(db: Session) -> ProviderService:
    """Get a ProviderService instance."""
    return ProviderService(db)
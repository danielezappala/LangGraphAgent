"""Configuration service for managing LLM provider configurations."""
import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session
from database import DBProvider, get_db
from config import get_llm_config, LLMConfig


class ValidationResult(BaseModel):
    """Result of provider configuration validation."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class ProviderStatus(BaseModel):
    """Overall provider configuration status."""
    has_active_provider: bool
    active_provider_name: Optional[str] = None
    total_providers: int = 0
    configuration_source: str  # 'env', 'database', 'mixed'
    issues: List[str] = []


class ConfigService:
    """Service for managing provider configurations (Database-First approach)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_provider(self) -> Optional[Dict[str, Any]]:
        """Get the active provider configuration from database only."""
        try:
            db_provider = self._get_active_db_provider()
            
            if db_provider:
                return {
                    'id': db_provider.id,
                    'name': db_provider.name,
                    'provider_type': db_provider.provider_type,
                    'api_key': db_provider.api_key,
                    'model': db_provider.model,
                    'endpoint': db_provider.endpoint,
                    'deployment': db_provider.deployment,
                    'api_version': db_provider.api_version,
                    'is_active': db_provider.is_active,
                    'is_from_env': db_provider.is_from_env,
                    'is_valid': db_provider.is_valid,
                    'connection_status': db_provider.connection_status,
                    'last_tested': db_provider.last_tested.isoformat() if db_provider.last_tested else None,
                    'source': 'database'
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting active provider: {e}")
            return None
    
    def _get_active_db_provider(self) -> Optional[DBProvider]:
        """Get the active provider from database."""
        try:
            return self.db.query(DBProvider).filter(DBProvider.is_active == True).first()
        except Exception as e:
            print(f"Error getting active DB provider: {e}")
            return None
    
    def validate_provider_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate a provider configuration."""
        errors = []
        warnings = []
        
        # Required fields validation
        if not config.get('name'):
            errors.append("Provider name is required")
        
        if not config.get('provider_type'):
            errors.append("Provider type is required")
        elif config['provider_type'] not in ['openai', 'azure']:
            errors.append("Provider type must be 'openai' or 'azure'")
        
        if not config.get('api_key'):
            errors.append("API key is required")
        elif len(config['api_key']) < 10:
            warnings.append("API key seems too short")
        
        # Provider-specific validation
        if config.get('provider_type') == 'azure':
            if not config.get('endpoint'):
                errors.append("Endpoint is required for Azure OpenAI")
            elif not config['endpoint'].startswith('https://'):
                errors.append("Azure endpoint must start with https://")
            
            if not config.get('deployment'):
                errors.append("Deployment name is required for Azure OpenAI")
            
            if not config.get('api_version'):
                warnings.append("API version not specified, using default")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get_provider_status(self) -> ProviderStatus:
        """Get overall provider configuration status."""
        try:
            active_provider = self.get_active_provider()
            total_providers = self.db.query(DBProvider).count()
            issues = []
            
            has_active = active_provider is not None
            active_name = active_provider.get('name') if active_provider else None
            
            # Check for common issues
            if not has_active:
                issues.append("No active provider configured")
            
            if total_providers == 0:
                issues.append("No providers configured in database")
            
            return ProviderStatus(
                has_active_provider=has_active,
                active_provider_name=active_name,
                total_providers=total_providers,
                configuration_source='database',  # Always database in Database-First approach
                issues=issues
            )
            
        except Exception as e:
            return ProviderStatus(
                has_active_provider=False,
                total_providers=0,
                configuration_source='error',
                issues=[f"Error checking provider status: {str(e)}"]
            )


def get_config_service(db: Session = None) -> ConfigService:
    """Get a ConfigService instance."""
    if db is None:
        db = next(get_db())
    return ConfigService(db)
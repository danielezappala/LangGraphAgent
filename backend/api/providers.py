"""API endpoints for managing LLM providers."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Literal, Optional
import os
from datetime import datetime
from sqlalchemy.orm import Session

from database import DBProvider, get_db
from services.config_service import get_config_service
from services.provider_service import get_provider_service

router = APIRouter()

class ProviderConfigBase(BaseModel):
    """Base LLM provider configuration."""
    name: str
    provider_type: Literal["openai", "azure"]
    api_key: str
    model: Optional[str] = None
    endpoint: Optional[str] = None
    deployment: Optional[str] = None
    api_version: Optional[str] = None

class ProviderConfigCreate(ProviderConfigBase):
    """Schema for creating a new provider configuration."""
    is_active: bool = False

class ProviderConfigResponse(ProviderConfigBase):
    """Response model for provider configuration."""
    id: int
    is_active: bool

    class Config:
        orm_mode = True

def get_active_provider_config(db: Session) -> Optional[DBProvider]:
    """Get the currently active provider configuration."""
    return db.query(DBProvider).filter(DBProvider.is_active == True).first()

@router.get("/active")
async def get_active_provider(db: Session = Depends(get_db)):
    """Get the currently active LLM provider."""
    try:
        provider_service = get_provider_service(db)
        active_provider = provider_service.get_active_provider()
        
        if not active_provider:
            raise HTTPException(status_code=404, detail="No active provider found")
        
        return active_provider
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/list")
async def list_providers(db: Session = Depends(get_db)):
    """List all available provider configurations."""
    try:
        provider_service = get_provider_service(db)
        providers = provider_service.list_all_providers()
        
        return providers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/add")
async def add_provider(
    config: ProviderConfigCreate,
    db: Session = Depends(get_db)
):
    """Add a new provider configuration."""
    try:
        provider_service = get_provider_service(db)
        
        # Convert Pydantic model to dict
        config_dict = {
            'name': config.name,
            'provider_type': config.provider_type,
            'api_key': config.api_key,
            'model': config.model,
            'endpoint': config.endpoint,
            'deployment': config.deployment,
            'api_version': config.api_version,
            'is_active': config.is_active
        }
        
        result = provider_service.create_provider(config_dict)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/switch/{provider_id}")
async def switch_provider(
    provider_id: int,
    config: ProviderConfigCreate,
    db: Session = Depends(get_db)
):
    """Switch to and update a provider configuration."""
    try:
        provider_service = get_provider_service(db)
        
        # Convert Pydantic model to dict
        config_dict = {
            'name': config.name,
            'provider_type': config.provider_type,
            'api_key': config.api_key,
            'model': config.model,
            'endpoint': config.endpoint,
            'deployment': config.deployment,
            'api_version': config.api_version,
            'is_active': config.is_active
        }
        
        result = provider_service.update_provider(provider_id, config_dict)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{provider_id}")
async def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    """Delete a provider configuration."""
    try:
        provider_service = get_provider_service(db)
        success = provider_service.delete_provider(provider_id)
        
        if success:
            return {"message": "Provider deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete provider")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{provider_id}/activate", response_model=ProviderConfigResponse)
async def activate_provider(provider_id: int, db: Session = Depends(get_db)):
    """Set a provider as the active one."""
    try:
        provider_service = get_provider_service(db)
        result = provider_service.set_active_provider(provider_id)
        
        if result:
            return result
        else:
            raise HTTPException(status_code=400, detail="Failed to activate provider")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{provider_id}/test")
async def test_provider_connection(provider_id: int, db: Session = Depends(get_db)):
    """Test connection to a provider."""
    print(f"=== TESTING PROVIDER CONNECTION ===")
    print(f"Provider ID: {provider_id}")
    
    try:
        # Get provider from database
        provider = db.query(DBProvider).filter(DBProvider.id == provider_id).first()
        if not provider:
            print(f"Provider with ID {provider_id} not found")
            raise HTTPException(status_code=404, detail="Provider not found")
        
        print(f"Found provider: {provider.name} ({provider.provider_type})")
        
        # Convert to config dict for testing
        config = {
            'name': provider.name,
            'provider_type': provider.provider_type,
            'api_key': provider.api_key,
            'model': provider.model,
            'endpoint': provider.endpoint,
            'deployment': provider.deployment,
            'api_version': provider.api_version
        }
        
        provider_service = get_provider_service(db)
        result = provider_service.test_provider_connection(config)
        
        # Update provider's connection status and last tested time
        provider.connection_status = 'connected' if result.success else 'failed'
        provider.last_tested = datetime.utcnow()
        db.commit()
        
        return {
            "success": result.success,
            "message": result.message,
            "response_time_ms": result.response_time_ms,
            "error_details": result.error_details
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/status")
async def get_provider_status(db: Session = Depends(get_db)):
    """Get overall provider configuration status."""
    try:
        config_service = get_config_service(db)
        status = config_service.get_provider_status()
        
        return {
            "has_active_provider": status.has_active_provider,
            "active_provider_name": status.active_provider_name,
            "total_providers": status.total_providers,
            "configuration_source": status.configuration_source,
            "issues": status.issues
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/sync")
async def sync_providers(db: Session = Depends(get_db)):
    """Force sync between .env and database configurations."""
    try:
        config_service = get_config_service(db)
        success = config_service.sync_env_to_database()
        
        if success:
            return {"message": "Providers synchronized successfully"}
        else:
            return {"message": "No environment configuration found to sync"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def update_environment_vars(provider: DBProvider):
    """Update environment variables based on provider configuration."""
    os.environ["LLM_PROVIDER"] = provider.provider_type
    
    if provider.provider_type == "openai":
        os.environ["OPENAI_API_KEY"] = provider.api_key
        if provider.model:
            os.environ["OPENAI_MODEL"] = provider.model
    elif provider.provider_type == "azure":
        os.environ["AZURE_OPENAI_API_KEY"] = provider.api_key
        if provider.endpoint:
            os.environ["AZURE_OPENAI_ENDPOINT"] = provider.endpoint
        if provider.deployment:
            os.environ["AZURE_OPENAI_DEPLOYMENT"] = provider.deployment
        if provider.model:
            os.environ["AZURE_OPENAI_MODEL"] = provider.model
        if provider.api_version:
            os.environ["AZURE_OPENAI_API_VERSION"] = provider.api_version

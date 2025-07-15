"""API endpoints for managing LLM providers."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Literal, Optional
import os
from sqlalchemy.orm import Session

from database import DBProvider, get_db

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

@router.get("/active", response_model=ProviderConfigResponse)
async def get_active_provider(db: Session = Depends(get_db)):
    """Get the currently active LLM provider."""
    provider = get_active_provider_config(db)
    if not provider:
        raise HTTPException(status_code=404, detail="No active provider found")
    return provider

@router.get("/list", response_model=List[ProviderConfigResponse])
async def list_providers(db: Session = Depends(get_db)):
    """List all available provider configurations."""
    return db.query(DBProvider).all()

@router.post("/add", response_model=ProviderConfigResponse)
async def add_provider(
    config: ProviderConfigCreate,
    db: Session = Depends(get_db)
):
    """Add a new provider configuration."""
    # If this is set to be active, deactivate all others
    if config.is_active:
        db.query(DBProvider).update({DBProvider.is_active: False})
    
    # Create the new provider
    db_provider = DBProvider(
        name=config.name,
        provider_type=config.provider_type,
        api_key=config.api_key,
        model=config.model,
        endpoint=config.endpoint,
        deployment=config.deployment,
        api_version=config.api_version,
        is_active=config.is_active
    )
    
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    
    return db_provider

@router.post("/switch/{provider_id}", response_model=ProviderConfigResponse)
async def switch_provider(
    provider_id: int,
    config: ProviderConfigCreate,
    db: Session = Depends(get_db)
):
    """Switch to and update a provider configuration."""
    # Find the provider to update
    provider = db.query(DBProvider).filter(DBProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # If this provider is being activated, deactivate all others
    if config.is_active:
        db.query(DBProvider).update({DBProvider.is_active: False})
    
    # Update provider details
    provider.name = config.name
    provider.provider_type = config.provider_type
    provider.api_key = config.api_key
    provider.model = config.model
    provider.endpoint = config.endpoint
    provider.deployment = config.deployment
    provider.api_version = config.api_version
    provider.is_active = config.is_active
    
    db.commit()
    db.refresh(provider)
    
    # Update environment variables if this is the active provider
    if provider.is_active:
        update_environment_vars(provider)
    
    return provider

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

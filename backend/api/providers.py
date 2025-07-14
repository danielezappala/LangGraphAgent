"""API endpoints for managing LLM providers."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
import os

router = APIRouter()

class ProviderConfig(BaseModel):
    """LLM provider configuration."""
    provider: Literal["openai", "azure"]
    api_key: Optional[str] = None
    model: Optional[str] = None
    # Azure specific
    endpoint: Optional[str] = None
    deployment: Optional[str] = None
    api_version: Optional[str] = None

@router.get("/active")
async def get_active_provider() -> dict:
    """Get the currently active LLM provider."""
    provider = os.getenv("LLM_PROVIDER", "openai")
    return {"provider": provider}

@router.post("/switch")
async def switch_provider(config: ProviderConfig) -> dict:
    """Switch the active LLM provider."""
    # Update environment variables
    os.environ["LLM_PROVIDER"] = config.provider
    
    if config.api_key:
        if config.provider == "openai":
            os.environ["OPENAI_API_KEY"] = config.api_key
            if config.model:
                os.environ["OPENAI_MODEL"] = config.model
        elif config.provider == "azure":
            os.environ["AZURE_OPENAI_API_KEY"] = config.api_key
            if config.endpoint:
                os.environ["AZURE_OPENAI_ENDPOINT"] = config.endpoint
            if config.deployment:
                os.environ["AZURE_OPENAI_DEPLOYMENT"] = config.deployment
            if config.model:
                os.environ["AZURE_OPENAI_MODEL"] = config.model
            if config.api_version:
                os.environ["AZURE_OPENAI_API_VERSION"] = config.api_version
    
    return {"status": "success", "provider": config.provider}

"""API endpoints for managing LLM provider configuration."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
from pathlib import Path

# Load environment variables using centralized loader
from core.env_loader import EnvironmentLoader
EnvironmentLoader.load_environment()

router = APIRouter()

class ProviderConfig(BaseModel):
    provider: Literal["openai", "azure"]
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = "gpt-4"
    openai_temperature: Optional[float] = 0.7
    azure_api_key: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_deployment: Optional[str] = None
    azure_api_version: Optional[str] = "2023-05-15"

@router.get("/config")
async def get_config() -> ProviderConfig:
    """Get current LLM provider configuration."""
    provider = EnvironmentLoader.get_llm_provider() or "openai"
    config = {"provider": provider}
    
    if provider == "openai":
        openai_config = EnvironmentLoader.get_openai_config()
        config.update({
            "openai_api_key": openai_config['api_key'],
            "openai_model": openai_config['model'],
            "openai_temperature": openai_config['temperature'],
        })
    else:  # azure
        azure_config = EnvironmentLoader.get_azure_config()
        config.update({
            "azure_api_key": azure_config['api_key'],
            "azure_endpoint": azure_config['endpoint'],
            "azure_deployment": azure_config['deployment'],
            "azure_api_version": azure_config['api_version'],
        })
    
    return ProviderConfig(**config)

@router.post("/config")
async def update_config(config: ProviderConfig):
    """Update LLM provider configuration."""
    env_file = Path(".env")
    env_lines = []
    
    if env_file.exists():
        with open(env_file, "r") as f:
            env_lines = f.readlines()
    
    # Remove existing config
    env_lines = [
        line for line in env_lines 
        if not any(line.startswith(prefix) 
                  for prefix in [
                      "LLM_PROVIDER=", 
                      "OPENAI_", 
                      "AZURE_OPENAI_"
                  ])
    ]
    
    # Add new config
    env_lines.append(f"LLM_PROVIDER={config.provider}\n")
    
    if config.provider == "openai":
        if not config.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
            
        env_lines.extend([
            f"OPENAI_API_KEY={config.openai_api_key}\n",
            f"OPENAI_MODEL={config.openai_model or 'gpt-4'}\n",
            f"OPENAI_TEMPERATURE={config.openai_temperature or 0.7}\n",
        ])
    else:  # azure
        if not all([config.azure_api_key, config.azure_endpoint, config.azure_deployment]):
            raise HTTPException(
                status_code=400, 
                detail="Azure API key, endpoint, and deployment are required"
            )
            
        env_lines.extend([
            f"AZURE_OPENAI_API_KEY={config.azure_api_key}\n",
            f"AZURE_OPENAI_ENDPOINT={config.azure_endpoint}\n",
            f"AZURE_OPENAI_DEPLOYMENT={config.azure_deployment}\n",
            f"AZURE_OPENAI_API_VERSION={config.azure_api_version or '2023-05-15'}\n",
        ])
    
    # Write back to .env
    with open(env_file, "w") as f:
        f.writelines(env_lines)
    
    return {"status": "success", "message": "Configuration updated successfully"}

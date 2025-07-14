"""Configuration module for LangGraphAgent.

This module handles the configuration for different LLM providers.
"""
import os
from typing import Literal, Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAIConfig(BaseSettings):
    """Configuration for OpenAI API."""
    api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    model: str = Field("gpt-4", validation_alias="OPENAI_MODEL")
    temperature: float = Field(0.0, validation_alias="OPENAI_TEMPERATURE")
    max_tokens: int = Field(1000, validation_alias="OPENAI_MAX_TOKENS")
    timeout: int = Field(30, validation_alias="OPENAI_TIMEOUT")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class AzureOpenAIConfig(BaseSettings):
    """Configuration for Azure OpenAI API."""
    api_key: str = Field(..., validation_alias="AZURE_OPENAI_API_KEY")
    endpoint: str = Field(..., validation_alias="AZURE_OPENAI_ENDPOINT")
    api_version: str = Field("2023-05-15", validation_alias="AZURE_OPENAI_API_VERSION")
    deployment: str = Field(..., validation_alias="AZURE_OPENAI_DEPLOYMENT")
    model: str = Field("gpt-4", validation_alias="AZURE_OPENAI_MODEL")  # Base model name (not deployment name)
    temperature: float = Field(0.0, validation_alias="AZURE_OPENAI_TEMPERATURE")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class LLMConfig(BaseSettings):
    """LLM configuration with provider selection."""
    provider: Literal["openai", "azure"] = Field(
        default=...,
        validation_alias="LLM_PROVIDER"
    )
    
    # Configurations will be loaded based on the provider
    openai: Optional[OpenAIConfig] = None
    azure: Optional[AzureOpenAIConfig] = None
    
    # External API keys
    tavily_api_key: Optional[str] = Field(None, validation_alias="TAVILY_API_KEY")
    notion_api_key: Optional[str] = Field(None, validation_alias="NOTION_API_KEY")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize the appropriate config based on provider
        if self.provider == "openai" and self.openai is None:
            self.openai = OpenAIConfig()
        elif self.provider == "azure" and self.azure is None:
            self.azure = AzureOpenAIConfig()


def get_llm_config() -> LLMConfig:
    """Get LLM configuration with automatic provider selection."""
    try:
        config = LLMConfig()
        print(f"\n=== Loaded Configuration ===")
        print(f"Provider: {config.provider}")
        if config.provider == "openai" and config.openai:
            print(f"OpenAI Model: {config.openai.model}")
        elif config.provider == "azure" and config.azure:
            print(f"Azure Endpoint: {config.azure.endpoint}")
            print(f"Azure Deployment: {config.azure.deployment}")
        print("==========================")
        return config
    except Exception as e:
        print(f"\n❌ Error loading LLM config: {e}")
        print("Please check your .env file configuration.")
        raise

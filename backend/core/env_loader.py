"""Centralized environment variable loading with consistent override logic."""
import os
import pathlib
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class EnvironmentLoader:
    """Centralized environment variable loading with consistent override logic."""
    
    _loaded = False
    
    @classmethod
    def load_environment(cls) -> None:
        """Load environment variables with proper precedence.
        
        Loading order (later overrides earlier):
        1. Root .env file (shared between frontend and backend)
        2. Backend-specific .env file (if exists)
        
        This method is idempotent - calling it multiple times is safe.
        """
        if cls._loaded:
            return
            
        try:
            # Get the backend directory path
            backend_dir = pathlib.Path(__file__).parent.parent
            root_dir = backend_dir.parent
            
            # Load root .env file first (shared configuration)
            root_env_path = root_dir / '.env'
            if root_env_path.exists():
                load_dotenv(root_env_path)
                print(f"Loaded shared environment from: {root_env_path}")
            
            # Load backend-specific .env file (overrides shared settings)
            backend_env_path = backend_dir / '.env'
            if backend_env_path.exists():
                load_dotenv(backend_env_path, override=True)
                print(f"Loaded backend environment from: {backend_env_path}")
            
            cls._loaded = True
            print("Environment variables loaded successfully")
            
        except Exception as e:
            print(f"Error loading environment variables: {e}")
            raise
    
    @staticmethod
    def get_database_url() -> str:
        """Get database URL with fallback logic."""
        return os.getenv("DATABASE_URL", "sqlite:///./langgraph_agent.db")
    
    @staticmethod
    def get_api_config() -> Dict[str, Any]:
        """Get API configuration settings."""
        return {
            'host': os.getenv("BACKEND_HOST", "0.0.0.0"),
            'port': int(os.getenv("BACKEND_PORT", "8000")),
            'frontend_port': int(os.getenv("FRONTEND_PORT", "9002")),
            'cors_origins': os.getenv("CORS_ORIGINS", "*").split(","),
            'debug': os.getenv("DEBUG", "false").lower() == "true"
        }
    
    @staticmethod
    def get_llm_provider() -> Optional[str]:
        """Get the configured LLM provider."""
        return os.getenv("LLM_PROVIDER")
    
    @staticmethod
    def get_openai_config() -> Dict[str, Any]:
        """Get OpenAI configuration from environment."""
        return {
            'api_key': os.getenv("OPENAI_API_KEY"),
            'model': os.getenv("OPENAI_MODEL", "gpt-4"),
            'temperature': float(os.getenv("OPENAI_TEMPERATURE", "0.0")),
            'max_tokens': int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
            'timeout': int(os.getenv("OPENAI_TIMEOUT", "30"))
        }
    
    @staticmethod
    def get_azure_config() -> Dict[str, Any]:
        """Get Azure OpenAI configuration from environment."""
        return {
            'api_key': os.getenv("AZURE_OPENAI_API_KEY"),
            'endpoint': os.getenv("AZURE_OPENAI_ENDPOINT"),
            'api_version': os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
            'deployment': os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            'model': os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
            'temperature': float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.0"))
        }
    
    @staticmethod
    def get_external_api_keys() -> Dict[str, Optional[str]]:
        """Get external API keys (Tavily, Notion, etc.)."""
        return {
            'tavily': os.getenv("TAVILY_API_KEY"),
            'notion': os.getenv("NOTION_API_KEY")
        }
    
    @staticmethod
    def is_development() -> bool:
        """Check if running in development mode."""
        return os.getenv("NODE_ENV", "development") == "development"
    
    @staticmethod
    def print_config_summary() -> None:
        """Print a summary of loaded configuration (for debugging)."""
        print("\n=== Environment Configuration Summary ===")
        print(f"LLM Provider: {EnvironmentLoader.get_llm_provider() or 'Not set'}")
        print(f"Database URL: {EnvironmentLoader.get_database_url()}")
        
        api_config = EnvironmentLoader.get_api_config()
        print(f"API Host: {api_config['host']}:{api_config['port']}")
        print(f"Frontend Port: {api_config['frontend_port']}")
        print(f"Development Mode: {EnvironmentLoader.is_development()}")
        
        # Show which provider configs are available (without exposing keys)
        openai_config = EnvironmentLoader.get_openai_config()
        azure_config = EnvironmentLoader.get_azure_config()
        
        if openai_config['api_key']:
            print(f"OpenAI: Configured (model: {openai_config['model']})")
        else:
            print("OpenAI: Not configured")
            
        if azure_config['api_key'] and azure_config['endpoint']:
            print(f"Azure OpenAI: Configured (deployment: {azure_config['deployment']})")
        else:
            print("Azure OpenAI: Not configured")
        
        external_keys = EnvironmentLoader.get_external_api_keys()
        external_configured = [k for k, v in external_keys.items() if v]
        if external_configured:
            print(f"External APIs: {', '.join(external_configured)}")
        else:
            print("External APIs: None configured")
        
        print("==========================================\n")


# Convenience function for backward compatibility
def load_environment() -> None:
    """Load environment variables using the centralized loader."""
    EnvironmentLoader.load_environment()
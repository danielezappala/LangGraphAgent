"""Tests for the centralized environment loader."""
import os
from unittest.mock import patch
import pytest

from backend.core.env_loader import EnvironmentLoader


class TestEnvironmentLoader:
    """Test cases for EnvironmentLoader."""
    
    def setup_method(self):
        """Reset the loader state before each test."""
        EnvironmentLoader._loaded = False
    
    def test_load_environment_idempotent(self):
        """Test that load_environment can be called multiple times safely."""
        with patch('backend.core.env_loader.load_dotenv') as mock_load:
            EnvironmentLoader.load_environment()
            EnvironmentLoader.load_environment()  # Second call
            
            # Should only load once due to _loaded flag
            assert EnvironmentLoader._loaded is True
    
    def test_get_database_url_default(self):
        """Test database URL with default value."""
        with patch.dict(os.environ, {}, clear=True):
            url = EnvironmentLoader.get_database_url()
            assert url == "sqlite:///./langgraph_agent.db"
    
    def test_get_database_url_custom(self):
        """Test database URL with custom value."""
        custom_url = "postgresql://user:pass@localhost/db"
        with patch.dict(os.environ, {"DATABASE_URL": custom_url}):
            url = EnvironmentLoader.get_database_url()
            assert url == custom_url
    
    def test_get_api_config_defaults(self):
        """Test API configuration with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = EnvironmentLoader.get_api_config()
            
            assert config['host'] == "0.0.0.0"
            assert config['port'] == 8000
            assert config['frontend_port'] == 9002
            assert config['cors_origins'] == ["*"]
            assert config['debug'] is False
    
    def test_get_api_config_custom(self):
        """Test API configuration with custom values."""
        env_vars = {
            "BACKEND_HOST": "127.0.0.1",
            "BACKEND_PORT": "3000",
            "FRONTEND_PORT": "3001",
            "CORS_ORIGINS": "http://localhost:3000,http://localhost:3001",
            "DEBUG": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            config = EnvironmentLoader.get_api_config()
            
            assert config['host'] == "127.0.0.1"
            assert config['port'] == 3000
            assert config['frontend_port'] == 3001
            assert config['cors_origins'] == ["http://localhost:3000", "http://localhost:3001"]
            assert config['debug'] is True
    
    def test_get_openai_config(self):
        """Test OpenAI configuration extraction."""
        env_vars = {
            "OPENAI_API_KEY": "sk-test123",
            "OPENAI_MODEL": "gpt-3.5-turbo",
            "OPENAI_TEMPERATURE": "0.5",
            "OPENAI_MAX_TOKENS": "2000",
            "OPENAI_TIMEOUT": "60"
        }
        
        with patch.dict(os.environ, env_vars):
            config = EnvironmentLoader.get_openai_config()
            
            assert config['api_key'] == "sk-test123"
            assert config['model'] == "gpt-3.5-turbo"
            assert config['temperature'] == 0.5
            assert config['max_tokens'] == 2000
            assert config['timeout'] == 60
    
    def test_get_azure_config(self):
        """Test Azure OpenAI configuration extraction."""
        env_vars = {
            "AZURE_OPENAI_API_KEY": "azure-key-123",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_API_VERSION": "2024-02-15-preview",
            "AZURE_OPENAI_DEPLOYMENT": "gpt-4-deployment",
            "AZURE_OPENAI_MODEL": "gpt-4",
            "AZURE_OPENAI_TEMPERATURE": "0.3"
        }
        
        with patch.dict(os.environ, env_vars):
            config = EnvironmentLoader.get_azure_config()
            
            assert config['api_key'] == "azure-key-123"
            assert config['endpoint'] == "https://test.openai.azure.com/"
            assert config['api_version'] == "2024-02-15-preview"
            assert config['deployment'] == "gpt-4-deployment"
            assert config['model'] == "gpt-4"
            assert config['temperature'] == 0.3
    
    def test_get_external_api_keys(self):
        """Test external API keys extraction."""
        env_vars = {
            "TAVILY_API_KEY": "tavily-123",
            "NOTION_API_KEY": "notion-456"
        }
        
        with patch.dict(os.environ, env_vars):
            keys = EnvironmentLoader.get_external_api_keys()
            
            assert keys['tavily'] == "tavily-123"
            assert keys['notion'] == "notion-456"
    
    def test_is_development(self):
        """Test development mode detection."""
        # Test development mode
        with patch.dict(os.environ, {"NODE_ENV": "development"}):
            assert EnvironmentLoader.is_development() is True
        
        # Test production mode
        with patch.dict(os.environ, {"NODE_ENV": "production"}):
            assert EnvironmentLoader.is_development() is False
        
        # Test default (should be development)
        with patch.dict(os.environ, {}, clear=True):
            assert EnvironmentLoader.is_development() is True
    
    def test_print_config_summary(self, capsys):
        """Test configuration summary printing."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-test",
            "OPENAI_MODEL": "gpt-4"
        }
        
        with patch.dict(os.environ, env_vars):
            EnvironmentLoader.print_config_summary()
            
            captured = capsys.readouterr()
            assert "Environment Configuration Summary" in captured.out
            assert "LLM Provider: openai" in captured.out
            assert "OpenAI: Configured (model: gpt-4)" in captured.out


if __name__ == "__main__":
    pytest.main([__file__])
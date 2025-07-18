"""Unit tests for BootstrapService."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from services.bootstrap_service import BootstrapService, get_bootstrap_service
from database import DBProvider


class TestBootstrapService:
    """Test cases for BootstrapService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.bootstrap_service = BootstrapService(self.mock_db)
    
    def test_init(self):
        """Test BootstrapService initialization."""
        assert self.bootstrap_service.db == self.mock_db
    
    def test_get_bootstrap_service(self):
        """Test get_bootstrap_service factory function."""
        mock_db = Mock(spec=Session)
        service = get_bootstrap_service(mock_db)
        assert isinstance(service, BootstrapService)
        assert service.db == mock_db
    
    def test_is_first_startup_true(self):
        """Test is_first_startup when no providers exist."""
        self.mock_db.query.return_value.count.return_value = 0
        
        result = self.bootstrap_service.is_first_startup()
        
        assert result is True
    
    def test_is_first_startup_false(self):
        """Test is_first_startup when providers exist."""
        self.mock_db.query.return_value.count.return_value = 2
        
        result = self.bootstrap_service.is_first_startup()
        
        assert result is False
    
    def test_is_first_startup_exception(self):
        """Test is_first_startup with database exception."""
        self.mock_db.query.side_effect = Exception("Database error")
        
        result = self.bootstrap_service.is_first_startup()
        
        assert result is True  # Assume first startup on error
    
    @patch('services.bootstrap_service.EnvironmentLoader')
    def test_get_env_config_openai(self, mock_env_loader):
        """Test getting OpenAI environment configuration."""
        mock_env_loader.get_llm_provider.return_value = "openai"
        mock_env_loader.get_openai_config.return_value = {
            'api_key': 'sk-test123',
            'model': 'gpt-4'
        }
        
        result = self.bootstrap_service._get_env_config()
        
        assert result is not None
        assert result['name'] == 'Environment OpenAI'
        assert result['provider_type'] == 'openai'
        assert result['api_key'] == 'sk-test123'
        assert result['model'] == 'gpt-4'
    
    @patch('services.bootstrap_service.EnvironmentLoader')
    def test_get_env_config_azure(self, mock_env_loader):
        """Test getting Azure environment configuration."""
        mock_env_loader.get_llm_provider.return_value = "azure"
        mock_env_loader.get_azure_config.return_value = {
            'api_key': 'azure-key-123',
            'model': 'gpt-4',
            'endpoint': 'https://test.openai.azure.com/',
            'deployment': 'gpt-4-deployment',
            'api_version': '2023-05-15'
        }
        
        result = self.bootstrap_service._get_env_config()
        
        assert result is not None
        assert result['name'] == 'Environment Azure OpenAI'
        assert result['provider_type'] == 'azure'
        assert result['api_key'] == 'azure-key-123'
        assert result['endpoint'] == 'https://test.openai.azure.com/'
        assert result['deployment'] == 'gpt-4-deployment'
    
    @patch('services.bootstrap_service.EnvironmentLoader')
    def test_get_env_config_no_provider(self, mock_env_loader):
        """Test getting environment config when no provider is set."""
        mock_env_loader.get_llm_provider.return_value = None
        
        result = self.bootstrap_service._get_env_config()
        
        assert result is None
    
    @patch('services.bootstrap_service.EnvironmentLoader')
    def test_get_env_config_openai_no_key(self, mock_env_loader):
        """Test getting OpenAI config when no API key is set."""
        mock_env_loader.get_llm_provider.return_value = "openai"
        mock_env_loader.get_openai_config.return_value = {
            'api_key': None,
            'model': 'gpt-4'
        }
        
        result = self.bootstrap_service._get_env_config()
        
        assert result is None
    
    def test_import_env_to_database_success(self):
        """Test successful environment import to database."""
        env_config = {
            'name': 'Environment OpenAI',
            'provider_type': 'openai',
            'api_key': 'sk-test123',
            'model': 'gpt-4'
        }
        
        # Mock no existing provider
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.update = Mock()
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        
        with patch.object(self.bootstrap_service, '_get_env_config', return_value=env_config):
            with patch('services.bootstrap_service.DBProvider') as mock_db_provider:
                result = self.bootstrap_service.import_env_to_database()
        
        assert result is True
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_import_env_to_database_no_config(self):
        """Test environment import when no config is available."""
        with patch.object(self.bootstrap_service, '_get_env_config', return_value=None):
            result = self.bootstrap_service.import_env_to_database()
        
        assert result is False
    
    def test_import_env_to_database_existing_provider(self):
        """Test environment import when provider already exists."""
        env_config = {
            'name': 'Environment OpenAI',
            'provider_type': 'openai',
            'api_key': 'sk-test123'
        }
        
        # Mock existing provider
        mock_existing = Mock(spec=DBProvider)
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_existing
        
        with patch.object(self.bootstrap_service, '_get_env_config', return_value=env_config):
            result = self.bootstrap_service.import_env_to_database()
        
        assert result is True
        # Should not add new provider
        self.mock_db.add.assert_not_called()
    
    def test_import_env_to_database_exception(self):
        """Test environment import with database exception."""
        env_config = {
            'name': 'Environment OpenAI',
            'provider_type': 'openai',
            'api_key': 'sk-test123'
        }
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.add.side_effect = Exception("Database error")
        self.mock_db.rollback = Mock()
        
        with patch.object(self.bootstrap_service, '_get_env_config', return_value=env_config):
            with patch('services.bootstrap_service.DBProvider'):
                result = self.bootstrap_service.import_env_to_database()
        
        assert result is False
        self.mock_db.rollback.assert_called_once()
    
    @patch('services.bootstrap_service.EnvironmentLoader')
    def test_create_default_providers_success(self, mock_env_loader):
        """Test successful creation of default providers."""
        mock_env_loader.get_openai_config.return_value = {
            'api_key': 'sk-test123',
            'model': 'gpt-4'
        }
        mock_env_loader.get_azure_config.return_value = {
            'api_key': 'azure-key',
            'model': 'gpt-4',
            'endpoint': 'https://test.openai.azure.com/',
            'deployment': 'gpt-4',
            'api_version': '2023-05-15'
        }
        
        # Mock no existing providers
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        
        with patch('services.bootstrap_service.DBProvider') as mock_db_provider:
            result = self.bootstrap_service.create_default_providers()
        
        assert result is True
        # Should add 2 providers (OpenAI and Azure)
        assert self.mock_db.add.call_count == 2
        self.mock_db.commit.assert_called_once()
    
    @patch('services.bootstrap_service.EnvironmentLoader')
    def test_create_default_providers_existing(self, mock_env_loader):
        """Test creating default providers when they already exist."""
        mock_env_loader.get_openai_config.return_value = {
            'api_key': 'sk-test123',
            'model': 'gpt-4'
        }
        mock_env_loader.get_azure_config.return_value = {
            'api_key': 'azure-key',
            'model': 'gpt-4',
            'endpoint': 'https://test.openai.azure.com/',
            'deployment': 'gpt-4',
            'api_version': '2023-05-15'
        }
        
        # Mock existing providers
        mock_existing = Mock(spec=DBProvider)
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_existing
        self.mock_db.commit = Mock()
        
        result = self.bootstrap_service.create_default_providers()
        
        assert result is True
        # Should not add any providers
        self.mock_db.add.assert_not_called()
        self.mock_db.commit.assert_called_once()
    
    def test_run_bootstrap_if_needed_first_startup_with_env(self):
        """Test bootstrap on first startup with environment config."""
        with patch.object(self.bootstrap_service, 'is_first_startup', return_value=True):
            with patch.object(self.bootstrap_service, 'import_env_to_database', return_value=True):
                with patch.object(self.bootstrap_service, 'mark_bootstrap_complete'):
                    result = self.bootstrap_service.run_bootstrap_if_needed()
        
        assert result is True
    
    def test_run_bootstrap_if_needed_first_startup_no_env(self):
        """Test bootstrap on first startup without environment config."""
        with patch.object(self.bootstrap_service, 'is_first_startup', return_value=True):
            with patch.object(self.bootstrap_service, 'import_env_to_database', return_value=False):
                with patch.object(self.bootstrap_service, 'create_default_providers', return_value=True):
                    with patch.object(self.bootstrap_service, 'mark_bootstrap_complete'):
                        result = self.bootstrap_service.run_bootstrap_if_needed()
        
        assert result is True
    
    def test_run_bootstrap_if_needed_not_first_startup(self):
        """Test bootstrap when not first startup."""
        with patch.object(self.bootstrap_service, 'is_first_startup', return_value=False):
            result = self.bootstrap_service.run_bootstrap_if_needed()
        
        assert result is True
    
    def test_run_bootstrap_if_needed_failure(self):
        """Test bootstrap failure scenario."""
        with patch.object(self.bootstrap_service, 'is_first_startup', return_value=True):
            with patch.object(self.bootstrap_service, 'import_env_to_database', return_value=False):
                with patch.object(self.bootstrap_service, 'create_default_providers', return_value=False):
                    result = self.bootstrap_service.run_bootstrap_if_needed()
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
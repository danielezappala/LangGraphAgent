"""Unit tests for ProviderService."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.provider_service import (
    ProviderService, 
    ValidationResult, 
    TestResult, 
    ProviderStatus,
    get_provider_service
)
from database import DBProvider


class TestProviderService:
    """Test cases for ProviderService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.provider_service = ProviderService(self.mock_db)
    
    def test_init(self):
        """Test ProviderService initialization."""
        assert self.provider_service.db == self.mock_db
    
    def test_get_provider_service(self):
        """Test get_provider_service factory function."""
        mock_db = Mock(spec=Session)
        service = get_provider_service(mock_db)
        assert isinstance(service, ProviderService)
        assert service.db == mock_db
    
    def test_list_all_providers_success(self):
        """Test successful provider listing."""
        # Mock database providers
        mock_provider1 = Mock(spec=DBProvider)
        mock_provider1.id = 1
        mock_provider1.name = "OpenAI"
        mock_provider1.provider_type = "openai"
        mock_provider1.api_key = "sk-test"
        mock_provider1.model = "gpt-4"
        mock_provider1.endpoint = None
        mock_provider1.deployment = None
        mock_provider1.api_version = None
        mock_provider1.is_active = True
        mock_provider1.is_from_env = False
        mock_provider1.is_valid = True
        mock_provider1.connection_status = "connected"
        mock_provider1.last_tested = datetime(2025, 1, 17, 12, 0, 0)
        mock_provider1.created_at = datetime(2025, 1, 17, 10, 0, 0)
        mock_provider1.updated_at = datetime(2025, 1, 17, 11, 0, 0)
        
        self.mock_db.query.return_value.all.return_value = [mock_provider1]
        
        result = self.provider_service.list_all_providers()
        
        assert len(result) == 1
        assert result[0]['id'] == 1
        assert result[0]['name'] == "OpenAI"
        assert result[0]['provider_type'] == "openai"
        assert result[0]['is_active'] is True
    
    def test_list_all_providers_empty(self):
        """Test provider listing when no providers exist."""
        self.mock_db.query.return_value.all.return_value = []
        
        result = self.provider_service.list_all_providers()
        
        assert result == []
    
    def test_list_all_providers_exception(self):
        """Test provider listing with database exception."""
        self.mock_db.query.side_effect = Exception("Database error")
        
        result = self.provider_service.list_all_providers()
        
        assert result == []
    
    def test_get_active_provider_success(self):
        """Test getting active provider successfully."""
        mock_provider = Mock(spec=DBProvider)
        mock_provider.id = 1
        mock_provider.name = "Azure OpenAI"
        mock_provider.provider_type = "azure"
        mock_provider.api_key = "test-key"
        mock_provider.model = "gpt-4"
        mock_provider.endpoint = "https://test.openai.azure.com/"
        mock_provider.deployment = "gpt-4"
        mock_provider.api_version = "2023-05-15"
        mock_provider.is_active = True
        mock_provider.is_from_env = True
        mock_provider.is_valid = True
        mock_provider.connection_status = "connected"
        mock_provider.last_tested = datetime(2025, 1, 17, 12, 0, 0)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_provider
        
        result = self.provider_service.get_active_provider()
        
        assert result is not None
        assert result['id'] == 1
        assert result['name'] == "Azure OpenAI"
        assert result['provider_type'] == "azure"
        assert result['is_active'] is True
        assert result['source'] == 'database'
    
    def test_get_active_provider_none(self):
        """Test getting active provider when none exists."""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.provider_service.get_active_provider()
        
        assert result is None
    
    def test_create_provider_success(self):
        """Test successful provider creation."""
        config = {
            'name': 'Test OpenAI',
            'provider_type': 'openai',
            'api_key': 'sk-test123',
            'model': 'gpt-4',
            'is_active': True
        }
        
        mock_new_provider = Mock(spec=DBProvider)
        mock_new_provider.id = 1
        mock_new_provider.name = config['name']
        mock_new_provider.provider_type = config['provider_type']
        mock_new_provider.api_key = config['api_key']
        mock_new_provider.model = config['model']
        mock_new_provider.endpoint = None
        mock_new_provider.deployment = None
        mock_new_provider.api_version = None
        mock_new_provider.is_active = config['is_active']
        
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        self.mock_db.query.return_value.update = Mock()
        
        # Mock the validation
        with patch.object(self.provider_service, 'validate_provider_config') as mock_validate:
            mock_validate.return_value = ValidationResult(is_valid=True)
            
            # Mock DBProvider constructor
            with patch('services.provider_service.DBProvider', return_value=mock_new_provider):
                result = self.provider_service.create_provider(config)
        
        assert result is not None
        assert result['name'] == config['name']
        assert result['provider_type'] == config['provider_type']
        assert result['is_active'] is True
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_create_provider_validation_failure(self):
        """Test provider creation with validation failure."""
        config = {
            'name': '',  # Invalid name
            'provider_type': 'openai',
            'api_key': 'sk-test123'
        }
        
        with patch.object(self.provider_service, 'validate_provider_config') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=False, 
                errors=["Provider name is required"]
            )
            
            with pytest.raises(ValueError, match="Invalid configuration"):
                self.provider_service.create_provider(config)
    
    def test_create_provider_integrity_error(self):
        """Test provider creation with database integrity error."""
        config = {
            'name': 'Test OpenAI',
            'provider_type': 'openai',
            'api_key': 'sk-test123'
        }
        
        self.mock_db.add.side_effect = IntegrityError("UNIQUE constraint failed", None, None)
        self.mock_db.rollback = Mock()
        
        with patch.object(self.provider_service, 'validate_provider_config') as mock_validate:
            mock_validate.return_value = ValidationResult(is_valid=True)
            
            with pytest.raises(ValueError, match="A provider with this name already exists"):
                self.provider_service.create_provider(config)
        
        self.mock_db.rollback.assert_called_once()
    
    def test_validate_provider_config_openai_valid(self):
        """Test validation of valid OpenAI configuration."""
        config = {
            'name': 'Test OpenAI',
            'provider_type': 'openai',
            'api_key': 'sk-test123456789',
            'model': 'gpt-4'
        }
        
        result = self.provider_service.validate_provider_config(config)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_provider_config_azure_valid(self):
        """Test validation of valid Azure configuration."""
        config = {
            'name': 'Test Azure',
            'provider_type': 'azure',
            'api_key': 'test-azure-key-123',
            'model': 'gpt-4',
            'endpoint': 'https://test.openai.azure.com/',
            'deployment': 'gpt-4-deployment',
            'api_version': '2023-05-15'
        }
        
        result = self.provider_service.validate_provider_config(config)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_provider_config_missing_name(self):
        """Test validation with missing name."""
        config = {
            'provider_type': 'openai',
            'api_key': 'sk-test123'
        }
        
        result = self.provider_service.validate_provider_config(config)
        
        assert result.is_valid is False
        assert "Provider name is required" in result.errors
    
    def test_validate_provider_config_invalid_provider_type(self):
        """Test validation with invalid provider type."""
        config = {
            'name': 'Test',
            'provider_type': 'invalid',
            'api_key': 'test-key'
        }
        
        result = self.provider_service.validate_provider_config(config)
        
        assert result.is_valid is False
        assert "Provider type must be 'openai' or 'azure'" in result.errors
    
    def test_validate_provider_config_azure_missing_endpoint(self):
        """Test validation of Azure config missing endpoint."""
        config = {
            'name': 'Test Azure',
            'provider_type': 'azure',
            'api_key': 'test-key',
            'deployment': 'gpt-4'
        }
        
        result = self.provider_service.validate_provider_config(config)
        
        assert result.is_valid is False
        assert "Endpoint is required for Azure OpenAI" in result.errors
    
    def test_validate_provider_config_short_api_key(self):
        """Test validation with short API key (warning)."""
        config = {
            'name': 'Test',
            'provider_type': 'openai',
            'api_key': 'short'
        }
        
        result = self.provider_service.validate_provider_config(config)
        
        assert result.is_valid is True  # Still valid, but with warning
        assert "API key seems too short" in result.warnings
    
    def test_get_provider_status_with_active_provider(self):
        """Test getting provider status with active provider."""
        mock_provider = Mock(spec=DBProvider)
        mock_provider.name = "Test Provider"
        
        with patch.object(self.provider_service, 'get_active_provider') as mock_get_active:
            mock_get_active.return_value = {'name': 'Test Provider'}
            self.mock_db.query.return_value.count.return_value = 2
            
            result = self.provider_service.get_provider_status()
        
        assert isinstance(result, ProviderStatus)
        assert result.has_active_provider is True
        assert result.active_provider_name == 'Test Provider'
        assert result.total_providers == 2
        assert result.configuration_source == 'database'
        assert len(result.issues) == 0
    
    def test_get_provider_status_no_active_provider(self):
        """Test getting provider status with no active provider."""
        with patch.object(self.provider_service, 'get_active_provider') as mock_get_active:
            mock_get_active.return_value = None
            self.mock_db.query.return_value.count.return_value = 1
            
            result = self.provider_service.get_provider_status()
        
        assert result.has_active_provider is False
        assert result.active_provider_name is None
        assert "No active provider configured" in result.issues
    
    @patch('services.provider_service.requests')
    def test_test_openai_connection_success(self, mock_requests):
        """Test successful OpenAI connection test."""
        config = {
            'provider_type': 'openai',
            'api_key': 'sk-test123'
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response
        
        with patch('services.provider_service.time.time', side_effect=[0, 0.1]):
            result = self.provider_service.test_provider_connection(config)
        
        assert isinstance(result, TestResult)
        assert result.success is True
        assert result.message == "Connection successful"
        assert result.response_time_ms == 100
    
    @patch('services.provider_service.requests')
    def test_test_openai_connection_failure(self, mock_requests):
        """Test failed OpenAI connection test."""
        config = {
            'provider_type': 'openai',
            'api_key': 'invalid-key'
        }
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_requests.get.return_value = mock_response
        
        with patch('services.provider_service.time.time', side_effect=[0, 0.05]):
            result = self.provider_service.test_provider_connection(config)
        
        assert result.success is False
        assert "API returned status 401" in result.message
        assert result.response_time_ms == 50
    
    @patch('services.provider_service.requests')
    def test_test_azure_connection_success(self, mock_requests):
        """Test successful Azure connection test."""
        config = {
            'provider_type': 'azure',
            'api_key': 'test-key',
            'endpoint': 'https://test.openai.azure.com/',
            'deployment': 'gpt-4',
            'api_version': '2023-05-15'
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response
        
        with patch('services.provider_service.time.time', side_effect=[0, 0.2]):
            result = self.provider_service.test_provider_connection(config)
        
        assert result.success is True
        assert result.message == "Connection successful"
        assert result.response_time_ms == 200
    
    def test_test_connection_unsupported_provider(self):
        """Test connection test with unsupported provider type."""
        config = {
            'provider_type': 'unsupported',
            'api_key': 'test-key'
        }
        
        result = self.provider_service.test_provider_connection(config)
        
        assert result.success is False
        assert "Unsupported provider type" in result.message
    
    def test_delete_provider_success(self):
        """Test successful provider deletion."""
        mock_provider = Mock(spec=DBProvider)
        mock_provider.is_active = False
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_provider
        self.mock_db.delete = Mock()
        self.mock_db.commit = Mock()
        
        result = self.provider_service.delete_provider(1)
        
        assert result is True
        self.mock_db.delete.assert_called_once_with(mock_provider)
        self.mock_db.commit.assert_called_once()
    
    def test_delete_provider_not_found(self):
        """Test deleting non-existent provider."""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Provider not found"):
            self.provider_service.delete_provider(999)
    
    def test_delete_active_provider(self):
        """Test deleting active provider (should fail)."""
        mock_provider = Mock(spec=DBProvider)
        mock_provider.is_active = True
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_provider
        
        with pytest.raises(ValueError, match="Cannot delete the active provider"):
            self.provider_service.delete_provider(1)


if __name__ == "__main__":
    pytest.main([__file__])
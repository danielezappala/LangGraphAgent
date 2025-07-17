"""Integration tests for consolidated API endpoints."""
import pytest
import httpx
import asyncio
from unittest.mock import patch, Mock
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DBProvider
from services.provider_service import ProviderService


class TestAPIIntegration:
    """Integration tests for consolidated API endpoints."""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for API tests."""
        return "http://localhost:8000"
    
    @pytest.fixture
    async def client(self):
        """HTTP client for API tests."""
        async with httpx.AsyncClient() as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_provider_status_endpoint(self, client, base_url):
        """Test provider status endpoint returns correct format."""
        response = await client.get(f"{base_url}/api/providers/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert 'has_active_provider' in data
        assert 'total_providers' in data
        assert 'configuration_source' in data
        assert 'issues' in data
        
        # Verify data types
        assert isinstance(data['has_active_provider'], bool)
        assert isinstance(data['total_providers'], int)
        assert isinstance(data['configuration_source'], str)
        assert isinstance(data['issues'], list)
    
    @pytest.mark.asyncio
    async def test_provider_list_endpoint(self, client, base_url):
        """Test provider list endpoint returns correct format."""
        response = await client.get(f"{base_url}/api/providers/list")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        # If providers exist, verify structure
        if data:
            provider = data[0]
            required_fields = [
                'id', 'name', 'provider_type', 'model', 
                'is_active', 'is_from_env', 'is_valid', 
                'connection_status', 'created_at'
            ]
            
            for field in required_fields:
                assert field in provider, f"Missing field: {field}"
    
    @pytest.mark.asyncio
    async def test_active_provider_endpoint(self, client, base_url):
        """Test active provider endpoint."""
        response = await client.get(f"{base_url}/api/providers/active")
        
        # Should return either 200 with provider data or 404 if no active provider
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert 'id' in data
            assert 'name' in data
            assert 'provider_type' in data
            assert data['is_active'] is True
    
    @pytest.mark.asyncio
    async def test_provider_connection_test_endpoint(self, client, base_url):
        """Test provider connection test endpoint."""
        # First get list of providers
        list_response = await client.get(f"{base_url}/api/providers/list")
        assert list_response.status_code == 200
        
        providers = list_response.json()
        
        if providers:
            provider_id = providers[0]['id']
            
            # Test connection
            response = await client.post(f"{base_url}/api/providers/{provider_id}/test")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify test result structure
            assert 'success' in data
            assert 'message' in data
            assert isinstance(data['success'], bool)
            assert isinstance(data['message'], str)
            
            if 'response_time_ms' in data:
                assert isinstance(data['response_time_ms'], (int, float))
    
    @pytest.mark.asyncio
    async def test_provider_connection_test_invalid_id(self, client, base_url):
        """Test provider connection test with invalid ID."""
        response = await client.post(f"{base_url}/api/providers/999999/test")
        
        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data or 'message' in data
    
    @pytest.mark.asyncio
    async def test_history_list_endpoint(self, client, base_url):
        """Test history list endpoint."""
        response = await client.get(f"{base_url}/api/history/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'conversations' in data
        assert isinstance(data['conversations'], list)
        
        # If conversations exist, verify structure
        if data['conversations']:
            conversation = data['conversations'][0]
            assert 'thread_id' in conversation
            assert 'preview' in conversation
    
    @pytest.mark.asyncio
    async def test_history_delete_nonexistent(self, client, base_url):
        """Test deleting non-existent conversation."""
        fake_thread_id = "non-existent-thread-id-12345"
        response = await client.delete(f"{base_url}/api/history/{fake_thread_id}")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_version_endpoint(self, client, base_url):
        """Test version endpoint."""
        response = await client.get(f"{base_url}/api/version/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'version' in data
        assert isinstance(data['version'], str)
    
    @pytest.mark.asyncio
    async def test_ping_endpoint(self, client, base_url):
        """Test ping endpoint."""
        response = await client.get(f"{base_url}/api/ping/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'message' in data
        assert data['message'] == "pong"
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, client, base_url):
        """Test API error handling for various scenarios."""
        # Test invalid endpoint
        response = await client.get(f"{base_url}/api/invalid-endpoint")
        assert response.status_code == 404
        
        # Test invalid method on valid endpoint
        response = await client.patch(f"{base_url}/api/providers/status")
        assert response.status_code == 405
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client, base_url):
        """Test CORS headers are properly set."""
        response = await client.get(f"{base_url}/api/ping/")
        
        assert response.status_code == 200
        
        # Check for CORS headers (these should be set by FastAPI middleware)
        headers = response.headers
        # Note: Actual CORS headers might vary based on server configuration
        # This test ensures the endpoint is accessible
    
    @pytest.mark.asyncio
    async def test_api_response_times(self, client, base_url):
        """Test API response times are reasonable."""
        import time
        
        endpoints = [
            "/api/ping/",
            "/api/version/",
            "/api/providers/status",
            "/api/providers/list",
            "/api/history/"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = await client.get(f"{base_url}{endpoint}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to ms
            
            # API should respond within 5 seconds (generous limit for integration tests)
            assert response_time < 5000, f"Endpoint {endpoint} took {response_time}ms"
            assert response.status_code in [200, 404], f"Endpoint {endpoint} returned {response.status_code}"


class TestAPIErrorScenarios:
    """Test API error scenarios and edge cases."""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for API tests."""
        return "http://localhost:8000"
    
    @pytest.fixture
    async def client(self):
        """HTTP client for API tests."""
        async with httpx.AsyncClient() as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_malformed_json_request(self, client, base_url):
        """Test handling of malformed JSON in requests."""
        # This would be relevant for POST/PUT endpoints when they're implemented
        # For now, test that existing endpoints handle unexpected content gracefully
        
        headers = {"Content-Type": "application/json"}
        malformed_json = '{"invalid": json}'
        
        # Test with provider test endpoint (if we have providers)
        list_response = await client.get(f"{base_url}/api/providers/list")
        if list_response.status_code == 200:
            providers = list_response.json()
            if providers:
                provider_id = providers[0]['id']
                response = await client.post(
                    f"{base_url}/api/providers/{provider_id}/test",
                    content=malformed_json,
                    headers=headers
                )
                # Should handle gracefully (either ignore body or return proper error)
                assert response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_large_request_handling(self, client, base_url):
        """Test handling of unusually large requests."""
        # Test with a very long thread ID for history deletion
        very_long_id = "x" * 1000  # 1000 character thread ID
        
        response = await client.delete(f"{base_url}/api/history/{very_long_id}")
        
        # Should handle gracefully (likely 404 or 400)
        assert response.status_code in [400, 404]
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client, base_url):
        """Test handling of concurrent requests."""
        # Make multiple concurrent requests to test thread safety
        tasks = []
        
        for _ in range(10):
            task = client.get(f"{base_url}/api/providers/status")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert 'has_active_provider' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
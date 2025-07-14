import httpx
import asyncio
import json

async def test_config_endpoints():
    base_url = "http://localhost:8000/api"
    
    async with httpx.AsyncClient() as client:
        # Test GET /api/config
        print("Testing GET /api/config...")
        response = await client.get(f"{base_url}/config")
        print(f"Status: {response.status_code}")
        print("Current config:", json.dumps(response.json(), indent=2))
        
        # Test switching to OpenAI
        print("\nTesting POST /api/config (OpenAI)...")
        openai_config = {
            "provider": "openai",
            "openai_api_key": "test-openai-key",
            "openai_model": "gpt-4",
            "openai_temperature": 0.7
        }
        response = await client.post(f"{base_url}/config", json=openai_config)
        print(f"Status: {response.status_code}")
        print("Response:", response.json())
        
        # Test switching to Azure
        print("\nTesting POST /api/config (Azure)...")
        azure_config = {
            "provider": "azure",
            "azure_api_key": "test-azure-key",
            "azure_endpoint": "https://test-endpoint.openai.azure.com/",
            "azure_deployment": "test-deployment",
            "azure_api_version": "2023-05-15"
        }
        response = await client.post(f"{base_url}/config", json=azure_config)
        print(f"Status: {response.status_code}")
        print("Response:", response.json())
        
        # Verify the current config
        print("\nVerifying current config...")
        response = await client.get(f"{base_url}/config")
        print(f"Status: {response.status_code}")
        print("Current config:", json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    asyncio.run(test_config_endpoints())

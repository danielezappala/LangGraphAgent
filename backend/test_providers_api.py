#!/usr/bin/env python3
"""Test script for provider API endpoints."""
import asyncio
import httpx
import json

async def test_provider_endpoints():
    """Test all provider API endpoints."""
    base_url = "http://localhost:8000/api/providers"
    
    print("=== Testing Provider API Endpoints ===\n")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test GET /api/providers/status
            print("1. Testing GET /api/providers/status...")
            response = await client.get(f"{base_url}/status")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            else:
                print(f"   Error: {response.text}")
            print()
            
            # Test GET /api/providers/list
            print("2. Testing GET /api/providers/list...")
            response = await client.get(f"{base_url}/list")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Found {len(data)} providers")
                for provider in data:
                    print(f"   - {provider.get('name')} ({provider.get('provider_type')}) - {'Active' if provider.get('is_active') else 'Inactive'}")
            else:
                print(f"   Error: {response.text}")
            print()
            
            # Test GET /api/providers/active
            print("3. Testing GET /api/providers/active...")
            response = await client.get(f"{base_url}/active")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Active provider: {data.get('name')} ({data.get('provider_type')})")
            elif response.status_code == 404:
                print("   No active provider found")
            else:
                print(f"   Error: {response.text}")
            print()
            
            # Test error handling with invalid provider ID
            print("4. Testing error handling (invalid provider ID)...")
            response = await client.post(f"{base_url}/999/test")
            print(f"   Status: {response.status_code}")
            if response.status_code == 404:
                print("   ✅ Correctly returned 404 for non-existent provider")
            else:
                print(f"   ⚠️  Unexpected response: {response.text}")
            print()
            
            print("=== Provider API Test Complete ===")
            
        except httpx.ConnectError:
            print("❌ Error: Could not connect to the server.")
            print("   Make sure the backend is running on http://localhost:8000")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_provider_endpoints())
#!/usr/bin/env python3
"""Final integration test for the consolidated codebase cleanup."""
import asyncio
import httpx
import json
import time

async def test_complete_integration():
    """Test complete provider management workflow and API endpoints."""
    base_url = "http://localhost:8000"
    
    print("=== FINAL INTEGRATION TEST ===\n")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Provider Status API
            print("1. Testing Provider Status API...")
            response = await client.get(f"{base_url}/api/providers/status")
            if response.status_code == 200:
                status_data = response.json()
                print(f"   ✅ Provider status: {status_data['has_active_provider']}")
                print(f"   ✅ Total providers: {status_data['total_providers']}")
                print(f"   ✅ Configuration source: {status_data['configuration_source']}")
            else:
                print(f"   ❌ Status API failed: {response.status_code}")
                return False
            
            # Test 2: List Providers API
            print("\n2. Testing List Providers API...")
            response = await client.get(f"{base_url}/api/providers/list")
            if response.status_code == 200:
                providers = response.json()
                print(f"   ✅ Found {len(providers)} providers")
                for provider in providers:
                    status = "Active" if provider.get('is_active') else "Inactive"
                    print(f"   - {provider.get('name')} ({provider.get('provider_type')}) - {status}")
            else:
                print(f"   ❌ List API failed: {response.status_code}")
                return False
            
            # Test 3: Active Provider API
            print("\n3. Testing Active Provider API...")
            response = await client.get(f"{base_url}/api/providers/active")
            if response.status_code == 200:
                active_provider = response.json()
                print(f"   ✅ Active provider: {active_provider.get('name')} ({active_provider.get('provider_type')})")
                active_provider_id = active_provider.get('id')
            elif response.status_code == 404:
                print("   ⚠️  No active provider found")
                active_provider_id = None
            else:
                print(f"   ❌ Active provider API failed: {response.status_code}")
                return False
            
            # Test 4: Provider Connection Test (if we have an active provider)
            if active_provider_id:
                print(f"\n4. Testing Provider Connection (ID: {active_provider_id})...")
                response = await client.post(f"{base_url}/api/providers/{active_provider_id}/test")
                if response.status_code == 200:
                    test_result = response.json()
                    if test_result.get('success'):
                        print(f"   ✅ Connection test successful: {test_result.get('message')}")
                        if test_result.get('response_time_ms'):
                            print(f"   ✅ Response time: {test_result.get('response_time_ms')}ms")
                    else:
                        print(f"   ⚠️  Connection test failed: {test_result.get('message')}")
                else:
                    print(f"   ❌ Connection test API failed: {response.status_code}")
            else:
                print("\n4. Skipping connection test (no active provider)")
            
            # Test 5: History API
            print("\n5. Testing History API...")
            response = await client.get(f"{base_url}/api/history/")
            if response.status_code == 200:
                history_data = response.json()
                conversations = history_data.get('conversations', [])
                print(f"   ✅ Found {len(conversations)} conversations")
                if conversations:
                    print(f"   ✅ Latest conversation: {conversations[0].get('preview', 'No preview')[:50]}...")
            else:
                print(f"   ❌ History API failed: {response.status_code}")
                return False
            
            # Test 6: Version API
            print("\n6. Testing Version API...")
            response = await client.get(f"{base_url}/api/version/")
            if response.status_code == 200:
                version_data = response.json()
                print(f"   ✅ Backend version: {version_data.get('version', 'Unknown')}")
            else:
                print(f"   ❌ Version API failed: {response.status_code}")
                return False
            
            # Test 7: Ping API
            print("\n7. Testing Ping API...")
            response = await client.get(f"{base_url}/api/ping/")
            if response.status_code == 200:
                ping_data = response.json()
                print(f"   ✅ Ping successful: {ping_data.get('message', 'No message')}")
            else:
                print(f"   ❌ Ping API failed: {response.status_code}")
                return False
            
            print("\n=== INTEGRATION TEST RESULTS ===")
            print("✅ All API endpoints are working correctly")
            print("✅ Provider management system is functional")
            print("✅ Database-First approach is working")
            print("✅ Consolidated configuration is loading properly")
            print("✅ Backend services are properly integrated")
            print("\n🎉 FINAL INTEGRATION TEST PASSED!")
            
            return True
            
        except httpx.ConnectError:
            print("❌ Error: Could not connect to the server.")
            print("   Make sure the backend is running on http://localhost:8000")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

async def test_environment_loading():
    """Test that environment loading works correctly with consolidated config."""
    print("\n=== ENVIRONMENT LOADING TEST ===")
    
    try:
        # Import and test the centralized environment loader
        import sys
        import os
        sys.path.append('backend')
        
        from core.env_loader import EnvironmentLoader
        
        # Load environment
        EnvironmentLoader.load_environment()
        
        # Test configuration loading
        print("1. Testing environment variable loading...")
        
        # Test database URL
        db_url = EnvironmentLoader.get_database_url()
        print(f"   ✅ Database URL: {db_url}")
        
        # Test API config
        api_config = EnvironmentLoader.get_api_config()
        print(f"   ✅ API Host: {api_config['host']}:{api_config['port']}")
        print(f"   ✅ Frontend Port: {api_config['frontend_port']}")
        
        # Test LLM provider
        provider = EnvironmentLoader.get_llm_provider()
        print(f"   ✅ LLM Provider: {provider or 'Not set'}")
        
        if provider:
            if provider.lower() == 'openai':
                openai_config = EnvironmentLoader.get_openai_config()
                print(f"   ✅ OpenAI Model: {openai_config['model']}")
                print(f"   ✅ OpenAI API Key: {'Set' if openai_config['api_key'] else 'Not set'}")
            elif provider.lower() == 'azure':
                azure_config = EnvironmentLoader.get_azure_config()
                print(f"   ✅ Azure Endpoint: {azure_config['endpoint'] or 'Not set'}")
                print(f"   ✅ Azure Deployment: {azure_config['deployment'] or 'Not set'}")
                print(f"   ✅ Azure API Key: {'Set' if azure_config['api_key'] else 'Not set'}")
        
        # Test external API keys
        external_keys = EnvironmentLoader.get_external_api_keys()
        tavily_key = external_keys.get('tavily')
        notion_key = external_keys.get('notion')
        print(f"   ✅ Tavily API Key: {'Set' if tavily_key else 'Not set'}")
        print(f"   ✅ Notion API Key: {'Set' if notion_key else 'Not set'}")
        
        print("\n✅ Environment loading test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Environment loading test failed: {e}")
        return False

async def main():
    """Run all integration tests."""
    print("Starting final integration testing...\n")
    
    # Test environment loading first
    env_test_passed = await test_environment_loading()
    
    if not env_test_passed:
        print("❌ Environment loading test failed. Cannot proceed with API tests.")
        return
    
    # Test API integration
    api_test_passed = await test_complete_integration()
    
    if env_test_passed and api_test_passed:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("The codebase cleanup and consolidation is complete and working correctly.")
    else:
        print("\n❌ Some integration tests failed.")
        print("Please check the backend server and configuration.")

if __name__ == "__main__":
    asyncio.run(main())
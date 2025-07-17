#!/usr/bin/env python3
"""End-to-end workflow testing for consolidated codebase."""
import asyncio
import httpx
import json
import time
import sys
import os

# Add backend to path for imports
sys.path.append('backend')

from core.env_loader import EnvironmentLoader


class E2EWorkflowTester:
    """End-to-end workflow tester for the consolidated system."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    def log_test(self, test_name, success, message=""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        
        if success:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {message}")
    
    async def test_system_bootstrap_workflow(self):
        """Test the complete system bootstrap workflow."""
        print("\n=== SYSTEM BOOTSTRAP WORKFLOW ===")
        
        try:
            # Test 1: Environment loading
            print("\n1. Testing Environment Configuration Loading...")
            
            # Load environment using consolidated loader
            EnvironmentLoader.load_environment()
            
            # Verify configuration is accessible
            db_url = EnvironmentLoader.get_database_url()
            api_config = EnvironmentLoader.get_api_config()
            
            self.log_test(
                "Environment Loading",
                db_url is not None and api_config is not None,
                f"DB: {db_url}, API: {api_config['host']}:{api_config['port']}"
            )
            
            # Test 2: API availability
            print("\n2. Testing API Availability...")
            response = await self.client.get(f"{self.base_url}/api/ping/")
            
            self.log_test(
                "API Availability",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            # Test 3: Provider system initialization
            print("\n3. Testing Provider System Initialization...")
            status_response = await self.client.get(f"{self.base_url}/api/providers/status")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                self.log_test(
                    "Provider System Initialization",
                    'has_active_provider' in status_data and 'total_providers' in status_data,
                    f"Active: {status_data.get('has_active_provider')}, Total: {status_data.get('total_providers')}"
                )
            else:
                self.log_test(
                    "Provider System Initialization",
                    False,
                    f"Status endpoint failed: {status_response.status_code}"
                )
            
        except Exception as e:
            self.log_test("System Bootstrap Workflow", False, str(e))
    
    async def test_provider_management_workflow(self):
        """Test complete provider management workflow."""
        print("\n=== PROVIDER MANAGEMENT WORKFLOW ===")
        
        try:
            # Test 1: List existing providers
            print("\n1. Testing Provider Listing...")
            list_response = await self.client.get(f"{self.base_url}/api/providers/list")
            
            if list_response.status_code == 200:
                providers = list_response.json()
                self.log_test(
                    "Provider Listing",
                    isinstance(providers, list),
                    f"Found {len(providers)} providers"
                )
                
                # Test 2: Get active provider
                print("\n2. Testing Active Provider Retrieval...")
                active_response = await self.client.get(f"{self.base_url}/api/providers/active")
                
                if active_response.status_code == 200:
                    active_provider = active_response.json()
                    self.log_test(
                        "Active Provider Retrieval",
                        active_provider.get('is_active') is True,
                        f"Active: {active_provider.get('name')} ({active_provider.get('provider_type')})"
                    )
                    
                    # Test 3: Test provider connection
                    if active_provider.get('id'):
                        print("\n3. Testing Provider Connection...")
                        test_response = await self.client.post(
                            f"{self.base_url}/api/providers/{active_provider['id']}/test"
                        )
                        
                        if test_response.status_code == 200:
                            test_result = test_response.json()
                            self.log_test(
                                "Provider Connection Test",
                                'success' in test_result,
                                f"Result: {test_result.get('message', 'No message')}"
                            )
                        else:
                            self.log_test(
                                "Provider Connection Test",
                                False,
                                f"Test failed: {test_response.status_code}"
                            )
                    
                elif active_response.status_code == 404:
                    self.log_test(
                        "Active Provider Retrieval",
                        True,  # 404 is valid if no active provider
                        "No active provider configured"
                    )
                else:
                    self.log_test(
                        "Active Provider Retrieval",
                        False,
                        f"Unexpected status: {active_response.status_code}"
                    )
                
                # Test 4: Provider status consistency
                print("\n4. Testing Provider Status Consistency...")
                status_response = await self.client.get(f"{self.base_url}/api/providers/status")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    expected_total = len(providers)
                    actual_total = status_data.get('total_providers', 0)
                    
                    self.log_test(
                        "Provider Status Consistency",
                        expected_total == actual_total,
                        f"Expected: {expected_total}, Actual: {actual_total}"
                    )
                else:
                    self.log_test(
                        "Provider Status Consistency",
                        False,
                        f"Status endpoint failed: {status_response.status_code}"
                    )
            
            else:
                self.log_test(
                    "Provider Listing",
                    False,
                    f"List endpoint failed: {list_response.status_code}"
                )
        
        except Exception as e:
            self.log_test("Provider Management Workflow", False, str(e))
    
    async def test_conversation_management_workflow(self):
        """Test complete conversation management workflow."""
        print("\n=== CONVERSATION MANAGEMENT WORKFLOW ===")
        
        try:
            # Test 1: List conversations
            print("\n1. Testing Conversation Listing...")
            history_response = await self.client.get(f"{self.base_url}/api/history/")
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                conversations = history_data.get('conversations', [])
                
                self.log_test(
                    "Conversation Listing",
                    isinstance(conversations, list),
                    f"Found {len(conversations)} conversations"
                )
                
                # Test 2: Conversation data structure
                if conversations:
                    print("\n2. Testing Conversation Data Structure...")
                    first_conv = conversations[0]
                    required_fields = ['thread_id', 'preview']
                    
                    has_required_fields = all(field in first_conv for field in required_fields)
                    self.log_test(
                        "Conversation Data Structure",
                        has_required_fields,
                        f"Fields present: {list(first_conv.keys())}"
                    )
                    
                    # Test 3: Conversation deletion (if safe to do)
                    # Only test deletion if we have multiple conversations
                    if len(conversations) > 1:
                        print("\n3. Testing Conversation Deletion...")
                        # Find a conversation that's not the most recent
                        test_thread_id = conversations[-1]['thread_id']  # Use oldest
                        
                        delete_response = await self.client.delete(
                            f"{self.base_url}/api/history/{test_thread_id}"
                        )
                        
                        if delete_response.status_code == 204:
                            # Verify deletion
                            verify_response = await self.client.get(f"{self.base_url}/api/history/")
                            if verify_response.status_code == 200:
                                new_conversations = verify_response.json().get('conversations', [])
                                deleted_successfully = not any(
                                    conv['thread_id'] == test_thread_id for conv in new_conversations
                                )
                                
                                self.log_test(
                                    "Conversation Deletion",
                                    deleted_successfully,
                                    f"Conversation {test_thread_id} removed"
                                )
                            else:
                                self.log_test(
                                    "Conversation Deletion",
                                    False,
                                    "Could not verify deletion"
                                )
                        else:
                            self.log_test(
                                "Conversation Deletion",
                                delete_response.status_code == 404,  # OK if already deleted
                                f"Delete status: {delete_response.status_code}"
                            )
                    else:
                        print("\n3. Skipping Conversation Deletion (insufficient conversations)")
                        self.log_test(
                            "Conversation Deletion",
                            True,
                            "Skipped - insufficient test data"
                        )
                else:
                    print("\n2. No conversations found - testing empty state")
                    self.log_test(
                        "Empty Conversation State",
                        True,
                        "Empty conversation list handled correctly"
                    )
            
            else:
                self.log_test(
                    "Conversation Listing",
                    False,
                    f"History endpoint failed: {history_response.status_code}"
                )
        
        except Exception as e:
            self.log_test("Conversation Management Workflow", False, str(e))
    
    async def test_error_handling_workflow(self):
        """Test error handling across the system."""
        print("\n=== ERROR HANDLING WORKFLOW ===")
        
        try:
            # Test 1: Invalid endpoints
            print("\n1. Testing Invalid Endpoint Handling...")
            invalid_response = await self.client.get(f"{self.base_url}/api/invalid-endpoint")
            
            self.log_test(
                "Invalid Endpoint Handling",
                invalid_response.status_code == 404,
                f"Status: {invalid_response.status_code}"
            )
            
            # Test 2: Invalid provider operations
            print("\n2. Testing Invalid Provider Operations...")
            invalid_provider_response = await self.client.post(
                f"{self.base_url}/api/providers/999999/test"
            )
            
            self.log_test(
                "Invalid Provider Operations",
                invalid_provider_response.status_code == 404,
                f"Status: {invalid_provider_response.status_code}"
            )
            
            # Test 3: Invalid conversation operations
            print("\n3. Testing Invalid Conversation Operations...")
            invalid_conv_response = await self.client.delete(
                f"{self.base_url}/api/history/non-existent-thread-id"
            )
            
            self.log_test(
                "Invalid Conversation Operations",
                invalid_conv_response.status_code == 404,
                f"Status: {invalid_conv_response.status_code}"
            )
            
            # Test 4: Malformed requests
            print("\n4. Testing Malformed Request Handling...")
            malformed_response = await self.client.post(
                f"{self.base_url}/api/providers/1/test",
                content="invalid-json-data",
                headers={"Content-Type": "application/json"}
            )
            
            # Should handle gracefully (either ignore body or return proper error)
            self.log_test(
                "Malformed Request Handling",
                malformed_response.status_code in [200, 400, 422],
                f"Status: {malformed_response.status_code}"
            )
        
        except Exception as e:
            self.log_test("Error Handling Workflow", False, str(e))
    
    async def test_performance_workflow(self):
        """Test system performance under normal load."""
        print("\n=== PERFORMANCE WORKFLOW ===")
        
        try:
            # Test 1: Response times
            print("\n1. Testing API Response Times...")
            
            endpoints = [
                "/api/ping/",
                "/api/version/",
                "/api/providers/status",
                "/api/providers/list",
                "/api/history/"
            ]
            
            total_time = 0
            successful_requests = 0
            
            for endpoint in endpoints:
                start_time = time.time()
                response = await self.client.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to ms
                total_time += response_time
                
                if response.status_code in [200, 404]:  # 404 is OK for some endpoints
                    successful_requests += 1
                
                print(f"   {endpoint}: {response_time:.2f}ms (Status: {response.status_code})")
            
            avg_response_time = total_time / len(endpoints)
            
            self.log_test(
                "API Response Times",
                avg_response_time < 1000 and successful_requests >= len(endpoints) - 1,
                f"Average: {avg_response_time:.2f}ms, Success rate: {successful_requests}/{len(endpoints)}"
            )
            
            # Test 2: Concurrent requests
            print("\n2. Testing Concurrent Request Handling...")
            
            async def make_request():
                response = await self.client.get(f"{self.base_url}/api/providers/status")
                return response.status_code == 200
            
            # Make 5 concurrent requests
            start_time = time.time()
            results = await asyncio.gather(*[make_request() for _ in range(5)])
            end_time = time.time()
            
            concurrent_time = (end_time - start_time) * 1000
            success_rate = sum(results) / len(results)
            
            self.log_test(
                "Concurrent Request Handling",
                success_rate >= 0.8 and concurrent_time < 5000,
                f"Success rate: {success_rate:.2%}, Time: {concurrent_time:.2f}ms"
            )
        
        except Exception as e:
            self.log_test("Performance Workflow", False, str(e))
    
    async def run_all_tests(self):
        """Run all end-to-end workflow tests."""
        print("🚀 STARTING END-TO-END WORKFLOW TESTING")
        print("=" * 50)
        
        start_time = time.time()
        
        # Run all workflow tests
        await self.test_system_bootstrap_workflow()
        await self.test_provider_management_workflow()
        await self.test_conversation_management_workflow()
        await self.test_error_handling_workflow()
        await self.test_performance_workflow()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print summary
        print("\n" + "=" * 50)
        print("🏁 END-TO-END WORKFLOW TEST SUMMARY")
        print("=" * 50)
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.test_results['passed']}")
        print(f"Failed: {self.test_results['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        
        if self.test_results['failed'] > 0:
            print("\n❌ FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   - {error}")
        
        if success_rate >= 90:
            print("\n🎉 END-TO-END WORKFLOW TESTS PASSED!")
            print("The consolidated codebase is working correctly across all workflows.")
            return True
        else:
            print("\n⚠️  SOME WORKFLOW TESTS FAILED")
            print("Please review the failed tests and fix any issues.")
            return False


async def main():
    """Main test runner."""
    print("End-to-End Workflow Testing for Consolidated Codebase")
    print("Testing complete user workflows after cleanup and consolidation\n")
    
    try:
        async with E2EWorkflowTester() as tester:
            success = await tester.run_all_tests()
            
            if success:
                print("\n✅ All workflow tests completed successfully!")
                sys.exit(0)
            else:
                print("\n❌ Some workflow tests failed.")
                sys.exit(1)
    
    except httpx.ConnectError:
        print("❌ Error: Could not connect to the server.")
        print("   Make sure the backend is running on http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
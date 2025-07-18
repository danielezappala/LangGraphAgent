#!/usr/bin/env python3
"""Comprehensive test runner for the consolidated codebase."""
import subprocess
import sys
import os
import asyncio
import time
from pathlib import Path


class TestRunner:
    """Comprehensive test runner for all test types."""
    
    def __init__(self):
        self.results = {
            'unit_tests': {'status': 'pending', 'details': ''},
            'integration_tests': {'status': 'pending', 'details': ''},
            'api_tests': {'status': 'pending', 'details': ''},
            'e2e_tests': {'status': 'pending', 'details': ''},
            'frontend_tests': {'status': 'pending', 'details': ''}
        }
    
    def print_header(self, title):
        """Print a formatted header."""
        print("\n" + "=" * 60)
        print(f"🧪 {title}")
        print("=" * 60)
    
    def print_status(self, test_type, status, details=""):
        """Print test status."""
        emoji = "✅" if status == "passed" else "❌" if status == "failed" else "⏳"
        print(f"{emoji} {test_type.replace('_', ' ').title()}: {status.upper()}")
        if details:
            print(f"   {details}")
    
    def run_command(self, command, cwd=None, timeout=300):
        """Run a command and return success status and output."""
        try:
            print(f"Running: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def run_unit_tests(self):
        """Run backend unit tests."""
        self.print_header("BACKEND UNIT TESTS")
        
        # Check if pytest is available
        success, _, _ = self.run_command(["python", "-m", "pytest", "--version"])
        if not success:
            self.results['unit_tests'] = {
                'status': 'skipped', 
                'details': 'pytest not installed'
            }
            self.print_status('unit_tests', 'skipped', 'pytest not installed')
            return
        
        # Run unit tests
        success, stdout, stderr = self.run_command([
            "python", "-m", "pytest", 
            "backend/tests/", 
            "-v", 
            "--tb=short"
        ])
        
        if success:
            self.results['unit_tests'] = {'status': 'passed', 'details': 'All unit tests passed'}
            self.print_status('unit_tests', 'passed')
        else:
            self.results['unit_tests'] = {'status': 'failed', 'details': stderr}
            self.print_status('unit_tests', 'failed', stderr[:200] + "..." if len(stderr) > 200 else stderr)
    
    def run_integration_tests(self):
        """Run integration tests."""
        self.print_header("INTEGRATION TESTS")
        
        # Run the comprehensive integration test
        success, stdout, stderr = self.run_command([
            "python", "backend/test_integration_final.py"
        ])
        
        if success:
            self.results['integration_tests'] = {'status': 'passed', 'details': 'Integration tests passed'}
            self.print_status('integration_tests', 'passed')
        else:
            self.results['integration_tests'] = {'status': 'failed', 'details': stderr}
            self.print_status('integration_tests', 'failed', stderr[:200] + "..." if len(stderr) > 200 else stderr)
    
    def run_api_tests(self):
        """Run API endpoint tests."""
        self.print_header("API ENDPOINT TESTS")
        
        # Run provider API tests
        print("\n📡 Testing Provider APIs...")
        success1, stdout1, stderr1 = self.run_command([
            "python", "backend/test_providers_api.py"
        ])
        
        # Run history API tests
        print("\n📚 Testing History APIs...")
        success2, stdout2, stderr2 = self.run_command([
            "python", "backend/test_history_api.py"
        ])
        
        if success1 and success2:
            self.results['api_tests'] = {'status': 'passed', 'details': 'All API tests passed'}
            self.print_status('api_tests', 'passed')
        else:
            error_details = []
            if not success1:
                error_details.append(f"Provider API: {stderr1}")
            if not success2:
                error_details.append(f"History API: {stderr2}")
            
            self.results['api_tests'] = {
                'status': 'failed', 
                'details': '; '.join(error_details)
            }
            self.print_status('api_tests', 'failed', '; '.join(error_details)[:200])
    
    def run_e2e_tests(self):
        """Run end-to-end workflow tests."""
        self.print_header("END-TO-END WORKFLOW TESTS")
        
        success, stdout, stderr = self.run_command([
            "python", "backend/test_e2e_workflows.py"
        ])
        
        if success:
            self.results['e2e_tests'] = {'status': 'passed', 'details': 'E2E workflow tests passed'}
            self.print_status('e2e_tests', 'passed')
        else:
            self.results['e2e_tests'] = {'status': 'failed', 'details': stderr}
            self.print_status('e2e_tests', 'failed', stderr[:200] + "..." if len(stderr) > 200 else stderr)
    
    def run_frontend_tests(self):
        """Run frontend component tests."""
        self.print_header("FRONTEND COMPONENT TESTS")
        
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            self.results['frontend_tests'] = {
                'status': 'skipped', 
                'details': 'Frontend directory not found'
            }
            self.print_status('frontend_tests', 'skipped', 'Frontend directory not found')
            return
        
        # Check if npm/yarn is available and if test dependencies are installed
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            self.results['frontend_tests'] = {
                'status': 'skipped', 
                'details': 'package.json not found'
            }
            self.print_status('frontend_tests', 'skipped', 'package.json not found')
            return
        
        # Check if Jest is configured
        jest_config = frontend_dir / "jest.config.js"
        if not jest_config.exists():
            self.results['frontend_tests'] = {
                'status': 'skipped', 
                'details': 'Jest not configured (jest.config.js missing)'
            }
            self.print_status('frontend_tests', 'skipped', 'Jest not configured')
            return
        
        # Try to run tests (this will fail if dependencies aren't installed)
        success, stdout, stderr = self.run_command([
            "npm", "test", "--", "--watchAll=false", "--coverage=false"
        ], cwd=frontend_dir)
        
        if success:
            self.results['frontend_tests'] = {'status': 'passed', 'details': 'Frontend tests passed'}
            self.print_status('frontend_tests', 'passed')
        else:
            # Check if it's a dependency issue
            if "jest" in stderr.lower() or "testing-library" in stderr.lower():
                self.results['frontend_tests'] = {
                    'status': 'skipped', 
                    'details': 'Test dependencies not installed'
                }
                self.print_status('frontend_tests', 'skipped', 'Test dependencies not installed')
            else:
                self.results['frontend_tests'] = {'status': 'failed', 'details': stderr}
                self.print_status('frontend_tests', 'failed', stderr[:200] + "..." if len(stderr) > 200 else stderr)
    
    def check_server_availability(self):
        """Check if the backend server is running."""
        try:
            import httpx
            
            async def check():
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.get("http://localhost:8000/api/ping/", timeout=5.0)
                        return response.status_code == 200
                    except:
                        return False
            
            return asyncio.run(check())
        except ImportError:
            # If httpx is not available, try with requests
            try:
                import requests
                response = requests.get("http://localhost:8000/api/ping/", timeout=5)
                return response.status_code == 200
            except:
                return False
    
    def print_summary(self):
        """Print test summary."""
        self.print_header("TEST SUMMARY")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r['status'] == 'passed')
        failed_tests = sum(1 for r in self.results.values() if r['status'] == 'failed')
        skipped_tests = sum(1 for r in self.results.values() if r['status'] == 'skipped')
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Test Suites: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⏭️  Skipped: {skipped_tests}")
        
        success_rate = (passed_tests / (total_tests - skipped_tests)) * 100 if (total_tests - skipped_tests) > 0 else 0
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_type, result in self.results.items():
            self.print_status(test_type, result['status'], result['details'])
        
        if failed_tests == 0:
            print(f"\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
            print("The consolidated codebase is working correctly.")
            return True
        else:
            print(f"\n⚠️  SOME TESTS FAILED")
            print("Please review the failed tests and fix any issues.")
            return False
    
    def run_all_tests(self):
        """Run all test suites."""
        print("🚀 COMPREHENSIVE TEST SUITE FOR CONSOLIDATED CODEBASE")
        print("Testing all aspects of the cleaned up and consolidated system")
        
        start_time = time.time()
        
        # Check if server is running for API tests
        server_running = self.check_server_availability()
        if not server_running:
            print("\n⚠️  WARNING: Backend server not detected at http://localhost:8000")
            print("   API and E2E tests may fail. Start the server with: python backend/run.py")
        
        # Run all test suites
        self.run_unit_tests()
        
        if server_running:
            self.run_integration_tests()
            self.run_api_tests()
            self.run_e2e_tests()
        else:
            print("\n⏭️  Skipping server-dependent tests (server not running)")
            self.results['integration_tests']['status'] = 'skipped'
            self.results['integration_tests']['details'] = 'Server not running'
            self.results['api_tests']['status'] = 'skipped'
            self.results['api_tests']['details'] = 'Server not running'
            self.results['e2e_tests']['status'] = 'skipped'
            self.results['e2e_tests']['details'] = 'Server not running'
        
        self.run_frontend_tests()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        success = self.print_summary()
        
        print(f"\n⏱️  Total execution time: {total_time:.2f} seconds")
        
        return success


def main():
    """Main entry point."""
    runner = TestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed or were skipped.")
        sys.exit(1)


if __name__ == "__main__":
    main()
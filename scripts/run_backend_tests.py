#!/usr/bin/env python3
"""
Test runner script for the backend test suite.
Provides easy commands to run different categories of tests.
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle the output."""
    print(f"\n🧪 {description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, cwd=Path(__file__).parent)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run backend tests")
    parser.add_argument(
        "test_type", 
        nargs="?", 
        choices=["unit", "integration", "performance", "all"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--file", "-f",
        help="Run a specific test file"
    )
    
    args = parser.parse_args()
    
    verbose_flag = "-v" if args.verbose else ""
    
    if args.file:
        # Run specific file
        cmd = f"python {args.file}"
        success = run_command(cmd, f"Running {args.file}")
    elif args.test_type == "unit":
        cmd = f"python -m pytest tests/unit/ {verbose_flag}"
        success = run_command(cmd, "Running Unit Tests")
    elif args.test_type == "integration":
        cmd = f"python -m pytest tests/integration/ {verbose_flag}"
        success = run_command(cmd, "Running Integration Tests")
    elif args.test_type == "performance":
        cmd = f"python -m pytest tests/performance/ {verbose_flag}"
        success = run_command(cmd, "Running Performance Tests")
    elif args.test_type == "all":
        print("🚀 Running Complete Test Suite")
        print("=" * 50)
        
        success = True
        
        # Run unit tests
        if success:
            success = run_command(f"python -m pytest tests/unit/ {verbose_flag}", "Unit Tests")
        
        # Run integration tests
        if success:
            success = run_command(f"python -m pytest tests/integration/ {verbose_flag}", "Integration Tests")
        
        # Run performance tests
        if success:
            success = run_command(f"python -m pytest tests/performance/ {verbose_flag}", "Performance Tests")
        
        if success:
            print("\n🎉 All tests passed successfully!")
        else:
            print("\n💥 Some tests failed. Check the output above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
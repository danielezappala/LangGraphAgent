#!/usr/bin/env python3
"""
Test script to verify server startup with unified database system.
This script tests the server startup process without actually starting the server.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from unified_database import get_unified_db, UnifiedAsyncSqliteSaver
from services.bootstrap_service import get_bootstrap_service
from services.provider_service import get_provider_service

async def test_server_startup_process():
    """Test the server startup process with unified database."""
    print("="*60)
    print("TESTING SERVER STARTUP WITH UNIFIED DATABASE")
    print("="*60)
    
    try:
        # Step 1: Initialize unified database system
        print("\n1. Initializing unified database system...")
        unified_db = get_unified_db()
        print(f"   ✓ Database path: {unified_db.db_path}")
        print(f"   ✓ Database URL: {unified_db.db_url}")
        
        # Step 2: Test database session
        print("\n2. Testing database session...")
        db = unified_db.get_session()
        
        try:
            # Step 3: Run bootstrap process
            print("\n3. Running bootstrap process...")
            bootstrap_service = get_bootstrap_service(db)
            bootstrap_result = bootstrap_service.run_bootstrap_if_needed()
            print(f"   ✓ Bootstrap result: {bootstrap_result}")
            
            # Step 4: Get active provider
            print("\n4. Getting active provider...")
            provider_service = get_provider_service(db)
            active_provider_config = provider_service.get_active_provider()
            
            if active_provider_config:
                print(f"   ✓ Active provider: {active_provider_config['name']} ({active_provider_config['provider_type']})")
            else:
                print("   ⚠ Warning: No active provider configured")
            
            # Step 5: Test provider status
            print("\n5. Testing provider status...")
            status = provider_service.get_provider_status()
            print(f"   ✓ Has active provider: {status.has_active_provider}")
            print(f"   ✓ Total providers: {status.total_providers}")
            print(f"   ✓ Configuration source: {status.configuration_source}")
            
        finally:
            db.close()
        
        # Step 6: Initialize unified checkpointer
        print("\n6. Initializing unified checkpointer...")
        checkpointer = UnifiedAsyncSqliteSaver(unified_db)
        print("   ✓ Unified checkpointer initialized")
        
        # Step 7: Test checkpointer functionality
        print("\n7. Testing checkpointer functionality...")
        test_config = {"configurable": {"thread_id": "startup-test-thread"}}
        test_checkpoint = {"test": "startup", "messages": []}
        test_metadata = {"test": True}
        
        await checkpointer.aput(test_config, test_checkpoint, test_metadata)
        result = await checkpointer.aget_tuple(test_config)
        
        if result and result[0].get("test") == "startup":
            print("   ✓ Checkpointer save/retrieve test passed")
        else:
            print("   ✗ Checkpointer test failed")
            return False
        
        # Step 8: Test database cleanup
        print("\n8. Testing database cleanup...")
        unified_db.close()
        print("   ✓ Database connections closed")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - SERVER STARTUP READY")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR DURING STARTUP TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = asyncio.run(test_server_startup_process())
    if success:
        print("\n🎉 Server startup test completed successfully!")
        print("The unified database system is ready for production use.")
        sys.exit(0)
    else:
        print("\n💥 Server startup test failed!")
        print("Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
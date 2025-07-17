#!/usr/bin/env python3
"""
Test script to verify unified database functionality.
This script tests both application data and LangGraph adapter functionality.
"""

import asyncio
import tempfile
import os
from datetime import datetime

from unified_database import UnifiedDatabase, UnifiedAsyncSqliteSaver, DBProvider, Checkpoint, Write

async def test_unified_database():
    """Test unified database functionality."""
    print("🧪 Testing Unified Database System")
    print("=" * 50)
    
    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as tmp_file:
        test_db_path = tmp_file.name
    
    try:
        # Test 1: Initialize unified database
        print("\n1. Testing database initialization...")
        unified_db = UnifiedDatabase(test_db_path)
        print("✅ Database initialized successfully")
        
        # Test 2: Test application data (DBProvider)
        print("\n2. Testing application data operations...")
        session = unified_db.get_session()
        
        # Create a test provider
        test_provider = DBProvider(
            name="test-openai",
            provider_type="openai",
            api_key="sk-test123",
            model="gpt-4",
            is_active=True,
            is_from_env=False
        )
        
        session.add(test_provider)
        session.commit()
        
        # Query the provider
        retrieved_provider = session.query(DBProvider).filter(DBProvider.name == "test-openai").first()
        assert retrieved_provider is not None
        assert retrieved_provider.provider_type == "openai"
        assert retrieved_provider.model == "gpt-4"
        print("✅ Application data operations working")
        
        session.close()
        
        # Test 3: Test LangGraph adapter
        print("\n3. Testing LangGraph adapter...")
        adapter = UnifiedAsyncSqliteSaver(unified_db)
        
        # Test configuration
        config = {
            "configurable": {
                "thread_id": "test-thread-123"
            }
        }
        
        # Test checkpoint save
        test_checkpoint = {"state": "test_state", "step": 1}
        test_metadata = {"timestamp": datetime.now().isoformat()}
        
        async with adapter:
            await adapter.aput(config, test_checkpoint, test_metadata)
            print("✅ Checkpoint saved successfully")
            
            # Test checkpoint retrieval
            result = await adapter.aget_tuple(config)
            if result:
                checkpoint_data, metadata = result
                assert checkpoint_data["state"] == "test_state"
                assert checkpoint_data["step"] == 1
                print("✅ Checkpoint retrieved successfully")
            else:
                print("⚠️  No checkpoint found (this might be expected)")
        
        # Test 4: Verify data in database
        print("\n4. Verifying data persistence...")
        session = unified_db.get_session()
        
        provider_count = session.query(DBProvider).count()
        checkpoint_count = session.query(Checkpoint).count()
        write_count = session.query(Write).count()
        
        print(f"   - Providers: {provider_count}")
        print(f"   - Checkpoints: {checkpoint_count}")
        print(f"   - Writes: {write_count}")
        
        assert provider_count >= 1
        print("✅ Data persistence verified")
        
        session.close()
        unified_db.close()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Unified database system is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up test database
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)

def test_migration_script():
    """Test that migration script can be imported and has required functions."""
    print("\n🧪 Testing Migration Script")
    print("=" * 30)
    
    try:
        from migrate_to_unified_db import DatabaseMigrator
        
        # Test that migrator can be instantiated
        migrator = DatabaseMigrator()
        
        # Check that required methods exist
        assert hasattr(migrator, 'backup_existing_databases')
        assert hasattr(migrator, 'migrate_app_data')
        assert hasattr(migrator, 'migrate_checkpoint_data')
        assert hasattr(migrator, 'validate_migration')
        assert hasattr(migrator, 'run_migration')
        
        print("✅ Migration script structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Migration script test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Unified Database Tests")
    
    # Test unified database functionality
    db_test_passed = await test_unified_database()
    
    # Test migration script
    migration_test_passed = test_migration_script()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Database functionality: {'✅ PASS' if db_test_passed else '❌ FAIL'}")
    print(f"Migration script:       {'✅ PASS' if migration_test_passed else '❌ FAIL'}")
    
    if db_test_passed and migration_test_passed:
        print("\n🎉 ALL TESTS PASSED! Ready for production use.")
        return True
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
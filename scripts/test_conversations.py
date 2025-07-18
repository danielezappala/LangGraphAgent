#!/usr/bin/env python3
"""
Script per testare il caricamento delle conversazioni dal database.
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

async def test_conversations():
    """Test che le conversazioni si caricano correttamente."""
    print("🗨️ Testing conversation loading...")
    
    try:
        from core.database.unified_database import get_unified_db, UnifiedAsyncSqliteSaver
        
        # Get database
        db = get_unified_db()
        print(f"✅ Database connected: {db.db_path}")
        
        # Test checkpoints count
        with db.get_session() as session:
            from core.database.unified_database import Checkpoint
            checkpoints_count = session.query(Checkpoint).count()
            print(f"✅ Found {checkpoints_count} checkpoints in database")
            
            # Get some sample thread IDs
            sample_threads = session.query(Checkpoint.thread_id).distinct().limit(5).all()
            thread_ids = [t[0] for t in sample_threads]
            print(f"✅ Sample thread IDs: {thread_ids[:3]}...")
        
        # Test LangGraph adapter
        saver = UnifiedAsyncSqliteSaver(db)
        print("✅ LangGraph adapter created successfully")
        
        # Test async context manager
        async with saver:
            print("✅ LangGraph saver context manager works")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run conversation tests."""
    print("🔍 Testing conversation loading after reorganization...")
    print("=" * 50)
    
    success = await test_conversations()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Conversation loading test passed!")
        print("✅ Conversations should load correctly in the application.")
    else:
        print("💥 Conversation loading test failed.")
        print("❌ Check the errors above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
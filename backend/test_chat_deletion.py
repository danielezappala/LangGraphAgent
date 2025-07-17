#!/usr/bin/env python3
"""Test script for chat deletion functionality."""
import asyncio
import aiosqlite
import pathlib

DB_PATH = str(pathlib.Path(__file__).parent / "data" / "chatbot_memory.sqlite")

async def test_chat_deletion():
    """Test chat deletion functionality."""
    print(f"Testing chat deletion with database: {DB_PATH}")
    
    try:
        # First, let's see what tables exist
        async with aiosqlite.connect(DB_PATH) as conn:
            print("\n=== Database Tables ===")
            cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = await cursor.fetchall()
            for table in tables:
                print(f"Table: {table[0]}")
            
            # Check if we have any conversations
            print("\n=== Current Conversations ===")
            try:
                cursor = await conn.execute("SELECT DISTINCT thread_id FROM checkpoints LIMIT 5;")
                threads = await cursor.fetchall()
                if threads:
                    print(f"Found {len(threads)} conversation threads:")
                    for thread in threads:
                        print(f"  - {thread[0]}")
                        
                    # Try to delete the first thread as a test
                    test_thread_id = threads[0][0]
                    print(f"\n=== Testing Deletion of Thread: {test_thread_id} ===")
                    
                    # Count records before deletion
                    cursor = await conn.execute("SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?", (test_thread_id,))
                    checkpoints_before = (await cursor.fetchone())[0]
                    
                    cursor = await conn.execute("SELECT COUNT(*) FROM writes WHERE thread_id = ?", (test_thread_id,))
                    writes_before = (await cursor.fetchone())[0]
                    
                    print(f"Before deletion: {checkpoints_before} checkpoints, {writes_before} writes")
                    
                    # Perform deletion
                    cursor = await conn.execute("DELETE FROM writes WHERE thread_id = ?", (test_thread_id,))
                    deleted_writes = cursor.rowcount
                    
                    cursor = await conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (test_thread_id,))
                    deleted_checkpoints = cursor.rowcount
                    
                    await conn.commit()
                    
                    print(f"Deletion result: {deleted_checkpoints} checkpoints deleted, {deleted_writes} writes deleted")
                    
                    if deleted_checkpoints > 0 or deleted_writes > 0:
                        print("✅ Chat deletion test PASSED")
                    else:
                        print("❌ Chat deletion test FAILED - no records were deleted")
                        
                else:
                    print("No conversation threads found in database")
                    
            except Exception as e:
                print(f"Error checking conversations: {e}")
                
    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_deletion())
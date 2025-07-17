#!/usr/bin/env python3
"""Debug script to check the history database for thread_id issues."""
import asyncio
import aiosqlite
import pathlib

DB_PATH = str(pathlib.Path(__file__).parent / "data" / "chatbot_memory.sqlite")

async def debug_history_database():
    """Debug the history database to find thread_id issues."""
    print("=== DEBUGGING HISTORY DATABASE ===\n")
    
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            # Check the structure of the checkpoints table
            print("1. Checking checkpoints table structure...")
            cursor = await conn.execute("PRAGMA table_info(checkpoints)")
            columns = await cursor.fetchall()
            print("   Columns:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
            # Check all thread_ids in the database
            print("\n2. Checking all thread_ids...")
            cursor = await conn.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id")
            thread_ids = await cursor.fetchall()
            print(f"   Found {len(thread_ids)} unique thread_ids:")
            for i, (thread_id,) in enumerate(thread_ids):
                print(f"   {i+1}. '{thread_id}' (length: {len(thread_id) if thread_id else 0})")
                if not thread_id or thread_id.strip() == '':
                    print(f"      ⚠️  EMPTY OR NULL THREAD_ID FOUND!")
            
            # Check the latest checkpoint_ns for each thread_id
            print("\n3. Checking latest checkpoint_ns for each thread_id...")
            cursor = await conn.execute("""
                SELECT thread_id, MAX(checkpoint_ns) as last_checkpoint_ns, COUNT(*) as checkpoint_count
                FROM checkpoints
                GROUP BY thread_id
                ORDER BY last_checkpoint_ns DESC
            """)
            thread_info = await cursor.fetchall()
            
            for thread_id, last_ns, count in thread_info:
                print(f"   Thread: '{thread_id}' | Last NS: {last_ns} | Checkpoints: {count}")
                if not thread_id or thread_id.strip() == '':
                    print(f"      ⚠️  THIS IS THE PROBLEMATIC THREAD!")
            
            # Check if there are any checkpoints with empty thread_id
            print("\n4. Checking for empty thread_ids...")
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM checkpoints 
                WHERE thread_id IS NULL OR thread_id = '' OR TRIM(thread_id) = ''
            """)
            empty_count = (await cursor.fetchone())[0]
            print(f"   Found {empty_count} checkpoints with empty/null thread_id")
            
            if empty_count > 0:
                print("\n5. Sample of problematic checkpoints...")
                cursor = await conn.execute("""
                    SELECT thread_id, checkpoint_ns, checkpoint_id
                    FROM checkpoints 
                    WHERE thread_id IS NULL OR thread_id = '' OR TRIM(thread_id) = ''
                    LIMIT 5
                """)
                problematic = await cursor.fetchall()
                for thread_id, ns, checkpoint_id in problematic:
                    print(f"   Thread: '{thread_id}' | NS: {ns} | ID: {checkpoint_id}")
            
            # Check writes table as well
            print("\n6. Checking writes table...")
            cursor = await conn.execute("SELECT COUNT(*) FROM writes")
            writes_count = (await cursor.fetchone())[0]
            print(f"   Total writes: {writes_count}")
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM writes 
                WHERE thread_id IS NULL OR thread_id = '' OR TRIM(thread_id) = ''
            """)
            empty_writes = (await cursor.fetchone())[0]
            print(f"   Writes with empty thread_id: {empty_writes}")
            
    except Exception as e:
        print(f"❌ Error debugging database: {e}")

if __name__ == "__main__":
    asyncio.run(debug_history_database())
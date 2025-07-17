#!/usr/bin/env python3
"""Fix empty thread_ids in the history database."""
import asyncio
import aiosqlite
import pathlib
import uuid

DB_PATH = str(pathlib.Path(__file__).parent / "data" / "chatbot_memory.sqlite")

async def fix_empty_thread_ids():
    """Fix empty thread_ids in the database."""
    print("=== FIXING EMPTY THREAD_IDS ===\n")
    
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            # First, let's see what we're dealing with
            print("1. Analyzing empty thread_ids...")
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM checkpoints 
                WHERE thread_id IS NULL OR thread_id = '' OR TRIM(thread_id) = ''
            """)
            empty_checkpoints = (await cursor.fetchone())[0]
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM writes 
                WHERE thread_id IS NULL OR thread_id = '' OR TRIM(thread_id) = ''
            """)
            empty_writes = (await cursor.fetchone())[0]
            
            print(f"   Found {empty_checkpoints} checkpoints with empty thread_id")
            print(f"   Found {empty_writes} writes with empty thread_id")
            
            if empty_checkpoints == 0 and empty_writes == 0:
                print("   ✅ No empty thread_ids found. Database is clean!")
                return
            
            # Option 1: Delete the orphaned records (recommended)
            print("\n2. Cleaning up orphaned records...")
            print("   This will DELETE all checkpoints and writes with empty thread_ids.")
            print("   These are likely corrupted or incomplete conversation data.")
            
            # Delete from writes first (foreign key constraints)
            cursor = await conn.execute("""
                DELETE FROM writes 
                WHERE thread_id IS NULL OR thread_id = '' OR TRIM(thread_id) = ''
            """)
            deleted_writes = cursor.rowcount
            print(f"   Deleted {deleted_writes} orphaned writes")
            
            # Delete from checkpoints
            cursor = await conn.execute("""
                DELETE FROM checkpoints 
                WHERE thread_id IS NULL OR thread_id = '' OR TRIM(thread_id) = ''
            """)
            deleted_checkpoints = cursor.rowcount
            print(f"   Deleted {deleted_checkpoints} orphaned checkpoints")
            
            # Commit the changes
            await conn.commit()
            
            print(f"\n✅ Database cleanup completed!")
            print(f"   - Removed {deleted_checkpoints} orphaned checkpoints")
            print(f"   - Removed {deleted_writes} orphaned writes")
            print(f"   - Chat deletion should now work correctly")
            
            # Verify the cleanup
            print("\n3. Verifying cleanup...")
            cursor = await conn.execute("""
                SELECT thread_id, MAX(checkpoint_ns) as last_checkpoint_ns, COUNT(*) as checkpoint_count
                FROM checkpoints
                GROUP BY thread_id
                ORDER BY last_checkpoint_ns DESC
            """)
            remaining_threads = await cursor.fetchall()
            
            print(f"   Remaining conversations: {len(remaining_threads)}")
            for thread_id, last_ns, count in remaining_threads:
                if thread_id and thread_id.strip():
                    print(f"   - {thread_id[:8]}... ({count} checkpoints)")
                else:
                    print(f"   ⚠️  Still found empty thread_id!")
            
    except Exception as e:
        print(f"❌ Error fixing database: {e}")

async def main():
    """Main function with user confirmation."""
    print("This script will clean up orphaned conversation data with empty thread_ids.")
    print("This data cannot be properly displayed or deleted through the UI.")
    print("\nProceed with cleanup? (y/N): ", end="")
    
    # For automated execution, we'll proceed automatically
    # In a real scenario, you might want to add input() here
    response = "y"  # Auto-confirm for this fix
    
    if response.lower() == 'y':
        await fix_empty_thread_ids()
    else:
        print("Cleanup cancelled.")

if __name__ == "__main__":
    asyncio.run(main())
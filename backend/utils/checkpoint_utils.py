"""
Utility functions for working with LangGraph checkpoints in the database.
"""
import os
import pickle
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Path to the SQLite database
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    "data", 
    "chatbot_memory.sqlite"
)

@dataclass
class CheckpointInfo:
    """Represents a single checkpoint in the database."""
    thread_id: str
    checkpoint_id: str
    checkpoint_data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime
    size_bytes: int

    @property
    def message_count(self) -> int:
        """Returns the number of messages in this checkpoint."""
        try:
            messages = self.checkpoint_data.get("channel_values", {}).get("messages", [])
            return len(messages)
        except Exception:
            return 0

    @property
    def last_message_preview(self) -> str:
        """Returns a preview of the last message in the checkpoint."""
        try:
            messages = self.checkpoint_data.get("channel_values", {}).get("messages", [])
            if not messages:
                return "No messages"
            last_msg = messages[-1]
            if hasattr(last_msg, 'content'):
                content = last_msg.content
            elif isinstance(last_msg, dict):
                content = last_msg.get('content', '')
            else:
                content = str(last_msg)
            return (content[:100] + '...') if len(content) > 100 else content
        except Exception as e:
            return f"Error getting message preview: {str(e)}"

def get_all_checkpoints(limit: int = 10) -> List[CheckpointInfo]:
    """
    Retrieves all checkpoints from the database.
    
    Args:
        limit: Maximum number of checkpoints to return
        
    Returns:
        List of CheckpointInfo objects
    """
    checkpoints = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get basic checkpoint info
        cursor.execute("""
            SELECT thread_id, checkpoint_id, checkpoint, metadata, 
                   length(checkpoint) as size
            FROM checkpoints
            ORDER BY checkpoint_id DESC
            LIMIT ?
        """, (limit,))
        
        for row in cursor.fetchall():
            thread_id, checkpoint_id, checkpoint_blob, metadata_blob, size = row
            
            try:
                # Deserialize the checkpoint data
                checkpoint_data = pickle.loads(checkpoint_blob)
                
                # Deserialize metadata if present
                metadata = {}
                if metadata_blob:
                    try:
                        metadata = pickle.loads(metadata_blob)
                    except Exception:
                        metadata = {"error": "Failed to deserialize metadata"}
                
                # Get timestamp from checkpoint_id if possible
                try:
                    # Assuming checkpoint_id contains a timestamp
                    timestamp = datetime.fromtimestamp(int(checkpoint_id) / 1000)
                except (ValueError, TypeError):
                    timestamp = datetime.now()
                
                checkpoints.append(CheckpointInfo(
                    thread_id=thread_id,
                    checkpoint_id=checkpoint_id,
                    checkpoint_data=checkpoint_data,
                    metadata=metadata,
                    timestamp=timestamp,
                    size_bytes=size
                ))
                
            except Exception as e:
                print(f"Error deserializing checkpoint {checkpoint_id}: {str(e)}")
                continue
                
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    finally:
        conn.close()
    
    return checkpoints

def get_checkpoints_for_thread(thread_id: str) -> List[CheckpointInfo]:
    """
    Retrieves all checkpoints for a specific thread.
    
    Args:
        thread_id: The thread ID to get checkpoints for
        
    Returns:
        List of CheckpointInfo objects for the specified thread
    """
    checkpoints = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT thread_id, checkpoint_id, checkpoint, metadata, 
                   length(checkpoint) as size
            FROM checkpoints
            WHERE thread_id = ?
            ORDER BY checkpoint_id ASC  # Oldest first
        """, (thread_id,))
        
        for row in cursor.fetchall():
            thread_id, checkpoint_id, checkpoint_blob, metadata_blob, size = row
            
            try:
                checkpoint_data = pickle.loads(checkpoint_blob)
                metadata = {}
                if metadata_blob:
                    try:
                        metadata = pickle.loads(metadata_blob)
                    except Exception:
                        metadata = {"error": "Failed to deserialize metadata"}
                
                try:
                    timestamp = datetime.fromtimestamp(int(checkpoint_id) / 1000)
                except (ValueError, TypeError):
                    timestamp = datetime.now()
                
                checkpoints.append(CheckpointInfo(
                    thread_id=thread_id,
                    checkpoint_id=checkpoint_id,
                    checkpoint_data=checkpoint_data,
                    metadata=metadata,
                    timestamp=timestamp,
                    size_bytes=size
                ))
                
            except Exception as e:
                print(f"Error deserializing checkpoint {checkpoint_id}: {str(e)}")
                continue
                
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    finally:
        conn.close()
    
    return checkpoints

def get_checkpoint_summary() -> Dict[str, Any]:
    """
    Returns a summary of checkpoints in the database.
    
    Returns:
        Dictionary containing summary information
    """
    summary = {
        "total_checkpoints": 0,
        "threads": {},
        "total_size_mb": 0,
        "checkpoints_per_thread": {},
        "largest_checkpoint": {"size": 0, "thread_id": None, "checkpoint_id": None}
    }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get total number of checkpoints
        cursor.execute("SELECT COUNT(*) FROM checkpoints")
        summary["total_checkpoints"] = cursor.fetchone()[0]
        
        # Get total size in MB
        cursor.execute("SELECT SUM(length(checkpoint)) FROM checkpoints")
        total_bytes = cursor.fetchone()[0] or 0
        summary["total_size_mb"] = round(total_bytes / (1024 * 1024), 2)
        
        # Get checkpoints per thread
        cursor.execute("""
            SELECT thread_id, COUNT(*) as count, 
                   SUM(length(checkpoint)) as total_size
            FROM checkpoints
            GROUP BY thread_id
            ORDER BY count DESC
        """)
        
        for thread_id, count, size in cursor.fetchall():
            summary["checkpoints_per_thread"][thread_id] = {
                "count": count,
                "size_mb": round(size / (1024 * 1024), 2)
            }
        
        # Get largest checkpoint
        cursor.execute("""
            SELECT thread_id, checkpoint_id, length(checkpoint) as size
            FROM checkpoints
            ORDER BY size DESC
            LIMIT 1
        """)
        
        largest = cursor.fetchone()
        if largest:
            summary["largest_checkpoint"] = {
                "size": largest[2],
                "thread_id": largest[0],
                "checkpoint_id": largest[1]
            }
        
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    finally:
        conn.close()
    
    return summary

def print_checkpoint_summary():
    """Prints a summary of checkpoints to the console."""
    summary = get_checkpoint_summary()
    
    print("\n=== Checkpoint Database Summary ===")
    print(f"Total checkpoints: {summary['total_checkpoints']}")
    print(f"Total size: {summary['total_size_mb']} MB")
    
    if summary['checkpoints_per_thread']:
        print("\nCheckpoints per thread:")
        for thread_id, data in summary['checkpoints_per_thread'].items():
            print(f"  - {thread_id}: {data['count']} checkpoints ({data['size_mb']} MB)")
    
    largest = summary['largest_checkpoint']
    if largest['thread_id']:
        print(f"\nLargest checkpoint: {largest['size']} bytes in thread {largest['thread_id']}")
    
    print("=" * 34 + "\n")

# Example usage
if __name__ == "__main__":
    print("Checkpoint Database Inspector")
    print("-" * 30)
    
    # Print summary
    print_checkpoint_summary()
    
    # Get all checkpoints (limited to 5 for demo)
    print("\nRecent checkpoints:")
    checkpoints = get_all_checkpoints(limit=5)
    
    for i, cp in enumerate(checkpoints, 1):
        print(f"\n{i}. Thread: {cp.thread_id}")
        print(f"   Timestamp: {cp.timestamp}")
        print(f"   Size: {cp.size_bytes} bytes")
        print(f"   Messages: {cp.message_count}")
        print(f"   Last message: {cp.last_message_preview}")
    
    print("\nInspection complete.")

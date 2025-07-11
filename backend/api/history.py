"""
API endpoints for chat history management, compatible with LangGraph's AsyncSqliteSaver.
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# --- Configuration ---
import pathlib

# --- Configuration ---
# Costruisce un percorso assoluto per il database per garantire l'affidabilità.
DB_PATH = str(pathlib.Path(__file__).parent.parent / "data" / "chatbot_memory.sqlite")
# logging.basicConfig(level=logging.INFO) # Uvicorn's logger will handle basicConfig
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Explicitly set this logger to DEBUG

# --- Pydantic Models ---
class Message(BaseModel):
    type: str
    content: str

class Conversation(BaseModel):
    thread_id: str
    last_message_ts: Optional[str] = None
    preview: str

class ConversationListResponse(BaseModel):
    conversations: List[Conversation]

class ConversationDetailResponse(BaseModel):
    messages: List[Message]

# --- Router Setup ---
router = APIRouter(prefix="/history", tags=["history"])

# --- Helper Functions ---
def get_last_human_message_preview(checkpoint: Dict[str, Any]) -> str:
    """Extracts a preview from the last human message in a checkpoint."""
    logger.debug(f"get_last_human_message_preview: Received checkpoint type: {type(checkpoint)}")
    if not checkpoint:
        logger.debug("get_last_human_message_preview: Checkpoint is None or empty.")
        return "No checkpoint data"

    channel_values = checkpoint.get('channel_values')
    if not channel_values:
        logger.debug(f"get_last_human_message_preview: 'channel_values' not found in checkpoint. Keys: {list(checkpoint.keys())}")
        return "No channel values"

    messages = channel_values.get('messages', [])
    if not messages:
        logger.debug("get_last_human_message_preview: 'messages' is empty or not found in channel_values.")
        return "No messages in channel"
    
    logger.debug(f"get_last_human_message_preview: Raw messages list (first 3): {messages[:3]}")

    human_messages = []
    for msg in reversed(messages):
        # LangChain messages can be BaseMessage objects or dicts after serialization/deserialization
        if hasattr(msg, 'type') and getattr(msg, 'type') == 'human': # Handles Pydantic model like objects
             if hasattr(msg, 'content'):
                human_messages.append(msg)
        elif isinstance(msg, dict) and msg.get('type') == 'human': # Handles plain dicts
            human_messages.append(msg)
        elif isinstance(msg, dict) and msg.get('lc_id'): # Check for LangChain's serialization structure
            # Example: {'lc': 1, 'type': 'constructor', 'id': ['langchain', 'schema', 'messages', 'HumanMessage'], 'kwargs': {'content': 'Hi', 'additional_kwargs': {}, 'response_metadata': {}, 'name': None, 'id': None, 'example': False}}
            if msg.get('id') and isinstance(msg['id'], list) and "HumanMessage" in msg['id'][-1]:
                if 'kwargs' in msg and 'content' in msg['kwargs']:
                    # Reconstruct a temporary message structure for preview
                    human_messages.append({'type': 'human', 'content': msg['kwargs']['content']})


    logger.debug(f"get_last_human_message_preview: Filtered human_messages (first 3): {human_messages[:3]}")
    
    if human_messages:
        # Ensure content is a string
        content = getattr(human_messages[0], 'content', None) if hasattr(human_messages[0], 'content') else human_messages[0].get('content', '')
        if not isinstance(content, str):
            content = str(content) # Convert to string if it's not, e.g. if it's some other object by mistake
        logger.debug(f"get_last_human_message_preview: Extracted content for preview: '{content}'")
        return content[:75] + '...' if len(content) > 75 else content
    
    logger.debug("get_last_human_message_preview: No human messages found after filtering.")
    return "No human messages yet"

# --- API Endpoints ---
@router.get("", response_model=ConversationListResponse, include_in_schema=False)
@router.get("/", response_model=ConversationListResponse)
async def list_conversations():
    """Restituisce la lista di tutte le conversazioni con i loro metadati."""
    logger.info("Listing all conversations")
    conversations_data = []
    try:
        # 1. Get all thread_ids and their latest checkpoint_ns (which is used as the timestamp)
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as conn:
            # Query to get the latest checkpoint_ns for each thread_id
            cursor = await conn.execute("""
                SELECT thread_id, MAX(checkpoint_ns) as last_checkpoint_ns
                FROM checkpoints
                GROUP BY thread_id
                ORDER BY last_checkpoint_ns DESC
            """)
            rows = await cursor.fetchall()
            if not rows:
                logger.info("Nessuna conversazione trovata nel database.")
                return ConversationListResponse(conversations=[])
            # Store as a list of tuples (thread_id, last_checkpoint_ns)
            thread_info_list = [(row[0], row[1]) for row in rows]

        # 2. For each thread, get the checkpoint content for preview
        async with AsyncSqliteSaver.from_conn_string(DB_PATH) as checkpointer:
            for thread_id, last_checkpoint_ns in thread_info_list:
                try:
                    # Config to get the specific latest checkpoint (though aget_tuple defaults to latest if ns isn't specified)
                    # For clarity and to be sure, we could specify checkpoint_ns, but it might be redundant
                    # if aget_tuple already correctly fetches the one with MAX(checkpoint_ns) by default.
                    # Let's rely on aget_tuple's default behavior of getting the latest for the thread_id.
                    config = {"configurable": {"thread_id": thread_id}} 
                    checkpoint_tuple = await checkpointer.aget_tuple(config)

                    if not checkpoint_tuple or not checkpoint_tuple.checkpoint:
                        logger.warning(f"No valid checkpoint content found for thread_id: {thread_id} (ts: {last_checkpoint_ns}) when listing.")
                        preview = "No content available"
                    else:
                        checkpoint_data = checkpoint_tuple.checkpoint
                        preview = get_last_human_message_preview(checkpoint_data)
                    
                    # Log the raw timestamp value before sending
                    logger.debug(f"list_conversations: For thread_id {thread_id}, raw last_checkpoint_ns: {last_checkpoint_ns}, type: {type(last_checkpoint_ns)}")
                    
                    ts_to_send = str(last_checkpoint_ns) if last_checkpoint_ns else None

                    conversations_data.append(
                        Conversation(
                            thread_id=thread_id,
                            last_message_ts=ts_to_send, # Use the queried MAX(checkpoint_ns) or None
                            preview=preview
                        )
                    )
                except Exception as e:
                    logger.error(f"Error processing checkpoint content for thread_id {thread_id} (ts: {last_checkpoint_ns}): {e}", exc_info=True)
                    ts_to_send_on_error = str(last_checkpoint_ns) if last_checkpoint_ns else None
                    conversations_data.append(
                        Conversation(
                            thread_id=thread_id,
                            last_message_ts=ts_to_send_on_error, # Still send the timestamp (or None)
                            preview="Error loading preview"
                        )
                    )
            
            return ConversationListResponse(conversations=conversations_data)
            
    except Exception as e:
        logger.error(f"Unexpected error in list_conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {e}")


@router.delete("/{thread_id}", status_code=204)
async def delete_conversation(thread_id: str):
    """
    Deletes all checkpoints and associated writes for a specific conversation thread.
    """
    logger.info(f"Attempting to delete conversation with thread_id: {thread_id}")
    try:
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as conn:
            # First, delete from 'writes' table if it cascade deletes aren't set up,
            # or if we want to be explicit.
            # Based on the schema, 'writes' is linked by (thread_id, checkpoint_ns, checkpoint_id)
            # We need to delete all writes for a given thread_id.
            cursor = await conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
            deleted_writes_count = cursor.rowcount
            logger.info(f"Deleted {deleted_writes_count} rows from 'writes' table for thread_id: {thread_id}")

            # Then, delete from 'checkpoints' table
            cursor = await conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            deleted_checkpoints_count = cursor.rowcount
            logger.info(f"Deleted {deleted_checkpoints_count} rows from 'checkpoints' table for thread_id: {thread_id}")
            
            await conn.commit()

            if deleted_checkpoints_count == 0 and deleted_writes_count == 0:
                # Nothing was deleted, which could mean the thread_id didn't exist.
                # Return 404, as per common REST practice for DELETE on non-existent resource.
                logger.warning(f"No checkpoints or writes found to delete for thread_id: {thread_id}. Returning 404.")
                raise HTTPException(status_code=404, detail="Conversation thread not found.")
            
            logger.info(f"Successfully deleted conversation for thread_id: {thread_id}")
            # Return 204 No Content implicitly by FastAPI due to status_code=204

    except HTTPException as http_exc: # Re-raise HTTPException
        raise http_exc
    except Exception as e:
        logger.error(f"Error deleting conversation for thread_id {thread_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {e}")


@router.get("/{thread_id}", response_model=ConversationDetailResponse)
async def get_conversation_detail(thread_id: str):
    """
    Fetches the full message history for a specific conversation thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        async with AsyncSqliteSaver.from_conn_string(DB_PATH) as checkpointer:
            checkpoint_tuple = await checkpointer.aget_tuple(config)
            if not checkpoint_tuple or not checkpoint_tuple.checkpoint:
                logger.warning(f"No valid checkpoint found for thread_id: {thread_id}")
                return ConversationDetailResponse(messages=[])

            logger.info(f"Checkpoint found for thread_id: {thread_id}, type: {type(checkpoint_tuple.checkpoint)}")
            messages_data = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
            logger.info(f"Extracted messages_data for thread_id {thread_id}: {messages_data}")
            
            processed_messages = []
            for msg in messages_data:
                if hasattr(msg, 'dict'):
                    processed_messages.append(msg.dict())
                elif isinstance(msg, dict):
                    processed_messages.append(msg)

            return ConversationDetailResponse(messages=processed_messages)
    except Exception as e:
        logger.error(f"Error fetching details for thread_id {thread_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation details.")


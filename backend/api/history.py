"""
API endpoints for chat history management, compatible with LangGraph's AsyncSqliteSaver.
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# --- Configuration ---
import pathlib

# --- Configuration ---
# Costruisce un percorso assoluto per il database per garantire l'affidabilità.
DB_PATH = str(pathlib.Path(__file__).parent.parent / "data" / "chatbot_memory.sqlite")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Models ---
class Message(BaseModel):
    type: str
    content: str

class Conversation(BaseModel):
    thread_id: str
    last_message_ts: str
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
    if not checkpoint or 'channel_values' not in checkpoint:
        return "No messages found"
    
    messages = checkpoint.get('channel_values', {}).get('messages', [])
    human_messages = [m for m in reversed(messages) if isinstance(m, dict) and m.get('type') == 'human']
    
    if human_messages:
        content = human_messages[0].get('content', '')
        return content[:75] + '...' if len(content) > 75 else content
    
    return "No human messages yet"

# --- API Endpoints ---
@router.get("", response_model=ConversationListResponse, include_in_schema=False)
@router.get("/", response_model=ConversationListResponse)
async def list_conversations():
    """Restituisce la lista di tutte le conversazioni con i loro metadati."""
    logger.info("Listing all conversations")
    try:
        # Usa una connessione SQL diretta per ottenere la lista delle conversazioni
        import aiosqlite
        import json
        
        async with aiosqlite.connect(DB_PATH) as conn:
            # Prima esaminiamo lo schema della tabella per debug
            cursor = await conn.execute("PRAGMA table_info(checkpoints)")
            rows = await cursor.fetchall()
            columns = [row[1] for row in rows]
            logger.info(f"Colonne disponibili nella tabella checkpoints: {columns}")
            
            # Query semplificata per ottenere l'ultimo checkpoint per ogni thread
            # Usiamo thread_id per il raggruppamento e il timestamp per l'ordinamento
            cursor = await conn.execute("""
                SELECT thread_id, checkpoint
                FROM checkpoints
                WHERE (thread_id, checkpoint_ns) IN (
                    SELECT thread_id, MAX(checkpoint_ns) as max_ns
                    FROM checkpoints
                    GROUP BY thread_id
                )
                ORDER BY checkpoint_ns DESC
            """)
            rows = await cursor.fetchall()
            if not rows:
                logger.info("Nessuna conversazione trovata nel database.")
                return ConversationListResponse(conversations=[])
            
            conversations = []
            for row in rows:
                thread_id = row[0]
                try:
                    # Decodifica il checkpoint (che è un BLOB JSON)
                    checkpoint = json.loads(row[1])
                    
                    # Estrai l'anteprima del messaggio
                    preview = 'No messages yet'
                    if 'messages' in checkpoint and checkpoint['messages']:
                        first_msg = checkpoint['messages'][0]
                        if isinstance(first_msg, dict) and 'content' in first_msg:
                            preview = first_msg['content'][:50] + '...'
                        else:
                            preview = str(first_msg)[:50] + '...'
                    
                    # Usa l'ID del thread come timestamp
                    last_message_ts = str(thread_id)
                    
                    conversations.append({
                        'thread_id': thread_id,
                        'last_message_ts': last_message_ts,
                        'preview': preview
                    })
                except Exception as e:
                    logger.error(f"Error processing checkpoint {thread_id}: {e}")
                    continue
            
            # Converti i dizionari in oggetti Conversation
            conversation_objects = [
                Conversation(
                    thread_id=conv['thread_id'],
                    last_message_ts=conv['last_message_ts'],
                    preview=conv.get('preview', 'No preview available')
                )
                for conv in conversations
            ]
            
            return ConversationListResponse(conversations=conversation_objects)
            
    except Exception as e:
        logger.error(f"Unexpected error in list_conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {e}")

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

            messages_data = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
            
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


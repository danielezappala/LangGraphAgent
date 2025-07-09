"""
API endpoints for chat history management.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import sqlite3
import os
from datetime import datetime, timezone

router = APIRouter(prefix="/api/history", tags=["history"])

# Modelli Pydantic per le richieste/risposte
class HistoryMessage(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime

class HistoryResponse(BaseModel):
    conversation_id: str
    messages: List[HistoryMessage]

# Funzione per ottenere la connessione al database
def get_db_connection():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chatbot_memory.sqlite")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Endpoint per ottenere la cronologia di una conversazione
@router.get("/{conversation_id}", response_model=HistoryResponse)
async def get_conversation_history(conversation_id: str):
    """
    Recupera la cronologia di una specifica conversazione.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verifica se la conversazione esiste
        cursor.execute(
            "SELECT * FROM conversations WHERE id = ?", 
            (conversation_id,)
        )
        conversation = cursor.fetchone()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Recupera i messaggi della conversazione
        cursor.execute(
            """
            SELECT id, role, content, timestamp 
            FROM messages 
            WHERE conversation_id = ? 
            ORDER BY timestamp ASC
            """,
            (conversation_id,)
        )
        
        messages = [
            {
                "id": msg["id"],
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": datetime.fromisoformat(msg["timestamp"])
            }
            for msg in cursor.fetchall()
        ]
        
        return {
            "conversation_id": conversation_id,
            "messages": messages
        }
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

# Endpoint per ottenere l'elenco delle conversazioni recenti
@router.get("/")
async def list_conversations(limit: int = 10, offset: int = 0):
    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT c.id, c.title, c.created_at, 
                       (SELECT content FROM messages WHERE conversation_id = c.id AND role = 'user' ORDER BY timestamp ASC LIMIT 1) as preview
                FROM conversations c
                ORDER BY c.updated_at DESC
                LIMIT ? OFFSET ?
                ''',
                (limit, offset)
            )
            conversations = []
            for conv in cursor.fetchall():
                raw_created_at = conv["created_at"]
                if raw_created_at:
                    try:
                        created_at = datetime.fromisoformat(raw_created_at).strftime("%d/%m/%Y %H:%M")
                    except Exception:
                        created_at = str(raw_created_at)
                else:
                    created_at = ""
                conversations.append({
                    "id": conv["id"],
                    "title": conv["title"] or "Conversazione senza titolo",
                    "preview": conv["preview"][:100] + ("..." if len(str(conv["preview"])) > 100 else "") if conv["preview"] else "",
                    "created_at": created_at
                })
            return {"conversations": conversations}
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception as e:
        import traceback
        print("[history.py] Errore in list_conversations:", traceback.format_exc())
        return JSONResponse(content={"conversations": []}, status_code=200)

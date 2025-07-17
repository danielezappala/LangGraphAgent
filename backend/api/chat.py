import json
import traceback
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    thread_id: str

router = APIRouter(tags=["chat"])

def create_chunk(
    content: str, 
    chunk_type: str = "text", 
    tool_name: Optional[str] = None,
    is_final: bool = False,
    thread_id: Optional[str] = None
) -> dict:
    """
    Crea un dizionario con il contenuto e i metadati specificati.
    
    Args:
        content: Il contenuto testuale del messaggio
        chunk_type: Il tipo di messaggio ('text', 'tool_result', 'error', 'end')
        tool_name: Nome del tool se il messaggio è un risultato di tool
        is_final: Se True, indica che questo è l'ultimo chunk del messaggio
        thread_id: ID del thread della conversazione
        
    Returns:
        Un dizionario Python con i dati del chunk strutturati
    """
    try:
        # Assicurati che il contenuto sia una stringa
        if not isinstance(content, str):
            content = str(content)
        
        # Determina il ruolo in base al tipo di messaggio
        role = "assistant"
        if chunk_type == "error":
            role = "system"
        
        # Crea il dizionario con la struttura standard
        chunk_data = {
            "success": chunk_type != "error",
            "message": {
                "id": str(uuid.uuid4()),
                "content": content,
                "role": role,
                "timestamp": datetime.utcnow().isoformat(),
                "type": chunk_type,
                "thread_id": thread_id or ""
            },
            "metadata": {
                "model": "gpt-4",
                "chunk_type": chunk_type,
                "is_final": is_final,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Aggiungi il nome del tool se fornito
        if tool_name:
            chunk_data["message"]["tool_name"] = tool_name
            chunk_data["metadata"]["tool_name"] = tool_name
        
        # Gestione speciale per gli errori
        if chunk_type == "error":
            chunk_data["error"] = content
        
        return chunk_data
        
    except Exception as e:
        # In caso di errore, restituisci un messaggio di errore strutturato
        return {
            "success": False,
            "error": f"Errore nel formattare il chunk: {str(e)}",
            "message": {
                "id": str(uuid.uuid4()),
                "content": f"Errore nel formattare il chunk: {str(e)}",
                "role": "system",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "error",
                "thread_id": thread_id or ""
            },
            "metadata": {
                "model": "gpt-4",
                "chunk_type": "error",
                "is_final": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

@router.post("/stream")
async def stream_chat_endpoint(request: Request, chat_request: ChatRequest):
    print("\n" + "="*80)
    print("== INIZIO stream_chat_endpoint ==")
    print(f"Thread ID: {chat_request.thread_id}")
    print(f"Messaggio: {chat_request.message}")
    print(f"Tipo messaggio: {type(chat_request.message).__name__}")
    print(f"Tipo thread_id: {type(chat_request.thread_id).__name__}")
    print("="*80 + "\n")
    
    # Log dello stato dell'applicazione
    print("\n=== STATO APPLICAZIONE ===")
    print(f"Tipo di request.app.state: {type(request.app.state).__name__}")
    print(f"Attributi di app.state: {dir(request.app.state)}")
    
    # Verifica che il grafo sia disponibile
    if not hasattr(request.app.state, 'graph'):
        print("!!! ERRORE: graph non trovato in app.state !!!")
    else:
        print("Graph trovato in app.state")
    
    # Inizializza la configurazione e i dati di input
    graph = request.app.state.graph  # Aggiunta riga mancante
    config = {"configurable": {"thread_id": chat_request.thread_id}}
    input_data = {"messages": [("human", chat_request.message)]}
    
    print("\n=== CONFIGURAZIONE ===")
    print(f"Configurazione: {config}")
    print(f"Tipo configurazione: {type(config).__name__}")
    print(f"\n=== INPUT DATA ===")
    print(f"Input data: {input_data}")
    print(f"Tipo input_data: {type(input_data).__name__}")

    async def stream_generator():
        try:
            print("\n=== INIZIO GENERAZIONE STREAM ===")
            print(f"Tipo di graph: {type(graph).__name__}")
            print(f"Tipo di input_data: {type(input_data).__name__}")
            print(f"Tipo di config: {type(config).__name__}")
            
            is_first_chunk = True
            chunk_count = 0
            
            print("\n=== INIZIO ASTREAM ===")
            print(f"Avvio astream con config: {config}")
            print(f"Input data: {input_data}")
            
            print("\nInizio esecuzione grafo...")
            async for chunk in graph.astream(input_data, config=config):
                chunk_count += 1
                print(f"\n--- Chunk #{chunk_count} ---")
                print(f"Tipo: {type(chunk).__name__}")
                print(f"Contenuto: {chunk}")
                
                if not chunk:
                    print("Chunk vuoto, salto...")
                    continue
                
                # Log della struttura completa del chunk per debug
                print(f"\n=== STRUTTURA DEL CHUNK #{chunk_count} ===")
                print(f"Tipo: {type(chunk).__name__}")
                print("Contenuto completo:", chunk)
                
                # Gestione dei diversi tipi di chunk
                if hasattr(chunk, 'get') and callable(chunk.get):
                    # Handle agent responses
                    if "agent" in chunk and "messages" in chunk["agent"] and chunk["agent"]["messages"]:
                        agent_message = chunk["agent"]["messages"][0]
                        print(f"\nAgent message received: {agent_message}")
                        
                        # Extract content from agent message
                        try:
                            # First try to get content directly
                            if hasattr(agent_message, 'content'):
                                content = agent_message.content
                            # Then try to get it as a dictionary
                            elif isinstance(agent_message, dict) and 'content' in agent_message:
                                content = agent_message['content']
                            # Then try to get text attribute
                            elif hasattr(agent_message, 'text'):
                                content = agent_message.text
                            # As a last resort, try to convert to string
                            else:
                                content = str(agent_message)
                                
                            # If content is a list, try to extract text from it
                            if isinstance(content, list):
                                content = ' '.join([str(item) for item in content])
                                
                            print(f"Agent message content: {content}")
                            print(f"Agent message type: {type(agent_message).__name__}")
                            print(f"Agent message attributes: {[a for a in dir(agent_message) if not a.startswith('_')]}")
                            if hasattr(agent_message, '__dict__'):
                                print(f"Agent message __dict__: {agent_message.__dict__}")
                                
                        except Exception as e:
                            print(f"Error extracting content from agent message: {str(e)}")
                            content = "[Error: Could not extract message content]"
                        
                        # Send the agent message
                        if content:
                            chunk_data = create_chunk(
                                content=content,
                                chunk_type="text",
                                is_final=False,
                                thread_id=chat_request.thread_id
                            )
                            print(f"Sending agent message chunk: {chunk_data}")
                            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                    # Handle tool messages
                    elif "tools" in chunk and "messages" in chunk["tools"] and chunk["tools"]["messages"]:
                        tool_message = chunk["tools"]["messages"][0]
                        print(f"\nTool message received: {tool_message}")
                        
                        # Extract content and tool name from tool message
                        content = getattr(tool_message, 'content', '')
                        
                        # Try different ways to get the tool name
                        tool_name = (
                            getattr(tool_message, 'name', None) or  # Check for 'name' attribute
                            getattr(tool_message, 'tool', None) or  # Check for 'tool' attribute
                            (tool_message.tool_call.get('name') if hasattr(tool_message, 'tool_call') else None) or  # Check tool_call
                            'search_tool'  # Default to 'search_tool' for Tavily search results
                        )
                        
                        print(f"Tool message - Name: {tool_name}, Content: {content}")
                        
                        # Send the tool message
                        if content:
                            chunk_data = create_chunk(
                                content=content,
                                chunk_type="tool_result",
                                tool_name=tool_name,
                                is_final=False,
                                thread_id=chat_request.thread_id
                            )
                            print(f"Sending tool message chunk: {chunk_data}")
                            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                    # Handle other message types (legacy format)
                    elif "messages" in chunk and chunk["messages"]:
                        last_message = chunk["messages"][-1]
                        print(f"\nLegacy message format detected: {last_message}")
                        
                        # Extract content based on message type
                        content = ""
                        is_tool = False
                        tool_name = None
                        
                        # 1. Controlla se è un messaggio con tool_calls
                        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            print(f"Trovato tool_calls: {last_message.tool_calls}")
                            is_tool = True
                            if last_message.tool_calls:
                                tool_name = last_message.tool_calls[0].get("name")
                                print(f"Tool name: {tool_name}")
                        
                        # 2. Controlla se ha un contenuto diretto
                        if hasattr(last_message, 'content'):
                            content = last_message.content or ""
                            print(f"Contenuto diretto: {content}")
                        
                        # 3. Controlla additional_kwargs per altri dati
                        if hasattr(last_message, 'additional_kwargs'):
                            print(f"Additional kwargs: {last_message.additional_kwargs}")
                            if 'tool_calls' in last_message.additional_kwargs:
                                is_tool = True
                                tool_calls = last_message.additional_kwargs['tool_calls']
                                if tool_calls and not tool_name:
                                    tool_name = tool_calls[0].get('function', {}).get('name')
                                    print(f"Tool name da additional_kwargs: {tool_name}")
                        
                        # 4. Se è un tool ma non abbiamo ancora il contenuto, usiamo la rappresentazione stringa
                        if is_tool and not content:
                            content = str(getattr(last_message, 'content', '')) or str(last_message)
                            print(f"Contenuto generato per tool: {content}")
                        
                        print(f"=== FINE ANALISI MESSAGGIO ===\n")
                        
                        # Invia il chunk solo se c'è contenuto
                        if content:
                            chunk_type = "tool_result" if is_tool else "text"
                            print(f"Invio chunk - Tipo: {chunk_type}, Tool: {tool_name}")
                            chunk = create_chunk(
                                content=content,
                                chunk_type=chunk_type,
                                tool_name=tool_name,
                                is_final=False,
                                thread_id=chat_request.thread_id
                            )
                            print(f"Invio chunk: {chunk}")
                            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"                  
                    # Gestione di altri tipi di chunk (es. invocazioni di tool, aggiornamenti di stato)
                    elif "__end__" in chunk:
                        # Questo è l'ultimo chunk
                        chunk = create_chunk(
                            content="",
                            chunk_type="end",
                            is_final=True,
                            thread_id=chat_request.thread_id
                        )
                        print(f"Invio chunk finale: {chunk}")
                        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                        return
                    
                # Gestione dei chunk di stringa (solo per debug, non dovrebbe mai accadere)
                elif isinstance(chunk, str):
                    print(f"\n!!! ATTENZIONE: Ricevuto chunk come stringa invece che come oggetto:")
                    print(f"Chunk: {chunk}")
                    print("Inviando come messaggio di testo formattato...")
                    
                    # Invia il messaggio come JSON strutturato
                    chunk_data = create_chunk(
                        content=chunk,
                        chunk_type="text",
                        is_final=False
                    )
                    print(f"Invio chunk di testo: {chunk_data}")
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                
                is_first_chunk = False
                
            # Non inviare un chunk finale vuoto, lo stream termina naturalmente
            print("\nFine naturale dello stream")
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n!!! ERRORE DURANTE LO STREAMING !!!")
            print(f"Tipo: {type(e).__name__}")
            print(f"Messaggio: {error_msg}")
            print("Traceback completo:")
            traceback.print_exc()
            
            error_chunk = create_chunk(
                content=error_msg,
                chunk_type="error",
                is_final=True
            )
            print(f"Errore durante lo streaming: {error_chunk}")
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disabilita il buffering in nginx
        }
    )

# Non-streaming fallback endpoint
@router.post("")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    print("\n" + "="*80)
    print("INVOCATO ENDPOINT NON-STREAMING /api/chat")
    print(f"Thread ID: {chat_request.thread_id or 'new-thread'}")
    print(f"Message: {chat_request.message[:100]}..." if len(chat_request.message) > 100 else f"Message: {chat_request.message}")
    
    try:
        graph = request.app.state.graph
        thread_id = chat_request.thread_id or "new-thread"
        config = {"configurable": {"thread_id": thread_id}}
        input_data = {"messages": [("human", chat_request.message)]}
        
        print("\n[CHAT] Dettagli richiesta:")
        print(f"- Thread ID: {thread_id}")
        print(f"- Configurazione: {config}")
        print(f"- Dati input: {input_data}")
        
        print("\n[CHAT] Invocazione grafo in corso...")
        result = await graph.ainvoke(input_data, config=config)
        
        print("\n[CHAT] Risultato ricevuto:")
        print(f"- Chiavi disponibili: {list(result.keys())}")
        
        if messages := result.get("messages"):
            print(f"- Trovati {len(messages)} messaggi nel risultato")
            for i, msg in enumerate(messages):
                print(f"  Messaggio {i+1}: {str(msg)[:200]}...")
            
            # Prendi l'ultimo messaggio
            last_message = messages[-1]
            print("\n[CHAT] Ultimo messaggio:")
            print(f"- Tipo: {type(last_message).__name__}")
            print(f"- Contenuto: {str(last_message.content)[:200]}..." if hasattr(last_message, 'content') else "- Nessun contenuto")
            
            if hasattr(last_message, 'content'):
                # Crea una risposta strutturata con metadati
                response = {
                    "success": True,
                    "message": {
                        "id": str(uuid.uuid4()),
                        "content": last_message.content,
                        "role": "assistant",
                        "timestamp": datetime.utcnow().isoformat(),
                        "thread_id": thread_id,
                        "type": "text"
                    },
                    "metadata": {
                        "model": "gpt-4",
                        "tokens": len(last_message.content.split())  # Stima approssimativa
                    }
                }
                print("\n[CHAT] Invio risposta strutturata:", json.dumps(response, indent=2))
                print("="*80 + "\n")
                return response
        
        error_msg = "Nessun messaggio valido nella risposta"
        print(f"\n[CHAT] {error_msg}")
        print("="*80 + "\n")
        return {
            "success": False,
            "error": error_msg,
            "message": {
                "id": str(uuid.uuid4()),
                "content": error_msg,
                "role": "system",
                "timestamp": datetime.utcnow().isoformat(),
                "thread_id": thread_id,
                "type": "error"
            }
        }
    except Exception as e:
        print("\n[CHAT] !!! ERRORE CRITICO !!!")
        print(f"Tipo: {type(e).__name__}")
        print(f"Messaggio: {str(e)}")
        print("\nTraceback completo:")
        traceback.print_exc()
        
        error_response = {
            "error": f"Errore durante l'elaborazione del messaggio: {str(e)}",
            "type": type(e).__name__
        }
        
        print("\n[CHAT] Invio risposta di errore:", error_response)
        print("="*80 + "\n")
        
        return JSONResponse(
            status_code=500,
            content=error_response,
        )

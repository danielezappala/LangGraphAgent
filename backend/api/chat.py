import json
import traceback
from typing import Dict, Any
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    thread_id: str

router = APIRouter(prefix="/chat", tags=["chat"])

# Streaming endpoint (original implementation)
@router.post("/stream")
async def stream_chat_endpoint(request: Request, chat_request: ChatRequest):
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": chat_request.thread_id}}
    input_data = {"messages": [("human", chat_request.message)]}

    async def stream_generator():
        try:
            print("Starting streaming response...")
            async for chunk in graph.astream(input_data, config=config):
                print(f"Received chunk: {type(chunk)}")
                if messages := chunk.get("messages"):
                    # Yield the content of the last message
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        data = json.dumps({"content": last_message.content})
                        print(f"Sending chunk: {data[:50]}...")
                        yield f"data: {data}\n\n"
        except Exception as e:
            print(f"Error during streaming: {e}")
            print("Traceback:")
            traceback.print_exc()
            error_data = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

# Non-streaming fallback endpoint
@router.post("")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    try:
        graph = request.app.state.graph
        thread_id = chat_request.thread_id or "new-thread"
        config = {"configurable": {"thread_id": thread_id}}
        input_data = {"messages": [("human", chat_request.message)]}
        
        print(f"[CHAT] Processing message with thread_id: {thread_id}")
        print(f"[CHAT] Input message: {chat_request.message}")
        print(f"[CHAT] Using config: {config}")
        result = await graph.ainvoke(input_data, config=config)
        print(f"[CHAT] Graph invocation completed. Result keys: {list(result.keys())}")
        
        if messages := result.get("messages"):
            print(f"[CHAT] Found {len(messages)} messages in result")
            # Get the content of the last message
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                return {"content": last_message.content}
        
        return {"content": "I don't have a response for that."}
    except Exception as e:
        print(f"Error in non-streaming chat: {e}")
        print("Traceback:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Chat processing error: {str(e)}"},
        )

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
import os

from backend.config import HISTORY_FILE, SYSTEM_PROMPT_FILE, MODEL_NAME, MIN_RESPONSE_TOKENS
from backend.persistent_memory import PersistentMemory
from backend.llm_utils import LLMClient
from backend.agent import ConversationalAgent
import json

load_dotenv()

app = FastAPI()

# Abilita CORS per sviluppo frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# Inizializza agent una sola volta
# --- Multi-agent setup ---
from typing import Dict

AGENTS: Dict[str, ConversationalAgent] = {}
AGENT_CONFIGS = {
    "basic1": {
        "name": "Basic1",
        "llm": MODEL_NAME,
        "prompt_file": SYSTEM_PROMPT_FILE
    }
}
for agent_id, cfg in AGENT_CONFIGS.items():
    mem = PersistentMemory(cfg["name"])
    llm = LLMClient(cfg["llm"], MIN_RESPONSE_TOKENS)
    with open(cfg["prompt_file"], "r") as f:
        prompt = json.load(f)
    AGENTS[agent_id] = ConversationalAgent(cfg["name"], mem, llm)
    # Log del grafo mermaid all'avvio
    try:
        from backend.graph_mermaid import stategraph_to_mermaid
        mermaid = stategraph_to_mermaid(AGENTS[agent_id].graph)
        print(f"[BACKEND] Grafo Mermaid per agente {agent_id}:\n{mermaid}")
    except Exception as e:
        print(f"[BACKEND] Errore generazione grafo Mermaid per agente {agent_id}: {e}")

# --- API endpoints ---

@app.get("/agents")
def list_agents():
    return [{
        "id": agent_id,
        "name": cfg["name"],
        "llm": cfg["llm"]
    } for agent_id, cfg in AGENT_CONFIGS.items()]

@app.get("/agents/{agent_id}")
def agent_details(agent_id: str):
    cfg = AGENT_CONFIGS.get(agent_id)
    if not cfg:
        return {"error": "Agent not found"}
    with open(cfg["prompt_file"], "r") as f:
        prompt = json.load(f)
    # Ottieni il grafo reale dell'agente
    agent = AGENTS.get(agent_id)
    grafo_mermaid = None
    if agent:
        try:
            from backend.graph_mermaid import stategraph_to_mermaid
            grafo_mermaid = stategraph_to_mermaid(agent.graph)
            print(f"[BACKEND] /agents/{{agent_id}} restituisce grafo:\n{grafo_mermaid}")
        except Exception as e:
            grafo_mermaid = f"Errore generazione grafo: {e}"
            print(f"[BACKEND] Errore generazione grafo in /agents/{{agent_id}}: {e}")
    else:
        grafo_mermaid = ""
        print(f"[BACKEND] Nessun grafo disponibile per agente {agent_id}")
    return {
        "id": agent_id,
        "name": cfg["name"],
        "llm": cfg["llm"],
        "prompt": prompt,
        "grafo": grafo_mermaid
    }

@app.post("/agents/{agent_id}/chat", response_model=ChatResponse)
def agent_chat(agent_id: str, request: ChatRequest):
    agent = AGENTS.get(agent_id)
    if not agent:
        return ChatResponse(response="Agent not found.")
    state = {"history": agent.memory.get_history(with_metadata=True), "last_input": request.message}
    result = agent.graph.invoke(state)
    risposta = result["history"][-1]["content"]
    return ChatResponse(response=risposta)

# --- Legacy endpoint for retrocompatibilità ---
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    agent = AGENTS["default"]
    state = {"history": agent.memory.get_history(with_metadata=True), "last_input": request.message}
    result = agent.graph.invoke(state)
    risposta = result["history"][-1]["content"]
    return ChatResponse(response=risposta)

if __name__ == "__main__":
    uvicorn.run("backend.api_server:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True) 
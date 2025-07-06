from __future__ import annotations
import logging
from typing import Any, Dict, List, TypedDict
from abc import ABC, abstractmethod
from langgraph.graph import END, StateGraph
from .persistent_memory import PersistentMemory
from .intent_extractor import extract_intent
from .mcp_tools import weather_tool, calendar_tool, recipe_tool

class BaseAgent(ABC):
    """
    Blueprint base per ogni agente AI.
    REQUISITI:
    - Ogni agente deve essere istanza di una sottoclasse di BaseAgent.
    - Attributi obbligatori: name, memory, llm_client, system_prompt, graph.
    - Deve implementare _build_graph (costruzione grafo) e node_func (logica nodo principale).
    """
    def __init__(self, name: str, memory: PersistentMemory, llm_client: Any, system_prompt: Any = None):
        self.name = name
        self.memory = memory
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.graph = self._build_graph()

    @abstractmethod
    def _build_graph(self):
        pass

    @abstractmethod
    def node_func(self, state: Dict) -> Dict:
        pass

    def run(self):
        print(f"Conversazione con l'agente {self.name} (scrivi 'esci' per terminare)")
        while True:
            user_input = input("Tu: ")
            if user_input.strip().lower() == "esci":
                break
            state = {"history": self.memory.get_history(with_metadata=True), "last_input": user_input}
            result = self.graph.invoke(state)
            print("Agente:", result["history"][-1]["content"])


# -------------------- system prompt (inglese) -------------------------
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are an expert AI assistant. "
        "Answer in Italian unless the user switches language. "
        "Keep replies concise and helpful."
    ),
}

# -------------------- logging -----------------------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# -------------------- state typing ------------------------------------
class ConvState(TypedDict, total=False):
    history: List[dict]
    last_input: str
    intent: str
    entities: dict | List[dict]
    tool_response: str

ROUTES = {
    "weather": "weather_tool",
    "agenda":  "calendar_tool",
    "food":    "recipe_tool",
}

# -------------------- base agent --------------------------------------

class ConversationalAgent(BaseAgent):
    """
    Agente conversazionale standard con grafo intent/tool/LLM.
    """
    def _build_graph(self):
        g: StateGraph[ConvState] = StateGraph(ConvState)
        g.add_node("start", lambda s: s)
        def node_intent(state: ConvState):
            res = extract_intent(state.get("last_input", ""))
            state["intent"] = res["intent"]
            state["entities"] = res["entities"]
            log.info("Intent=%s Entities=%s", state['intent'], state['entities'])
            return state
        g.add_node("intent", node_intent)
        def node_weather(state: ConvState):
            ent = state.get("entities", {})
            city = ent.get("city") if isinstance(ent, dict) else "?"
            date = ent.get("date") if isinstance(ent, dict) else "?"
            out  = weather_tool({"city": city, "date": date})
            state["tool_response"] = (
                f"Previsioni meteo per {out['city']} il {out['date']}: {out['forecast']}"
            )
            return state
        g.add_node("weather_tool", node_weather)
        g.add_node("calendar_tool",
                   lambda s: s | {"tool_response": calendar_tool(s.get("entities", {}))})
        g.add_node("recipe_tool",
                   lambda s: s | {"tool_response": recipe_tool(s.get("entities", {}))})
        def node_llm(state: ConvState):
            msgs = [SYSTEM_PROMPT]
            msgs += [{"role": m["role"], "content": m["content"]} for m in state.get("history", [])]
            msgs.append({"role": "user", "content": state["last_input"]})
            state["tool_response"] = self.llm_client.invoke_with_continuation(msgs, 20)
            return state
        g.add_node("llm_response", node_llm)
        g.add_edge("start", "intent")
        def router(state: ConvState) -> str:
            return ROUTES.get(state.get("intent"), "llm_response")
        g.add_conditional_edges("intent", router)
        for term in ("weather_tool", "calendar_tool", "recipe_tool", "llm_response"):
            g.add_edge(term, END)
        g.set_entry_point("start")
        return g.compile()

    def node_func(self, state: Dict) -> Dict:
        # Nodo principale per compatibilità futura (non usato direttamente qui)
        return state


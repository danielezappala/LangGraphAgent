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
            return {
                "tool_response": f"Previsioni meteo per {out['city']} il {out['date']}: {out['forecast']}"
            }
        g.add_node("weather_tool", node_weather)
        g.add_node("calendar_tool",
                   lambda s: {"tool_response": calendar_tool(s.get("entities", {}))})
        g.add_node("recipe_tool",
                   lambda s: {"tool_response": recipe_tool(s.get("entities", {}))})
        def node_llm(state: ConvState):
            msgs = []
            if self.system_prompt:
                msgs.append(self.system_prompt if isinstance(self.system_prompt, dict) else {"role": "system", "content": self.system_prompt})
            msgs += [{"role": m["role"], "content": m["content"]} for m in state.get("history", [])]
            msgs.append({"role": "user", "content": state["last_input"]})
            # Assumendo che invoke_with_continuation restituisca direttamente il contenuto della risposta
            response_content = self.llm_client.invoke_with_continuation(msgs, 20)
            return {"tool_response": response_content}
        g.add_node("llm_response", node_llm)

        def node_update_history(state: ConvState):
            """
            Aggiorna la cronologia con l'ultimo input dell'utente e la risposta dell'agente.
            Chiama self.memory.add_message() per preparare il salvataggio.
            """
            user_input = state.get("last_input")
            agent_response = state.get("tool_response") # Questo ora contiene la risposta dell'LLM o dello strumento

            if user_input:
                # TODO: Decidere come gestire i token per l'input dell'utente. Per ora, 0.
                self.memory.add_message(role="user", content=user_input, tokens=0)
            
            if agent_response:
                # TODO: Decidere come gestire i token per la risposta dell'agente. 
                # Se la risposta è dall'LLM, idealmente l'LLM dovrebbe restituire il conteggio dei token.
                # Per gli strumenti, potrebbe essere 0 o un valore stimato. Per ora, 0.
                self.memory.add_message(role="assistant", content=agent_response, tokens=0)
            
            # Restituisce la cronologia aggiornata da PersistentMemory per lo stato del grafo
            # Questo assicura che lo stato del grafo rifletta ciò che è in memoria prima del salvataggio.
            return {"history": self.memory.get_history(with_metadata=True)}
        
        g.add_node("update_history", node_update_history)
        g.add_edge("start", "intent")
        
        def router(state: ConvState) -> str:
            return ROUTES.get(state.get("intent"), "llm_response")
        
        g.add_conditional_edges("intent", router)
        
        # I nodi degli strumenti e il nodo di risposta LLM ora puntano a update_history
        for tool_node_name in ROUTES.values():
            g.add_edge(tool_node_name, "update_history")
        g.add_edge("llm_response", "update_history")
        
        # update_history punta a END
        g.add_edge("update_history", END)
        
        g.set_entry_point("start")
        return g.compile()

    def node_func(self, state: Dict) -> Dict:
        # Nodo principale per compatibilità futura (non usato direttamente qui)
        return state


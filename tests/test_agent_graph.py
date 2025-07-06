import pytest
from backend.agent import ConversationalAgent
from backend.graph_validation import validate_agent_graph

def test_agent_graph_serialization_and_validation():
    """
    Test end-to-end:
    - Costruisce un agente conversazionale
    - Simula tutte le navigazioni possibili (intent)
    - Serializza il grafo e lo valida
    - Accetta warning su archi virtuali, segnala errore solo se manca davvero il path logico
    """
    # Mock minimal
    class MockMemory:
        def append(self, *a, **kw): pass
        def get(self, *a, **kw): return []
    class MockLLMClient:
        def invoke_with_continuation(self, messages, *args, **kwargs):
            # Se chiamata da intent_extraction, restituisci JSON valido
            if messages and "estrai" in messages[0]["content"].lower():
                # Simula intent extraction weather
                return '{"intent": "weather", "entities": {"city": "Milano", "date": "oggi"}}'
            return "Risposta mock"
    agent = ConversationalAgent(
        name="basic1",
        memory=MockMemory(),
        llm_client=MockLLMClient(),
        system_prompt={"role": "system", "content": "Prompt di test"}
    )
    compiled = agent._build_graph()
    # Simula tutti i path logici dopo la compilazione (best practice LangGraph)
    compiled.invoke({"intent": "weather", "last_input": "Che tempo fa a Milano?", "entities": {"city": "Milano", "date": "oggi"}})
    compiled.invoke({"intent": "general", "last_input": "Dimmi una barzelletta", "entities": {}})
    compiled.invoke({"intent": "unknown", "last_input": "Test fallback", "entities": {}})
    g = compiled.get_graph()
    nodes = list(g.nodes)
    edges = list(g.edges)
    print(f"[TEST] Nodi: {nodes}")
    print(f"[TEST] Archi: {edges}")
    # Validazione custom (accetta warning su archi virtuali)
    validate_agent_graph(compiled, start="start_node", end="end_node")
    # Se la validazione non solleva errori, il test passa

import pytest
from backend.agent import BaseAgent, ConversationalAgent
from backend.persistent_memory import PersistentMemory
from backend.graph_mermaid import stategraph_to_mermaid

class DummyLLM:
    def invoke_with_continuation(self, messages, min_tokens):
        return "dummy response"
    def count_tokens(self, messages):
        return 1

def test_baseagent_instantiation():
    # Cannot instantiate BaseAgent directly (should raise TypeError)
    with pytest.raises(TypeError):
        BaseAgent("test", PersistentMemory("test"), DummyLLM(), "prompt")

def test_conversational_agent_instantiation():
    agent = ConversationalAgent(
        name="test",
        memory=PersistentMemory("test"),
        llm_client=DummyLLM(),
        system_prompt="prompt"
    )
    assert agent.name == "test"
    assert hasattr(agent, "graph")
    assert callable(agent.node_func)
    # Test nodi/edge tramite API pubbliche
    # 1. nodes property
    nodes = agent.graph.nodes if hasattr(agent.graph, "nodes") else None
    if nodes is not None:
        assert "llm_node" in nodes
        assert "end_node" in nodes
    # 2. get_graph (potrebbe restituire un oggetto networkx)
    g = agent.graph.get_graph() if hasattr(agent.graph, "get_graph") else None
    if g is not None:
        # networkx Graph: check node presence with 'in g.nodes'
        assert "llm_node" in g.nodes
        assert "end_node" in g.nodes
        # Check at least one edge
        assert len(list(g.edges)) >= 1

def test_mermaid_export_conversational_agent():
    agent = ConversationalAgent(
        name="test",
        memory=PersistentMemory("test"),
        llm_client=DummyLLM(),
        system_prompt="prompt"
    )
    mermaid = stategraph_to_mermaid(agent.graph)
    # Deve contenere almeno le transizioni chiave
    assert "start_node --> llm_node" in mermaid
    assert "llm_node --> end_node" in mermaid
    # Non deve contenere errori
    assert "Errore" not in mermaid

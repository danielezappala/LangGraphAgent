import pytest
from backend.basic_chatbot import graph, memory

def test_rewind_time_travel():
    # Simula una breve conversazione
    config = {"configurable": {"thread_id": "test-thread"}}
    state1 = {"messages": [{"role": "user", "content": "Ciao!"}], "user_name": "Test"}
    graph.invoke(state1, config)
    state2 = {"messages": [{"role": "user", "content": "Come stai?"}], "user_name": "Test"}
    graph.invoke(state2, config)
    state3 = {"messages": [{"role": "user", "content": "Raccontami una barzelletta."}], "user_name": "Test"}
    graph.invoke(state3, config)

    # Ottieni la lista degli snapshot
    # MemorySaver: snapshots(thread_id) restituisce la lista degli snapshot per il thread
    snapshots = memory.snapshots("test-thread")
    assert len(snapshots) >= 2, "Devono esserci almeno 2 snapshot per testare rewind."

    # Rewind di 2 step
    target_idx = max(0, len(snapshots) - 2)
    snapshot_id = snapshots[target_idx]
    restored_state = graph.rewind(snapshot_id)
    assert isinstance(restored_state, dict)
    # Lo stato ripristinato deve contenere almeno la chiave 'messages'
    assert "messages" in restored_state
    # Il messaggio utente deve essere coerente con lo stato ripristinato
    assert any(m["content"].lower() in ["ciao!", "come stai?", "raccontami una barzelletta."] for m in restored_state["messages"])

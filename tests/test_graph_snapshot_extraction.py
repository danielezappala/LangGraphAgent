import pytest
from backend.basic_chatbot import graph

def make_snapshot(state):
    class DummySnap:
        def __init__(self, state, id):
            self.state = state
            self.id = id
            self.config = {}
    return DummySnap(state, id(state))

# Funzione copiata e adattata dalla /graph per testare estrazione messaggi

def extract_last_user_message(snap):
    last_msg = ""
    if hasattr(snap, "state") and snap.state and isinstance(snap.state, dict):
        msgs = snap.state.get("messages")
        print(f"[DEBUG] Snapshot {snap.id} - state: {repr(snap.state)}")
        print(f"[DEBUG] Snapshot {snap.id} - msgs: {repr(msgs)}")
        if msgs and isinstance(msgs, list) and msgs:
            if not any(isinstance(m, dict) for m in msgs):
                print(f"[DEBUG] msgs non dict: tipo={type(msgs[0])}, repr={repr(msgs[0])}")
            user_msgs = []
            for m in msgs:
                if isinstance(m, dict) and m.get("role") == "user":
                    user_msgs.append(m)
                elif hasattr(m, "role") and getattr(m, "role", None) == "user":
                    user_msgs.append(m)
            if user_msgs:
                last = user_msgs[-1]
                if isinstance(last, dict):
                    last_msg = last.get("content", "")
                elif hasattr(last, "content"):
                    last_msg = getattr(last, "content", "")
                else:
                    last_msg = str(last)
            else:
                # Cerca l'ultimo elemento non None
                for m in reversed(msgs):
                    if m is not None:
                        last_msg = str(m)
                        break
                else:
                    last_msg = "<nessun messaggio>"
        else:
            print(f"[DEBUG] msgs vuoto o tipo inatteso: {type(msgs)} - {repr(msgs)}")
    if last_msg and len(last_msg) > 40:
        last_msg = last_msg[:37] + "..."
    if not last_msg:
        last_msg = "<nessun messaggio>"
    return last_msg

def test_snapshot_extraction_various_formats():
    # Caso 1: lista di dict
    snap1 = make_snapshot({"messages": [
        {"role": "user", "content": "Ciao!"},
        {"role": "assistant", "content": "Ciao! Come posso aiutarti?"},
        {"role": "user", "content": "Come stai?"}
    ]})
    assert extract_last_user_message(snap1) == "Come stai?"

    # Caso 2: lista di oggetti con attributi
    class Msg:
        def __init__(self, role, content):
            self.role = role
            self.content = content
    snap2 = make_snapshot({"messages": [
        Msg("user", "Ciao!"),
        Msg("assistant", "Risposta"),
        Msg("user", "Test oggetto")
    ]})
    assert extract_last_user_message(snap2) == "Test oggetto"

    # Caso 3: lista mista
    snap3 = make_snapshot({"messages": [
        {"role": "user", "content": "A"},
        Msg("user", "B")
    ]})
    assert extract_last_user_message(snap3) == "B"

    # Caso 4: lista di stringhe
    snap4 = make_snapshot({"messages": ["Messaggio semplice"]})
    assert extract_last_user_message(snap4) == "Messaggio semplice"

    # Caso 5: lista vuota
    snap5 = make_snapshot({"messages": []})
    assert extract_last_user_message(snap5) == "<nessun messaggio>"

    # Caso 6: chiave mancante
    snap6 = make_snapshot({})
    assert extract_last_user_message(snap6) == "<nessun messaggio>"

    # Caso 7: formato ignoto
    snap7 = make_snapshot({"messages": [123, None]})
    assert extract_last_user_message(snap7) == "123"

if __name__ == "__main__":
    test_snapshot_extraction_various_formats()
    print("[TEST] Estrazione messaggio utente dagli snapshot: OK")

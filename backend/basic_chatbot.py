from typing import Annotated
from typing_extensions import TypedDict
from typing import Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
import os
import json
from dotenv import load_dotenv
import json
from langchain_tavily import TavilySearch
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt
try:
    from IPython.display import Image, display
    HAS_IPYTHON = True
except ImportError:
    HAS_IPYTHON = False

def extract_node_name(snap: Any) -> str:
    """Estrai il nome del nodo da uno snapshot.
    
    Args:
        snap: Lo snapshot da cui estrarre il nome del nodo
        
    Returns:
        str: Il nome del nodo o 'unknown' se non trovato
    """
    try:
        # 1. Cerca in values._current_node
        if hasattr(snap, "values") and hasattr(snap.values, "get"):
            node_name = snap.values.get("_current_node")
            if node_name:
                return str(node_name)
        
        # 2. Cerca in metadata.source
        if hasattr(snap, "metadata") and hasattr(snap.metadata, "get"):
            node_name = snap.metadata.get("source")
            if node_name:
                return str(node_name)
        
        # 3. Prova con _asdict()
        if hasattr(snap, "_asdict"):
            snap_dict = snap._asdict()
            # Cerca in values._current_node
            if "values" in snap_dict and isinstance(snap_dict["values"], dict):
                node_name = snap_dict["values"].get("_current_node")
                if node_name:
                    return str(node_name)
            # Cerca in metadata.source
            if "metadata" in snap_dict and isinstance(snap_dict["metadata"], dict):
                node_name = snap_dict["metadata"].get("source")
                if node_name:
                    return str(node_name)
        
        # 4. Prova con __dict__
        if hasattr(snap, "__dict__"):
            snap_dict = vars(snap)
            # Cerca in values._current_node
            if "values" in snap_dict and hasattr(snap_dict["values"], "get"):
                node_name = snap_dict["values"].get("_current_node")
                if node_name:
                    return str(node_name)
            # Cerca in metadata.source
            if "metadata" in snap_dict and hasattr(snap_dict["metadata"], "get"):
                node_name = snap_dict["metadata"].get("source")
                if node_name:
                    return str(node_name)
        
        return "unknown"
    except Exception as e:
        print(f"[ERROR] Errore nell'estrazione del nome del nodo: {e}")
        return "error"

# Carica le API key da .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY non trovata. Inserisci la chiave nel file .env o come variabile d'ambiente.")
if not tavily_key:
    raise RuntimeError("TAVILY_API_KEY non trovata. Inserisci la chiave nel file .env o come variabile d'ambiente.")
os.environ["OPENAI_API_KEY"] = api_key
os.environ["TAVILY_API_KEY"] = tavily_key

# Definisci lo stato del grafo
class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

# 1. Definisci il tool TavilySearch e la supervisione umana
search_tool = TavilySearch(max_results=2)

# Tool di supervisione umana secondo tutorial LangGraph
@tool
def human_assistance(query: str) -> str:
    """Richiedi assistenza a un umano. Usa questo strumento quando la richiesta richiede un giudizio umano, 
    è di natura sensibile o richiede competenze specialistiche che vanno oltre le capacità dell'AI."""
    try:
        print(f"\n[SUPERVISIONE UMANA] Richiesta di intervento umano per: {query}")
        human_response = input("Inserisci la risposta: ")
        print(f"[RISPOSTA UMANA] {human_response}")
        return human_response
    except Exception as e:
        print(f"[ERRORE] Errore durante l'assistenza umana: {str(e)}")
        return "Mi dispiace, si è verificato un errore durante la richiesta di assistenza umana. Riprova più tardi."

tools = [search_tool, human_assistance]

# 2. Inizializza il modello LLM e bind_tools
llm = init_chat_model("openai:gpt-4o")
llm_with_tools = llm.bind_tools(tools)

# 3. Nodo principale chatbot (supporta solo una tool_call per ciclo, come da tutorial)
def convert_message_to_dict(message):
    """Converte un oggetto messaggio in un dizionario, normalizzando 'type' a 'role'."""
    final_dict = {}
    if isinstance(message, dict):
        final_dict = message.copy()
    elif hasattr(message, 'dict'):
        final_dict = message.dict()
    elif hasattr(message, 'to_dict'):
        final_dict = message.to_dict()
    else:
        # Fallback per oggetti non standard
        if hasattr(message, 'role'):
            final_dict['role'] = message.role
        elif hasattr(message, 'type'):
            final_dict['role'] = message.type
        
        if hasattr(message, 'content'):
            final_dict['content'] = message.content
        if hasattr(message, 'tool_calls'):
            final_dict['tool_calls'] = message.tool_calls
        if hasattr(message, 'tool_call_id'):
            final_dict['tool_call_id'] = message.tool_call_id

    # Normalizza 'type' a 'role' se 'role' non è già presente
    if 'type' in final_dict and 'role' not in final_dict:
        final_dict['role'] = final_dict.pop('type')

    return final_dict

def sanitize_history(messages: list) -> list:
    """
    Pulisce e sanifica la cronologia dei messaggi per renderla conforme alle API OpenAI.
    - Rimuove i duplicati esatti.
    - Rimuove i messaggi 'tool' orfani (non preceduti da una 'tool_calls').
    - Unisce i messaggi consecutivi dello stesso ruolo (es. due 'user' di fila).
    """
    if not messages:
        return []

    # 1. Converti tutto in dizionari e deduplica usando JSON canonico
    unique_messages = []
    seen = set()
    for msg in messages:
        try:
            msg_dict = convert_message_to_dict(msg)
            # Serializza in una stringa JSON canonica per una deduplicazione robusta
            # default=str gestisce tipi non serializzabili come oggetti errore o Pydantic models
            canonical_repr = json.dumps(msg_dict, sort_keys=True, default=str)
            if canonical_repr not in seen:
                seen.add(canonical_repr)
                unique_messages.append(msg_dict) # Ora msg_dict è già un dizionario pulito
        except Exception as e:
            print(f"[SANITIZE] Ignorato messaggio non processabile durante la deduplicazione: {e}")

    # 2. Valida la sequenza dei tool_calls
    valid_sequence = []
    for msg in unique_messages:
        if msg.get('role') == 'tool':
            if (valid_sequence and 
                valid_sequence[-1].get('role') == 'assistant' and 
                valid_sequence[-1].get('tool_calls')):
                valid_sequence.append(msg)
            else:
                print(f"[SANITIZE] Ignorato messaggio 'tool' orfano: {str(msg.get('content', ''))[:100]}")
        else:
            valid_sequence.append(msg)

    # 3. Unisci messaggi consecutivi dello stesso ruolo (eccetto 'tool')
    if not valid_sequence:
        return []
        
    merged_messages = [valid_sequence[0]]
    for i in range(1, len(valid_sequence)):
        current_msg = valid_sequence[i]
        last_msg = merged_messages[-1]
        
        # Unisci se i ruoli sono identici e non sono 'tool' o 'assistant' con tool_calls
        if (current_msg.get('role') == last_msg.get('role') and 
            current_msg.get('role') != 'tool' and 
            not last_msg.get('tool_calls')):
            
            content1 = str(last_msg.get('content', '') or '')
            content2 = str(current_msg.get('content', '') or '')
            merged_messages[-1]['content'] = f"{content1}\n{content2}".strip()
            print(f"[SANITIZE] Messaggi consecutivi uniti per il ruolo: {current_msg.get('role')}")
        else:
            merged_messages.append(current_msg)
            
    return merged_messages

def chatbot(state: State) -> State:
    try:
        print("\n[CHATBOT] Inizio elaborazione stato...")
        # Crea una copia dello stato per evitare modifiche in-place
        new_state = state.copy()
        new_state["_current_node"] = "chatbot"
        
        messages = new_state.get("messages", [])

        # Sanifica la cronologia per rimuovere duplicati e correggere la sequenza
        validated_messages = sanitize_history(messages)

        if not validated_messages:
            print("[ERROR] Nessun messaggio valido dopo la validazione. Impossibile procedere.")
            return {
                "messages": messages + [{
                    'role': 'assistant', 
                    'content': 'Si è verificato un errore interno, la cronologia non è valida.'
                }],
                "_current_node": "chatbot"
            }

        print(f"\n[DEBUG] Messaggi validati pronti per l'invio ({len(validated_messages)} totali):")
        for i, msg in enumerate(validated_messages):
            print(f"  {i}. {msg.get('role', '').upper()}: {str(msg.get('content', ''))[:100]}...")

        # Invoca il modello con i messaggi validati
        message = llm_with_tools.invoke(validated_messages)
        
        print(f"[CHATBOT] Risposta generata: {getattr(message, 'content', str(message))[:100]}...")

        # Aggiungi la nuova risposta alla cronologia originale
        new_state["messages"] = messages + [message]

        return new_state

    except Exception as e:
        print(f"[CRITICAL] Errore critico in chatbot(): {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "messages": state.get("messages", []) + [{
                "role": "assistant", 
                "content": "Si è verificato un errore critico. Per favore, riprova."
            }],
            "_current_node": "chatbot"
        }

graph_builder.add_node("chatbot", chatbot)

# 4. Nodo tool: usa ToolNode prebuilt e tools_condition per routing
# (questo gestisce sia Tavily che human_assistance)
tool_node = ToolNode(tools=tools)

def tool_node_wrapper(state: State) -> State:
    try:
        print("[DEBUG] ToolNode - Inizio elaborazione")
        
        # Crea una copia dello stato per evitare modifiche in-place
        new_state = state.copy()
        new_state["_current_node"] = "tool_node"
        
        messages = new_state.get("messages", [])
        if not messages:
            print("[TOOL_NODE] Nessun messaggio trovato")
            return {"messages": [], "_current_node": "tool_node"}
            
        last_message = messages[-1]
        print(f"[TOOL_NODE] Ultimo messaggio: {type(last_message).__name__}")
        
        # Converti l'ultimo messaggio in dizionario
        last_msg_dict = convert_message_to_dict(last_message)
        
        # Estrai le tool calls dal messaggio
        tool_calls = last_msg_dict.get("tool_calls", [])
        if not tool_calls:
            print("[TOOL_NODE] Nessuna tool call trovata")
            return new_state
            
        print(f"[TOOL_NODE] Trovate {len(tool_calls)} tool calls")
        
        # Esegui ogni tool e raccogli i risultati
        tool_responses = []
        for tool_call in tool_calls:
            try:
                # Estrai le informazioni necessarie dalla tool call
                tool_call_id = None
                tool_name = None
                tool_args = {}
                
                # Gestisci diversi formati di tool call
                if isinstance(tool_call, dict):
                    tool_call_id = tool_call.get("id")
                    if "function" in tool_call:
                        tool_name = tool_call["function"].get("name")
                        tool_args_str = tool_call["function"].get("arguments", "{}")
                    else:
                        tool_name = tool_call.get("name")
                        tool_args_str = tool_call.get("arguments", "{}")
                elif hasattr(tool_call, "function"):
                    tool_call_id = getattr(tool_call, "id", None)
                    tool_name = getattr(tool_call.function, "name", None)
                    tool_args_str = getattr(tool_call.function, "arguments", "{}")
                else:
                    tool_call_id = getattr(tool_call, "id", None)
                    tool_name = getattr(tool_call, "name", None)
                    tool_args_str = getattr(tool_call, "arguments", "{}")
                
                if not tool_name or not tool_call_id:
                    print(f"[TOOL_NODE] Tool call non valida: {tool_call}")
                    continue
                
                # Converti gli argomenti da stringa JSON a dizionario se necessario
                if isinstance(tool_args_str, str):
                    import json
                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError:
                        tool_args = {"query": tool_args_str}  # Fallback per argomenti non JSON
                else:
                    tool_args = tool_args_str
                
                # Assicurati che tool_args sia un dizionario
                if not isinstance(tool_args, dict):
                    tool_args = {"input": str(tool_args)}
                
                # Trova il tool corrispondente
                tool = next((t for t in tools if t.name == tool_name), None)
                if not tool:
                    print(f"[TOOL_NODE] Tool non trovato: {tool_name}")
                    tool_result = f"Errore: Tool '{tool_name}' non trovato"
                else:
                    # FIX: Se il tool è human_assistance e non ha una query, la inseriamo dall'ultimo messaggio utente
                    if tool_name == "human_assistance" and not tool_args.get("query"):
                        print("[TOOL_NODE] La query per human_assistance è mancante, la estraggo dallo stato.")
                        # Cerca l'ultimo messaggio umano nello stato (può essere dict o HumanMessage)
                        last_human_message = next((msg for msg in reversed(messages) if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get("role") == "user")), None)
                        
                        if last_human_message:
                            # Estrai il contenuto in modo sicuro
                            if isinstance(last_human_message, dict):
                                query_content = last_human_message.get('content', '')
                            else: # È un oggetto BaseMessage
                                query_content = getattr(last_human_message, 'content', '')
                            
                            tool_args["query"] = query_content
                            print(f"[TOOL_NODE] Query inserita: '{tool_args['query']}'")
                        else:
                            print("[TOOL_NODE] ATTENZIONE: Nessun messaggio umano trovato per popolare la query.")

                    # Esegui il tool con gli argomenti corretti
                    try:
                        tool_result = tool.invoke(tool_args)
                        print(f"[TOOL_NODE] Tool {tool_name} eseguito con successo")
                    except Exception as e:
                        error_msg = f"Errore durante l'esecuzione del tool: {str(e)}"
                        print(f"[ERROR] {error_msg}")
                        tool_result = error_msg
                
                # Crea la risposta del tool nel formato corretto per le API OpenAI
                tool_response = {
                    "role": "tool",
                    "content": str(tool_result),
                    "tool_call_id": tool_call_id,
                    "name": tool_name
                }
                
                tool_responses.append(tool_response)
                
            except Exception as e:
                error_msg = f"Errore durante l'elaborazione della tool call: {str(e)}"
                print(f"[ERROR] {error_msg}")
                import traceback
                traceback.print_exc()
                
                # Aggiungi una risposta di errore
                tool_responses.append({
                    "role": "tool",
                    "content": error_msg,
                    "tool_call_id": tool_call_id or "unknown",
                    "name": tool_name or "unknown"
                })
        
        # Crea una copia dei messaggi esistenti
        result_messages = messages.copy()
        
        # Aggiungi le risposte dei tool ai messaggi
        for response in tool_responses:
            # Crea un nuovo messaggio per ogni risposta tool
            tool_message = {
                "role": "tool",
                "content": response["content"],
                "tool_call_id": response["tool_call_id"],
                "name": response["name"]
            }
            result_messages.append(tool_message)
        
        print(f"[TOOL_NODE] Aggiunte {len(tool_responses)} risposte tool")
        
        return {
            "messages": result_messages,
            "_current_node": "tool_node"
        }
        
    except Exception as e:
        print(f"[ERROR] Errore critico in tool_node: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # In caso di errore critico, restituisci un messaggio di errore
        error_response = {
            "role": "tool",
            "content": f"Si è verificato un errore critico durante l'esecuzione del tool: {str(e)}",
            "tool_call_id": "error_" + str(hash(str(e)))[:8],
            "name": "error_handler"
        }
        
        # Assicurati di restituire lo stato con i messaggi esistenti + l'errore
        result_messages = state.get("messages", []).copy()
        result_messages.append(error_response)
        
        return {
            "messages": result_messages,
            "_current_node": "tool_node"
        }

graph_builder.add_node("tools", tool_node_wrapper)

def route_tools(state: State) -> str:
    """Router: se tool_calls sono presenti, vai a tools, altrimenti END."""
    messages = state.get("messages", [])
    if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
        return "tools"
    return END

# Definisci la struttura del grafo
graph_builder.add_conditional_edges("chatbot", route_tools, {"tools": "tools", END: END})
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("tools", "chatbot")

# Compila il grafo con il checkpointer per la persistenza
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

sqlite_path = os.path.join(os.path.dirname(__file__), "chatbot_memory.sqlite")

def get_conn():
    return sqlite3.connect(sqlite_path, check_same_thread=False)

memory = SqliteSaver(conn=get_conn())
graph = graph_builder.compile(checkpointer=memory)


if __name__ == "__main__":
    print("Chatbot LangGraph con tool TavilySearch, memoria persistente e supervisione umana.")
    print("Scrivi 'exit' per uscire. Puoi cambiare thread digitando '/thread <id>' (default: 1)")
    thread_id = "1"
    from langgraph.types import Command
    # Carica la cronologia dell'ultimo snapshot del thread corrente (se esiste)
    config = {"configurable": {"thread_id": thread_id}}
    snapshots = list(graph.get_state_history(config))
    if snapshots:
        last_snapshot = snapshots[-1]
        state = last_snapshot.state.copy() if hasattr(last_snapshot, "state") else {"messages": []}
    else:
        state = {"messages": []}
    while True:
        user_input = input(f"[{thread_id}] Tu: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Arrivederci!")
            break
        if user_input.startswith("/thread"):
            try:
                thread_id = user_input.split()[1]
                print(f"[INFO] Cambiato thread_id: {thread_id}")
                config = {"configurable": {"thread_id": thread_id}}
                # Carica la cronologia dell'ultimo snapshot del nuovo thread (se esiste)
                snapshots = list(graph.get_state_history(config))
                if snapshots:
                    last_snapshot = snapshots[-1]
                    state = last_snapshot.state.copy() if hasattr(last_snapshot, "state") else {"messages": []}
                else:
                    state = {"messages": []}
            except Exception:
                print("[ERRORE] Usa: /thread <id>")
            continue
        if user_input.startswith("/rewind"):
            try:
                n = int(user_input.split()[1])
                print(f"[INFO] Eseguo rewind di {n} step...")
                snapshots = list(graph.get_state_history(config))
                if not snapshots:
                    print("[WARN] Nessuno snapshot disponibile per il rewind.")
                    continue
                target_idx = max(0, len(snapshots) - n)
                checkpoint = snapshots[target_idx]
                checkpoint_config = checkpoint.config if hasattr(checkpoint, "config") else config
                print(f"[INFO] Stato ripristinato al checkpoint {getattr(checkpoint, 'id', target_idx)} (step {target_idx+1} su {len(snapshots)})")
                print(json.dumps(checkpoint.state if hasattr(checkpoint, "state") else {}, indent=2, ensure_ascii=False))
                # Aggiorna la cronologia locale allo stato ripristinato
                state = checkpoint.state.copy() if hasattr(checkpoint, "state") else {"messages": []}
                # --- Offri scelta: sovrascrivi HEAD o crea branch ---
                print("\nVuoi [1] sovrascrivere la timeline (HEAD) oppure [2] creare un nuovo ramo (branch)?")
                scelta = input("[1]=sovrascrivi, [2]=branch: ").strip()
                if scelta == "2":
                    branch_name = input("Nome del nuovo branch (opzionale): ").strip()
                    branch_metadata = {"branch": branch_name} if branch_name else {}
                    branch_config = graph.update_state(
                        checkpoint_config,
                        {},
                    )
                    print(f"[BRANCH] Creato nuovo ramo{' \"' + branch_name + '\"' if branch_name else ''}. HEAD ora punta a questo branch.")
                    config = branch_config
                else:
                    new_config = graph.update_state(checkpoint_config, {})
                    print("[HEAD] Timeline sovrascritta: HEAD aggiornato su questo checkpoint.")
                    config = new_config
                continue
            except Exception as e:
                print(f"[ERRORE] Usa: /rewind <n>   Dettaglio: {e}")
            continue

        if user_input.startswith("/graph"):
            try:
                import graphviz
                config = {"configurable": {"thread_id": thread_id}}
                snapshots = list(graph.get_state_history(config))
                dot = graphviz.Digraph(comment='LangGraph Timeline')
                branch_colors = {}
                color_list = ["lightblue", "lightyellow", "lightpink", "lightgreen", "orange", "lightgray", "gold", "violet", "turquoise"]
                head_id = str(getattr(snapshots[-1], "id", id(snapshots[-1]))) if snapshots else None
                for i, snap in enumerate(snapshots):
                    node_id = str(getattr(snap, "id", id(snap)))
                    # Estrai nome branch e nodo corrente dai metadati
                    branch_name = None
                    node_name = "unknown"
                    if hasattr(snap, "config") and isinstance(snap.config, dict):
                        branch_name = snap.config.get("branch") or snap.config.get("configurable", {}).get("branch")
                    
                    # Estrai il nome del nodo usando la funzione dedicata
                    node_name = extract_node_name(snap)
                    # Mostra l'ultimo messaggio utente come etichetta
                    last_msg = f"[{node_name}] "
                    user_msgs = []
                    
                    # Debug: stampa la struttura completa dello snapshot
                    print(f"\n[GRAPH-DEBUG] Analisi nodo {node_id}")
                    print(f"[GRAPH-DEBUG] Tipo snap: {type(snap)}")
                    
                    # Stampa tutti gli attributi e metodi disponibili
                    print("[GRAPH-DEBUG] Attributi e metodi di snap:", dir(snap))
                    
                    # Prova a estrarre i messaggi in modo robusto
                    messages = []
                    
                    # 1. Prova con snap.values.messages
                    if hasattr(snap, "values") and hasattr(snap.values, "get"):
                        values = snap.values
                        if hasattr(values, "get"):
                            messages = values.get("messages", [])
                            if messages:
                                print(f"[GRAPH-DEBUG] Trovati {len(messages)} messaggi in snap.values.messages")
                    
                    # 2. Se non trovati, prova con _asdict
                    if not messages and hasattr(snap, "_asdict"):
                        try:
                            snap_dict = snap._asdict()
                            if "values" in snap_dict and isinstance(snap_dict["values"], dict):
                                messages = snap_dict["values"].get("messages", [])
                                if messages:
                                    print(f"[GRAPH-DEBUG] Trovati {len(messages)} messaggi in snap._asdict()['values']['messages']")
                        except Exception as e:
                            print(f"[GRAPH-DEBUG] Errore in _asdict: {e}")
                    
                    # 3. Se ancora non trovati, prova con __dict__
                    if not messages and hasattr(snap, "__dict__"):
                        snap_dict = vars(snap)
                        if "values" in snap_dict and hasattr(snap_dict["values"], "get"):
                            messages = snap_dict["values"].get("messages", [])
                            if messages:
                                print(f"[GRAPH-DEBUG] Trovati {len(messages)} messaggi in vars(snap)['values']['messages']")
                    
                    # Cerca l'ultimo messaggio utente
                    if messages:
                        for msg in reversed(messages):
                            try:
                                # Gestisci sia oggetti Message che dizionari
                                content = ""
                                is_human = False
                                
                                if hasattr(msg, "content") and hasattr(msg, "type"):
                                    # È un oggetto Message
                                    content = str(msg.content)
                                    is_human = msg.type == "human"
                                elif isinstance(msg, dict) and "content" in msg and "type" in msg:
                                    # È un dizionario con i campi di un messaggio
                                    content = str(msg["content"])
                                    is_human = msg.get("type") == "human"
                                
                                if is_human and content:
                                    last_msg += content[:50] + ("..." if len(content) > 50 else "")
                                    print(f"[GRAPH-DEBUG] Trovato messaggio utente: {last_msg}")
                                    break
                                    
                            except Exception as e:
                                print(f"[GRAPH-DEBUG] Errore nell'elaborazione del messaggio: {e}")
                        
                        # Estrai solo i messaggi utente univoci
                        seen_messages = set()
                        for msg in processed_msgs:
                            if not isinstance(msg, dict):
                                continue
                                
                            # Estrai il contenuto del messaggio
                            content = ''
                            if isinstance(msg.get('content'), str):
                                content = msg['content'].strip()
                            elif isinstance(msg.get('text'), str):
                                content = msg['text'].strip()
                            
                            # Verifica se è un messaggio utente
                            role = (msg.get('role', '') or msg.get('type', '')).lower()
                            is_user = role in ['user', 'human'] or any(
                                kw in (msg.get('content', '') or '').lower() 
                                for kw in ['user:', 'utente:', 'io:', 'dice:']
                            )
                            
                            if is_user and content and content not in seen_messages:
                                seen_messages.add(content)
                                user_msgs.append({'content': content, 'raw': msg})
                                print(f"[GRAPH-DEBUG] Aggiunto messaggio utente univoco: {content[:50]}...")
                        
                        print(f"[GRAPH-DEBUG] Nodo {node_id} - Messaggi utente univoci trovati: {len(user_msgs)}")
                        
                        # Prendi l'ultimo messaggio utente per l'etichetta
                        if user_msgs:
                            last_msg = user_msgs[-1]['content']
                            print(f"[GRAPH-DEBUG] Nodo {node_id} - Ultimo messaggio: {last_msg}")
                        else:
                            # Se non ci sono messaggi utente ma è lo stato iniziale, mostralo
                            if not msgs and i == len(snapshots) - 1:
                                last_msg = "[Stato Iniziale]"
                                print(f"[GRAPH-DEBUG] Nodo {node_id} - Rilevato stato iniziale")
                            else:
                                last_msg = "[Nessun messaggio utente]"
                                print(f"[GRAPH-DEBUG] Nodo {node_id} - Nessun messaggio utente trovato")
                    else:
                        # Gestisci il caso di stato iniziale o vuoto
                        if not msgs and i == len(snapshots) - 1:
                            last_msg = "[Stato Iniziale]"
                            print(f"[GRAPH-DEBUG] Nodo {node_id} - Rilevato stato iniziale (nessun messaggio)")
                        else:
                            last_msg = "[Nessun messaggio]"
                            print(f"[GRAPH-DEBUG] Nodo {node_id} - Nessun messaggio trovato")
                    
                    print(f"[GRAPH-DEBUG] Nodo {node_id} - Etichetta finale: {last_msg}")
                    
                    # Vecchio codice di debug, mantenuto per riferimento
                    if not user_msgs and 'msgs' in locals() and msgs:
                        print(f"[DEBUG] msgs vuoto o tipo inatteso: {type(msgs)} - {repr(msgs)}")
                    
                    print(f"[GRAPH-DEBUG] Nodo {node_id}: last_msg={last_msg}")
                    if last_msg and len(last_msg) > 40:
                        last_msg = last_msg[:37] + "..."
                    if not last_msg:
                        last_msg = "<nessun messaggio>"
                    label = f"{node_id}\n'{last_msg}'"
                    if branch_name:
                        label += f"\n[{branch_name}]"
                    node_color = None
                    if branch_name:
                        if branch_name not in branch_colors:
                            branch_colors[branch_name] = color_list[len(branch_colors) % len(color_list)]
                        node_color = branch_colors[branch_name]
                    node_label = f"{node_id}\n{node_name}"
                    if branch_name and branch_name != "main":
                        node_label += f"\nBranch: {branch_name}"
                    if last_msg.strip():
                        node_label += f"\n---\n{last_msg}"
                    
                    if node_id == head_id:
                        dot.node(node_id, node_label, shape="box", style="filled", fillcolor="lime", color="black", penwidth="2")
                    elif node_color:
                        dot.node(node_id, node_label, shape="box", style="filled", fillcolor=node_color)
                    else:
                        dot.node(node_id, node_label)
                    parent_id = getattr(snap, "parent_id", None)
                    if parent_id:
                        dot.edge(str(parent_id), node_id)
                print("[GRAPH] Grafo DOT della timeline/branch:")
                print(dot.source)
                dot.render('timeline.gv', view=True, format="png")
                print("[GRAPH] Esportato anche come timeline.gv.png")
            except ImportError:
                print("[ERRORE] Devi installare il pacchetto 'graphviz' (pip install graphviz) e Graphviz nel sistema per la visualizzazione del grafo.")
            except Exception as e:
                print(f"[ERRORE] Problema nella generazione del grafo: {e}")
            continue
        # Aggiungi il messaggio utente alla cronologia
        state["messages"].append({"role": "user", "content": user_input})
        print(f"[DEBUG] Cronologia AGGIORNATA (utente): {json.dumps(state['messages'], ensure_ascii=False)}")
        
        # Salva lo stato aggiornato
        graph.update_state(config, state)
        saved_state = graph.get_state(config)
        print(f"[DEBUG] Stato salvato (nodo: {state.get('_current_node')})")
        
        # Avvia lo streaming della risposta
        print("[DEBUG] Avvio streaming risposta...")
        events = graph.stream(state, config)
        print(f"[DEBUG] Tipo di events: {type(events)}")
        last_assistant_content = None
        needs_save = False
        event_count = 0
        last_node = None
        for event in events:
            event_count += 1
            
            # Log dettagliato di tutti i tipi di evento
            if hasattr(event, 'node'):
                # Evento di nodo
                current_node = event.node
                print(f"[GRAFO] Nodo: {current_node}")
                last_node = current_node
                
                # Se c'è un risultato dal nodo, loggalo
                if hasattr(event, 'result') and event.result is not None:
                    print(f"[GRAFO]   Risultato: {type(event.result).__name__}")
                
            elif isinstance(event, dict):
                # Log per i vari tipi di nodi basati su chiave
                node_types = [k for k in event.keys() if k not in ['messages']]
                for node_type in node_types:
                    print(f"[GRAFO] Nodo: {node_type}")
                    last_node = node_type
                    
                    # Log specifico per i tool
                    if node_type == 'tools' and 'messages' in event['tools']:
                        tool_msgs = event['tools']['messages']
                        tool_names = set()
                        for msg in tool_msgs:
                            if hasattr(msg, 'name'):
                                tool_names.add(msg.name)
                            elif hasattr(msg, 'tool'):
                                tool_names.add(msg.tool)
                        if tool_names:
                            # FIX: Filtra eventuali None prima di fare il join
                            valid_tool_names = [name for name in tool_names if name is not None]
                            if valid_tool_names:
                                print(f"[GRAFO]   Tool utilizzati: {', '.join(valid_tool_names)}")
                                if 'human_assistance' in valid_tool_names:
                                    print("[GRAFO]   Richiesta assistenza umana")
                        else:
                            print("[GRAFO]   Tool sconosciuto")
            
            # Log per le transizioni tra nodi
            if hasattr(event, 'source') and hasattr(event, 'target'):
                print(f"[GRAFO] Transizione: {event.source} -> {event.target}")
            
            # Log per errori
            if hasattr(event, 'error'):
                print(f"[GRAFO] ERRORE in {last_node}: {event.error}")
            
            # Estrai e mostra solo i messaggi dell'assistente (non i tool)
            if isinstance(event, dict) and 'chatbot' in event and 'messages' in event['chatbot']:
                messages = event['chatbot']['messages']
                if messages and isinstance(messages, list):
                    # Mostra solo i messaggi dell'assistente (ignora i ToolMessage)
                    assistant_msgs = [m for m in messages if getattr(m, 'type', '') != 'tool']
                    if assistant_msgs and hasattr(assistant_msgs[-1], 'content'):
                        print(f"\n[{thread_id}] Assistente: {assistant_msgs[-1].content}")
                        continue
            
            # Se non abbiamo ancora trovato la risposta, mostra i dettagli di debug
            # Log per le interruzioni (richieste di intervento umano)
            if isinstance(event, dict) and '__interrupt__' in event:
                interrupt_data = event['__interrupt__']
                if isinstance(interrupt_data, tuple) and len(interrupt_data) > 0:
                    query = getattr(interrupt_data[0], 'query', 'Nessuna query specificata')
                    print(f"\n[SUPERVISIONE UMANA] L'AI richiede assistenza umana!")
                    print(f"[DOMANDA] {query}")
                    human_msg = input("Inserisci la risposta: ")
                    print(f"[RISPOSTA] {human_msg}")
                    state["messages"].append({"role": "assistant", "content": human_msg})
                    print(f"[DEBUG] Cronologia AGGIORNATA (supervisione): {json.dumps(state['messages'], ensure_ascii=False)}")
                    continue
            if hasattr(event, "output") and event.output is not None:
                print(f"[DEBUG] Evento output ricevuto: {event.output}")
                # Aggiungi la risposta assistant alla cronologia SOLO se non è None
                last_assistant_content = getattr(event.output, "content", None)
                print(f"[DEBUG] Contenuto estratto: {last_assistant_content}")
                if last_assistant_content and (not state["messages"] or state["messages"][-1]["content"] != last_assistant_content):
                    state["messages"].append({"role": "assistant", "content": last_assistant_content})
                    print(f"[DEBUG] Cronologia AGGIORNATA (assistant): {json.dumps(state['messages'], ensure_ascii=False)}")
                    print(f"[{thread_id}] Assistente: {last_assistant_content}")
                    needs_save = True
        
        # Salva lo stato finale solo se ci sono stati aggiornamenti
        if last_assistant_content and not needs_save:
            # Se per qualsiasi motivo non è stato salvato prima, stampiamo comunque la risposta
            print(f"[{thread_id}] Assistente: {last_assistant_content}")
        if needs_save:
            graph.update_state(config, state)

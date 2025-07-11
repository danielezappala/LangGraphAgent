import os
from typing import Annotated, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from tools import tavily_tool, financial_advice_refusal, human_assistance, general_refusal, calculator
from langchain_mcp_adapters.client import MultiServerMCPClient

# Definisce lo stato del grafo. 
# 'messages' è una lista a cui vengono aggiunti nuovi messaggi.
class AgentState(dict):
    messages: Annotated[List[BaseMessage], add_messages]

async def build_graph(checkpointer: AsyncSqliteSaver):
    """
    Costruisce e compila il grafo dell'agente.

    Args:
        checkpointer: Un'istanza di AsyncSqliteSaver per la persistenza dello stato.

    Returns:
        Il grafo compilato e pronto per l'esecuzione.
    """
    # 1. Caricamento dei tool
    # Combina tool statici (definiti localmente) e dinamici (caricati da MCP)
    static_tools = [
        tavily_tool,
        financial_advice_refusal,
        human_assistance,
        general_refusal,
        calculator
    ]
    import json
    config_path = os.path.join(os.path.dirname(__file__), 'mcp_config.json')
    with open(config_path, 'r') as f:
        mcp_configs = json.load(f)
    mcp_client = MultiServerMCPClient(mcp_configs['mcpServers'])
    dynamic_tools = await mcp_client.get_tools()
    tools = static_tools + dynamic_tools

    # 2. Inizializzazione del modello LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    # Associa i tool al modello in modo che possa decidere quali chiamare
    llm_with_tools = llm.bind_tools(tools)

    # 3. Definizione dei nodi del grafo
    # Nodo principale: invoca l'LLM per ottenere una risposta o una chiamata a un tool
    def agent_node(state: AgentState):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    # Nodo secondario: esegue i tool chiamati dall'agente
    tool_node = ToolNode(tools)

    # 4. Definizione della logica di transizione (archi condizionali)
    # Decide se continuare l'esecuzione chiamando un tool o se terminare
    def should_continue(state: AgentState) -> str:
        if state["messages"][-1].tool_calls:
            return "tools"  # Se ci sono chiamate a tool, passa al nodo dei tool
        return "__end__"  # Altrimenti, termina il ciclo

    # 5. Costruzione e compilazione del grafo
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")  # Dopo l'esecuzione dei tool, torna all'agente

    # Compila il grafo e lo associa al checkpointer per la persistenza
    graph = workflow.compile(checkpointer=checkpointer)
    return graph

import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import TypedDict, Annotated, List
import operator
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END

# Definiamo esplicitamente lo stato dell'agente per evitare problemi di importazione
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

from .tools import tavily_tool, financial_advice_refusal, human_assistance, general_refusal, calculator
from .mcp_adapter import load_mcp_tools

async def build_graph(checkpointer):
    """
    Costruisce e compila il grafo con un agente personalizzato per garantire
    il corretto flusso di esecuzione asincrona.
    """
    # Carica i tool statici e quelli dinamici dal server MCP
    static_tools = [tavily_tool, financial_advice_refusal, human_assistance, general_refusal, calculator]
    mcp_tools = await load_mcp_tools()
    tools = mcp_tools + static_tools
    
    SYSTEM_PROMPT = (
        "You are a helpful assistant with access to a set of tools. Your main goal is to help the user with their requests."
        "When the user mentions 'Notion', you must use the provided Notion tools."
        
        "**VERY IMPORTANT RULE**: If the user wants to add content to a page or modify it (e.g., add notes, change title), you MUST follow this sequence and you CANNOT skip any step:"
        "1. **SEARCH**: First, you MUST use the 'API-post-search' tool to find the page by its title. This will give you the essential 'page_id'."
        "2. **VALIDATE**: Check the result from the search. If you found a page, you will have its 'page_id'."
        "3. **EXECUTE**: Only if you have a valid 'page_id' from the previous step, you can then use 'API-patch-block-children' to add content or 'API-patch-page' to modify the page properties."
        
        "You are strictly forbidden from calling 'API-patch-block-children' or 'API-patch-page' without a 'page_id' that you have obtained from a previous 'API-post-search' call."
        "If you don't have the page_id, your only option is to search for it first."
    )
    
    # Definisci il modello LLM e il prompt
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    # Associa i tool e il prompt al modello
    llm_with_tools = model.bind_tools(tools)
    runnable_agent = prompt | llm_with_tools

    # --- Nodi del Grafo Personalizzato ---

    # 1. Nodo Agente: invoca l'LLM per decidere la prossima azione
    def agent_node(state: AgentState):
        response = runnable_agent.invoke(state)
        return {"messages": [response]}

    # 2. Nodo Tool: esegue i tool richiesti dall'agente
    async def tool_node(state: AgentState) -> dict:
        messages = []
        last_message = state['messages'][-1]
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            found_tool = next((t for t in tools if t.name == tool_name), None)
            if not found_tool:
                messages.append(ToolMessage(content=f"Error: Tool '{tool_name}' not found.", tool_call_id=tool_call["id"]))
                continue
            try:
                output = await found_tool.ainvoke(tool_call["args"])
                messages.append(ToolMessage(content=str(output), tool_call_id=tool_call["id"]))
            except Exception as e:
                messages.append(ToolMessage(content=f"Error executing tool {tool_name}: {e}", tool_call_id=tool_call["id"]))
        return {"messages": messages}

    # --- Costruzione del Grafo ---
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    # Bordo condizionale: decide se chiamare i tool o terminare
    def should_continue(state):
        return "tools" if state["messages"][-1].tool_calls else "end"

    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")
    graph.set_entry_point("agent")

    # Compila il grafo con il checkpointer
    return graph.compile(checkpointer=checkpointer)

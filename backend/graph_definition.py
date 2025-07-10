import json
import os
import pathlib
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, BaseMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

# Definiamo esplicitamente lo stato dell'agente per evitare problemi di importazione
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

from tools import tavily_tool, financial_advice_refusal, human_assistance, general_refusal, calculator
from langchain_mcp_adapters.client import MultiServerMCPClient

async def build_graph(checkpointer):
    """
    Costruisce e compila il grafo con un agente personalizzato per garantire
    il corretto flusso di esecuzione asincrona.
    """
    # Carica i tool statici e quelli dinamici dal server MCP
    static_tools = [tavily_tool, financial_advice_refusal, human_assistance, general_refusal, calculator]
    # Carica le variabili d'ambiente dal file .env
    dotenv_path = pathlib.Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=dotenv_path)

    # Carica dinamicamente la configurazione del server MCP e inserisci la chiave API di Notion
    notion_api_key = os.getenv("NOTION_API_KEY")
    if not notion_api_key:
        raise RuntimeError("NOTION_API_KEY non trovata nel file .env")

    config_path = pathlib.Path(__file__).parent / "mcp_config.json"
    mcp_config = json.loads(config_path.read_text())
    
    # Inserisci dinamicamente la chiave API di Notion nella configurazione
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Notion-Version": "2022-06-28"
    }
    mcp_config["mcpServers"]["notionApi"]["env"]["OPENAPI_MCP_HEADERS"] = json.dumps(headers)

    # Inizializzazione del client MCP in base all'ambiente
    mcp_server_url = os.getenv("MCP_SERVER_URL")

    if mcp_server_url:
        print(f"Connessione al server MCP remoto: {mcp_server_url}")
        # In produzione, ci si connette a un URL remoto
        client = MultiServerMCPClient(mcp_server_url=mcp_server_url)
    else:
        print("Avvio del server MCP locale dalla configurazione.")
        # In locale, si usa il file di configurazione per avviare il server
        config_path = os.path.join(os.path.dirname(__file__), "mcp_config.json")
        client = MultiServerMCPClient(config_path=config_path)

    # Creazione del toolkit MCP
    mcp_tools = await client.get_tools()
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

        "\n**Content Presentation Rules**:\n"
        "- When you describe the content of a Notion page, you MUST ignore any empty elements like empty paragraphs or empty blocks."
        "- List only the items that have actual content, such as text, images, or child pages."
        "- Be concise and clear in your summary."
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

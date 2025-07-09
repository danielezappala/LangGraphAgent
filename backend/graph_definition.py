import asyncio
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

from .tools import tavily_tool, financial_advice_refusal, human_assistance, general_refusal, calculator
from .mcp_adapter import load_mcp_tools

async def build_graph(checkpointer):
    """
    Costruisce e compila il grafo utilizzando la funzione pre-costruita 
    `create_react_agent` per un'implementazione robusta e semplificata.
    """
    # Definisci i tool che l'agente può usare
    # Carica i tool statici e quelli dinamici dal server MCP
    static_tools = [tavily_tool, financial_advice_refusal, human_assistance, general_refusal, calculator]
    mcp_tools = await load_mcp_tools()
    tools = mcp_tools + static_tools
    
    SYSTEM_PROMPT = (
        "You are an expert assistant who is masterful at using tools to answer user questions. "
        "Your primary goal is to select and use the most appropriate tool based on the user's query. "
        "If a user's request can be answered by one of your tools, you MUST use that tool instead of asking for human assistance. "
        "Specifically, when the user mentions 'Notion' or asks to find or search for something, use one of the Notion tools. "
        "The 'API-post-search' tool is used to search for pages in Notion by title. "
        "Be decisive and act without asking for clarification."
    )
    
    # Definisci il modello LLM
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Crea un prompt template personalizzato che include il system prompt
    from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    # Crea l'agente usando la funzione pre-costruita
    # Questo si occupa di tutta la logica interna del grafo
    graph = create_react_agent(
        model,  # Usa il modello originale
        tools,
        prompt=prompt,  # Passa il prompt personalizzato
        checkpointer=checkpointer
    )
    
    return graph

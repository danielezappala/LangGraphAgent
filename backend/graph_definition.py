from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from .tools import tavily_tool, financial_advice_refusal, human_assistance, general_refusal, calculator

def build_graph(checkpointer):
    """
    Costruisce e compila il grafo utilizzando la funzione pre-costruita 
    `create_react_agent` per un'implementazione robusta e semplificata.
    """
    # Definisci i tool che l'agente può usare
    tools = [tavily_tool, financial_advice_refusal, human_assistance, general_refusal, calculator]
    
    # Definisci il modello LLM
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Crea l'agente usando la funzione pre-costruita
    # Questo si occupa di tutta la logica interna del grafo
    graph = create_react_agent(model, tools, checkpointer=checkpointer)
    
    return graph

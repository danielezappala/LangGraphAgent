import os
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain_core.tools import tool

# Carica le variabili d'ambiente dal file .env
# Questo assicura che le chiavi API siano disponibili non appena i tool vengono importati
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

# Validazione delle chiavi API
if not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"):
    raise RuntimeError("Assicurati che OPENAI_API_KEY e TAVILY_API_KEY siano nel file .env")

import numexpr

@tool
def search_web(query: str) -> str:
    """Searches the web for information about a given query."""
    tavily = TavilySearch(max_results=2)
    return tavily.invoke(query)

# 2. Human Assistance Tool
@tool
def general_refusal(query: str) -> str:
    """
    Use this as a last resort if the user asks for advice on sensitive topics like medical, legal, or other high-stakes areas for which a specific refusal tool does not exist. This tool provides a general, polite refusal.
    The input query should be the user's original question.
    """
    return (
        "Mi dispiace, ma non posso fornire consigli su questo argomento. Per questioni importanti o che richiedono competenze specifiche, è sempre meglio consultare un professionista del settore."
    )


@tool
def human_assistance(query: str) -> str:
    """
    Use this tool when you need to ask for human help or clarification on something.
    The user will provide an answer.
    """
    # In this CLI example, we just return a confirmation that the request was noted.
    # In a real app, this would trigger a notification to a human operator.
    print(f'\n[ASSISTENZA UMANA RICHIESTA] L\'assistente chiede: "{query}"\n')
    return "Richiesta di assistenza umana registrata. Un operatore prenderà in carico la richiesta."

@tool
def calculator(expression: str) -> str:
    """
    Use this tool to evaluate a mathematical expression.
    The input should be a valid mathematical expression (e.g., '2 + 2', '7 * (4 / 2)').
    It returns the numerical result.
    """
    try:
        # Using numexpr is safer than eval() for mathematical expressions
        result = numexpr.evaluate(expression).item()
        return f"Il risultato dell'espressione '{expression}' è {result}."
    except Exception as e:
        return f"Errore nella valutazione dell'espressione '{expression}': {e}. Per favore, fornisci un'espressione matematica valida."

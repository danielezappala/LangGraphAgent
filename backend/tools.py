from langchain_tavily import TavilySearch
from langchain_core.tools import tool

import numexpr

# Definisci i tool che l'agente può usare
tavily_tool = TavilySearch(max_results=2)

@tool
def financial_advice_refusal(query: str) -> str:
    """
    Use this tool when the user asks for financial advice, investment suggestions, 
    stock picks, or any topic related to personal finance where providing advice would be 
    inappropriate or risky. This tool provides a standard refusal response.
    The input query should be the user's original question.
    """
    return (
        "Non sono un consulente finanziario e non posso fornire consigli di investimento. "
        "Per decisioni finanziarie importanti, è sempre meglio consultare un professionista qualificato."
    )

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

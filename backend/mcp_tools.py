import re
from datetime import datetime
from typing import Dict, Any, Optional

# MCP request/response schema (simple, no Pydantic for testability)
def parse_weather_request(message: str) -> Optional[Dict[str, Any]]:
    """
    Estrae città e data da una richiesta meteo in linguaggio naturale.
    Ritorna un dict MCP-style oppure None se non matcha.
    """
    # Pattern: "tempo a [città] il [data]"
    match = re.search(r"tempo.*a ([\w\s]+) il (\d{1,2} \w+)", message, re.IGNORECASE)
    if match:
        city = match.group(1).strip()
        date_str = match.group(2).strip()
        # Tenta conversione in ISO date
        try:
            date = datetime.strptime(date_str, "%d %B").replace(year=datetime.now().year).date().isoformat()
        except Exception:
            date = date_str
        return {
            "tool": "weather",
            "input": {
                "city": city,
                "date": date
            },
            "context": {}
        }
    return None

def weather_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool meteo mock: restituisce una risposta MCP-style
    """
    city = input_data.get("city", "?")
    date = input_data.get("date", "?")
    # Qui puoi collegare una vera API meteo
    return {
        "city": city,
        "date": date,
        "forecast": f"Soleggiato a {city} il {date}, 29°C"
    }

def calendar_tool(input_data: Dict[str, Any]) -> str:
    """
    Tool agenda mock: restituisce una risposta fittizia sull'agenda.
    """
    # Puoi personalizzare la logica qui
    return "La tua agenda per oggi: call alle 10, pranzo alle 13, meeting alle 15."

def recipe_tool(input_data: Dict[str, Any]) -> str:
    """
    Tool ricette mock: restituisce una ricetta fittizia.
    """
    ingredient = input_data.get("ingredient", "pasta") if isinstance(input_data, dict) else "pasta"
    return f"Ricetta consigliata: {ingredient} al pomodoro."

def handle_mcp(message: str) -> Optional[Dict[str, Any]]:
    """
    Pipeline: da messaggio discorsivo a MCP response (solo meteo demo)
    """
    mcp_req = parse_weather_request(message)
    if mcp_req and mcp_req["tool"] == "weather":
        output = weather_tool(mcp_req["input"])
        return {
            "tool": "weather",
            "output": output
        }
    return None

import pytest
from mcp_tools import parse_weather_request, weather_tool, handle_mcp

def test_parse_weather_request_match():
    msg = "Che tempo farà a Milano il 5 luglio?"
    mcp = parse_weather_request(msg)
    assert mcp is not None
    assert mcp["tool"] == "weather"
    assert mcp["input"]["city"].lower() == "milano"
    assert mcp["input"]["date"].startswith("2025-07-05") or mcp["input"]["date"].endswith("luglio")

def test_parse_weather_request_no_match():
    msg = "Qual è la capitale della Francia?"
    mcp = parse_weather_request(msg)
    assert mcp is None

def test_weather_tool_mock():
    input_data = {"city": "Roma", "date": "2025-08-01"}
    out = weather_tool(input_data)
    assert out["city"] == "Roma"
    assert out["date"] == "2025-08-01"
    assert "Soleggiato" in out["forecast"]

def test_handle_mcp_full_pipeline():
    msg = "Vorrei sapere che tempo fa a Napoli il 10 luglio"
    resp = handle_mcp(msg)
    assert resp is not None
    assert resp["tool"] == "weather"
    assert resp["output"]["city"].lower() == "napoli"
    assert "forecast" in resp["output"]

def test_handle_mcp_no_tool():
    msg = "Raccontami una barzelletta"
    resp = handle_mcp(msg)
    assert resp is None

import pytest
from fastapi.testclient import TestClient
from backend.api_server import app

client = TestClient(app)

def test_chat_endpoint():
    response = client.post("/chat", json={"message": "Ciao, chi sei?"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0 
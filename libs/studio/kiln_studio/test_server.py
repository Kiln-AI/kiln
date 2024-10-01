from unittest.mock import patch

import pytest
import requests
from fastapi.testclient import TestClient

from libs.studio.kiln_studio.server import app

client = TestClient(app)


def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == "pong"


def test_connect_ollama_success():
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "models": [{"model": "model1"}, {"model": "model2"}]
        }
        response = client.post("/provider/ollama/connect")
        assert response.status_code == 200
        assert response.json() == {
            "message": "Ollama connected",
            "models": ["model1", "model2"],
        }


def test_connect_ollama_connection_error():
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError
        response = client.post("/provider/ollama/connect")
        assert response.status_code == 417
        assert response.json() == {
            "message": "Failed to connect to Ollama. Ensure Ollama app is running."
        }


def test_connect_ollama_general_exception():
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Test exception")
        response = client.post("/provider/ollama/connect")
        assert response.status_code == 500
        assert response.json() == {
            "message": "Failed to connect to Ollama: Test exception"
        }


def test_connect_ollama_no_models():
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"models": []}
        response = client.post("/provider/ollama/connect")
        assert response.status_code == 417
        assert response.json() == {
            "message": "Ollama not connected, or no Ollama models installed."
        }


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "https://localhost:8443",
        "https://127.0.0.1:8443",
    ],
)
def test_cors_allowed_origins(origin):
    response = client.get("/ping", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize(
    "origin",
    [
        "http://example.com",
        "https://kiln-ai.com",
        "http://192.168.1.100",
        "http://localhost.com",
        "http://127.0.0.2",
        "http://127.0.0.2.com",
    ],
)
def test_cors_blocked_origins(origin):
    response = client.get("/ping", headers={"Origin": origin})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_no_origin():
    response = client.get("/")
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from kiln_ai.utils.config import Config

from libs.studio.kiln_studio.provider_api import (
    connect_groq,
    connect_openrouter,
    connect_provider_api,
)


@pytest.fixture
def app():
    app = FastAPI()
    connect_provider_api(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_connect_api_key_invalid_payload(client):
    response = client.post(
        "/api/provider/connect_api_key",
        json={"provider": "openai", "key_data": "invalid"},
    )
    assert response.status_code == 400
    assert response.json() == {"message": "Invalid key_data or provider"}


def test_connect_api_key_unsupported_provider(client):
    response = client.post(
        "/api/provider/connect_api_key",
        json={"provider": "unsupported", "key_data": {"API Key": "test"}},
    )
    assert response.status_code == 400
    assert response.json() == {"message": "Provider unsupported not supported"}


@patch("libs.studio.kiln_studio.provider_api.connect_openai")
def test_connect_api_key_openai_success(mock_connect_openai, client):
    mock_connect_openai.return_value = {"message": "Connected to OpenAI"}
    response = client.post(
        "/api/provider/connect_api_key",
        json={"provider": "openai", "key_data": {"API Key": "test_key"}},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Connected to OpenAI"}
    mock_connect_openai.assert_called_once_with("test_key")


@patch("libs.studio.kiln_studio.provider_api.requests.get")
@patch("libs.studio.kiln_studio.provider_api.Config.shared")
def test_connect_openai_success(mock_config_shared, mock_requests_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests_get.return_value = mock_response

    mock_config = MagicMock()
    mock_config_shared.return_value = mock_config

    response = client.post(
        "/api/provider/connect_api_key",
        json={"provider": "openai", "key_data": {"API Key": "test_key"}},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Connected to OpenAI"}
    assert mock_config.open_ai_api_key == "test_key"


@patch("libs.studio.kiln_studio.provider_api.requests.get")
def test_connect_openai_invalid_key(mock_requests_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_requests_get.return_value = mock_response

    response = client.post(
        "/api/provider/connect_api_key",
        json={"provider": "openai", "key_data": {"API Key": "invalid_key"}},
    )

    assert response.status_code == 401
    assert response.json() == {
        "message": "Failed to connect to OpenAI. Invalid API key."
    }


@patch("libs.studio.kiln_studio.provider_api.requests.get")
def test_connect_openai_request_exception(mock_requests_get, client):
    mock_requests_get.side_effect = Exception("Test error")

    response = client.post(
        "/api/provider/connect_api_key",
        json={"provider": "openai", "key_data": {"API Key": "test_key"}},
    )

    assert response.status_code == 400
    assert "Failed to connect to OpenAI. Error:" in response.json()["message"]


@pytest.fixture
def mock_requests_get():
    with patch("libs.studio.kiln_studio.provider_api.requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_config():
    with patch("libs.studio.kiln_studio.provider_api.Config") as mock_config:
        mock_config.shared.return_value = MagicMock()
        yield mock_config


@patch("libs.studio.kiln_studio.provider_api.requests.get")
@patch("libs.studio.kiln_studio.provider_api.Config.shared")
async def test_connect_groq_success(mock_config_shared, mock_requests_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"models": []}'
    mock_requests_get.return_value = mock_response

    mock_config = MagicMock()
    mock_config_shared.return_value = mock_config

    assert mock_config.shared.return_value.groq_api_key != "test_api_key"
    result = await connect_groq("test_api_key")

    assert result.status_code == 200
    assert result.body == b'{"message":"Connected to Groq"}'
    mock_config.shared.return_value.groq_api_key = "test_api_key"
    mock_requests_get.assert_called_once_with(
        "https://api.groq.com/openai/v1/models",
        headers={
            "Authorization": "Bearer test_api_key",
            "Content-Type": "application/json",
        },
    )
    assert mock_config.shared.return_value.groq_api_key == "test_api_key"


async def test_connect_groq_invalid_api_key(mock_requests_get):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "{a:'invalid_api_key'}"
    mock_requests_get.return_value = mock_response

    result = await connect_groq("invalid_key")

    assert result.status_code == 401
    response_data = json.loads(result.body)
    assert "Invalid API key" in response_data["message"]


async def test_connect_groq_request_error(mock_requests_get):
    mock_requests_get.side_effect = Exception("Connection error")

    result = await connect_groq("test_api_key")

    assert result.status_code == 400
    response_data = json.loads(result.body)
    assert "Failed to connect to Groq" in response_data["message"]


async def test_connect_groq_non_200_response(mock_requests_get):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = Exception("Server error")
    mock_requests_get.return_value = mock_response

    result = await connect_groq("test_api_key")

    assert result.status_code == 400
    response_data = json.loads(result.body)
    assert "Failed to connect to Groq" in response_data["message"]


@pytest.mark.asyncio
async def test_connect_openrouter():
    # Test case 1: Valid API key
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = (
            400  # Simulating an expected error due to empty body
        )
        mock_post.return_value = mock_response

        result = await connect_openrouter("valid_api_key")
        assert result.status_code == 200
        assert result.body == b'{"message":"Connected to OpenRouter"}'
        assert Config.shared().open_router_api_key == "valid_api_key"

    # Test case 2: Invalid API key
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        result = await connect_openrouter("invalid_api_key")
        assert result.status_code == 401
        assert (
            result.body
            == b'{"message":"Failed to connect to OpenRouter. Invalid API key."}'
        )
        assert Config.shared().open_router_api_key != "invalid_api_key"

    # Test case 3: Unexpected error
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("Unexpected error")

        result = await connect_openrouter("api_key")
        assert result.status_code == 400
        assert (
            b"Failed to connect to OpenRouter. Error: Unexpected error" in result.body
        )
        assert Config.shared().open_router_api_key != "api_key"

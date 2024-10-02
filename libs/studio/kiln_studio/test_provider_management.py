from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from libs.studio.kiln_studio.provider_management import connect_provider_management


@pytest.fixture
def app():
    app = FastAPI()
    connect_provider_management(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_connect_api_key_invalid_payload(client):
    response = client.post(
        "/provider/connect_api_key", json={"provider": "openai", "key_data": "invalid"}
    )
    assert response.status_code == 400
    assert response.json() == {"message": "Invalid key_data or provider"}


def test_connect_api_key_unsupported_provider(client):
    response = client.post(
        "/provider/connect_api_key",
        json={"provider": "unsupported", "key_data": {"API Key": "test"}},
    )
    assert response.status_code == 400
    assert response.json() == {"message": "Provider unsupported not supported"}


@patch("libs.studio.kiln_studio.provider_management.connect_openai")
def test_connect_api_key_openai_success(mock_connect_openai, client):
    mock_connect_openai.return_value = {"message": "Connected to OpenAI"}
    response = client.post(
        "/provider/connect_api_key",
        json={"provider": "openai", "key_data": {"API Key": "test_key"}},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Connected to OpenAI"}
    mock_connect_openai.assert_called_once_with("test_key")


@patch("libs.studio.kiln_studio.provider_management.requests.get")
@patch("libs.studio.kiln_studio.provider_management.Config.shared")
def test_connect_openai_success(mock_config_shared, mock_requests_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests_get.return_value = mock_response

    mock_config = MagicMock()
    mock_config_shared.return_value = mock_config

    response = client.post(
        "/provider/connect_api_key",
        json={"provider": "openai", "key_data": {"API Key": "test_key"}},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Connected to OpenAI"}
    assert mock_config.open_ai_api_key == "test_key"


@patch("libs.studio.kiln_studio.provider_management.requests.get")
def test_connect_openai_invalid_key(mock_requests_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_requests_get.return_value = mock_response

    response = client.post(
        "/provider/connect_api_key",
        json={"provider": "openai", "key_data": {"API Key": "invalid_key"}},
    )

    assert response.status_code == 401
    assert response.json() == {
        "message": "Failed to connect to OpenAI. Invalid API key."
    }


@patch("libs.studio.kiln_studio.provider_management.requests.get")
def test_connect_openai_request_exception(mock_requests_get, client):
    mock_requests_get.side_effect = Exception("Test error")

    response = client.post(
        "/provider/connect_api_key",
        json={"provider": "openai", "key_data": {"API Key": "test_key"}},
    )

    assert response.status_code == 400
    assert (
        "Failed to connect to OpenAI. Likely invalid API key. Error:"
        in response.json()["message"]
    )

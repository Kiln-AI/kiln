import os

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
from kiln_studio.settings import connect_settings, load_settings, settings_path


@pytest.fixture
def temp_home(tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda x: str(tmp_path))
    return tmp_path


@pytest.fixture
def app():
    app = FastAPI()
    connect_settings(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_settings_path(temp_home):
    expected_path = os.path.join(temp_home, ".kiln_ai", "settings.yaml")
    assert settings_path() == expected_path
    assert os.path.exists(os.path.dirname(expected_path))


def test_load_settings_empty(temp_home):
    assert load_settings() == {}


def test_load_settings_existing(temp_home):
    settings_file = settings_path()
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    test_settings = {"key": "value"}
    with open(settings_file, "w") as f:
        yaml.dump(test_settings, f)

    assert load_settings() == test_settings


def test_update_settings(client, temp_home):
    new_settings = {"test_key": "test_value"}
    response = client.post("/setting", json=new_settings)
    assert response.status_code == 200
    assert response.json() == {"message": "Settings updated"}

    # Verify the settings were actually updated
    with open(settings_path(), "r") as f:
        saved_settings = yaml.safe_load(f)
    assert saved_settings == new_settings


def test_read_settings(client, temp_home):
    test_settings = {"key1": "value1", "key2": 42}
    with open(settings_path(), "w") as f:
        yaml.dump(test_settings, f)

    response = client.get("/settings")
    assert response.status_code == 200
    assert response.json() == test_settings


def test_read_item(client):
    response = client.get("/items/42")
    assert response.status_code == 200
    assert response.json() == {"item_id": 42}

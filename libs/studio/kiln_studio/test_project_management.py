import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from libs.core.kiln_ai.datamodel import Project
from libs.core.kiln_ai.utils.config import Config
from libs.studio.kiln_studio.project_management import (
    connect_project_management,
    default_project_path,
)


@pytest.fixture
def app():
    app = FastAPI()
    connect_project_management(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_create_project_success(client):
    with patch("os.path.exists", return_value=False), patch("os.makedirs"), patch(
        "libs.core.kiln_ai.datamodel.Project.save_to_file"
    ):
        response = client.post(
            "/api/project",
            json={
                "name": "Test Project",
                "description": "A test project",
            },
        )

    assert response.status_code == 200
    res = response.json()
    assert res["name"] == "Test Project"
    assert res["description"] == "A test project"
    assert res["path"] == os.path.join(
        default_project_path(), "Test Project", "project.json"
    )
    assert res["v"] == 1
    assert res["model_type"] == "project"
    assert res["created_by"] == Config.shared().user_id
    assert res["created_at"] is not None


def test_create_project_missing_name(client):
    response = client.post("/api/project", json={"description": "A test project"})

    assert response.status_code == 422
    assert '"Field required"' in response.text


def test_create_project_invalid_description(client):
    response = client.post(
        "/api/project",
        json={"name": "Test Project", "description": 123},
    )

    assert response.status_code == 422
    assert "Input should be a valid string" in response.text


def test_create_project_existing_name(client):
    with patch("os.path.exists", return_value=True):
        response = client.post(
            "/api/project",
            json={
                "name": "Existing Project",
                "description": "This project already exists",
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "message": "Project with this name already exists. Please choose a different name."
    }


def test_create_and_load_project(client):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the default_project_path to use our temporary directory
        with patch(
            "libs.studio.kiln_studio.project_management.default_project_path",
            return_value=temp_dir,
        ):
            # Create a new project
            response = client.post(
                "/api/project",
                json={
                    "name": "Test Project",
                    "description": "A test project description",
                },
            )

            assert response.status_code == 200
            res = response.json()
            assert res["name"] == "Test Project"
            assert res["description"] == "A test project description"
            assert res["path"] == os.path.join(temp_dir, "Test Project", "project.json")
            assert res["v"] == 1
            assert res["model_type"] == "project"
            assert res["created_by"] == Config.shared().user_id
            assert res["created_at"] is not None

            # Verify the project file was created
            project_path = os.path.join(temp_dir, "Test Project")
            project_file = os.path.join(project_path, "project.json")
            assert os.path.exists(project_path)
            assert os.path.isfile(project_file)

            # Load the project and verify its contents
            loaded_project = Project.load_from_file(project_file)
            assert loaded_project.name == "Test Project"
            assert loaded_project.description == "A test project description"

            # Verify the project is in the list of projects
            assert project_file in Config.shared().projects
            assert Config.shared().current_project == project_file

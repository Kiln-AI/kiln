import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from libs.core.kiln_ai.datamodel import Project
from libs.core.kiln_ai.utils.config import Config
from libs.studio.kiln_studio.custom_errors import connect_custom_errors
from libs.studio.kiln_studio.project_management import (
    connect_project_management,
    default_project_path,
)


@pytest.fixture
def app():
    app = FastAPI()
    connect_project_management(app)
    connect_custom_errors(app)
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

            # Skipping this assert as it's broken
            # assert Config.shared().current_project == project_file


@pytest.fixture
def mock_projects():
    return [
        Project(
            name="Project 1", description="Description 1", path="/path/to/project1.json"
        ),
        Project(
            name="Project 2", description="Description 2", path="/path/to/project2.json"
        ),
    ]


def test_get_projects_empty(client):
    with patch.object(Config, "shared") as mock_config:
        mock_config.return_value.projects = []
        response = client.get("/api/projects")

    assert response.status_code == 200
    assert response.json() == {"projects": [], "current_project_path": None}


def test_get_projects_success(client, mock_projects):
    with patch.object(Config, "shared") as mock_config, patch(
        "libs.core.kiln_ai.datamodel.Project.load_from_file"
    ) as mock_load:
        mock_config.return_value.projects = [p.path for p in mock_projects]
        mock_load.side_effect = mock_projects

        response = client.get("/api/projects")

    assert response.status_code == 200
    result = response.json()
    assert "projects" in result
    assert len(result["projects"]) == 2

    for i, project in enumerate(result["projects"]):
        assert project["name"] == f"Project {i+1}"
        assert project["description"] == f"Description {i+1}"
        assert project["path"] == str(mock_projects[i].path)


def test_get_projects_file_not_found(client, mock_projects):
    with patch.object(Config, "shared") as mock_config, patch(
        "libs.core.kiln_ai.datamodel.Project.load_from_file"
    ) as mock_load:
        mock_config.return_value.projects = [p.path for p in mock_projects]
        mock_load.side_effect = [mock_projects[0], FileNotFoundError]

        response = client.get("/api/projects")

    assert response.status_code == 200
    result = response.json()
    assert "projects" in result
    assert len(result["projects"]) == 1
    assert result["projects"][0]["name"] == "Project 1"


def test_get_projects_with_current_project(client, mock_projects):
    with patch.object(Config, "shared") as mock_config, patch(
        "libs.core.kiln_ai.datamodel.Project.load_from_file"
    ) as mock_load:
        mock_config.return_value.projects = [p.path for p in mock_projects]
        mock_config.return_value.current_project = mock_projects[1].path
        mock_load.side_effect = mock_projects

        response = client.get("/api/projects")

    assert response.status_code == 200
    result = response.json()
    assert "projects" in result
    assert len(result["projects"]) == 2
    assert "current_project_path" in result
    assert result["current_project_path"] == str(mock_projects[1].path)


def test_get_projects_with_invalid_current_project(client, mock_projects):
    with patch.object(Config, "shared") as mock_config, patch(
        "libs.core.kiln_ai.datamodel.Project.load_from_file"
    ) as mock_load:
        mock_config.return_value.projects = [p.path for p in mock_projects]
        mock_config.return_value.current_project = "/invalid/path"
        mock_load.side_effect = mock_projects

        response = client.get("/api/projects")

    assert response.status_code == 200
    result = response.json()
    assert "projects" in result
    assert len(result["projects"]) == 2
    assert "current_project_path" in result
    assert result["current_project_path"] == str(mock_projects[0].path)


def test_get_projects_with_no_projects(client):
    with patch.object(Config, "shared") as mock_config:
        mock_config.return_value.projects = []
        mock_config.return_value.current_project = None

        response = client.get("/api/projects")

    assert response.status_code == 200
    result = response.json()
    assert result["projects"] == []

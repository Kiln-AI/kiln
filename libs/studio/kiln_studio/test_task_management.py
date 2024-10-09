from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from libs.core.kiln_ai.datamodel import Project, Task
from libs.studio.kiln_studio.custom_errors import connect_custom_errors
from libs.studio.kiln_studio.task_management import connect_task_management


@pytest.fixture
def app():
    app = FastAPI()
    connect_task_management(app)
    connect_custom_errors(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_create_task_success(client, tmp_path):
    project_path = tmp_path / "test_project"
    project_path.mkdir()

    task_data = {
        "name": "Test Task",
        "description": "This is a test task",
        "instruction": "This is a test instruction",
    }

    with patch(
        "libs.core.kiln_ai.datamodel.Project.load_from_file"
    ) as mock_load, patch("libs.core.kiln_ai.datamodel.Task.save_to_file") as mock_save:
        mock_load.return_value = Project(name="Test Project")
        mock_save.return_value = None

        response = client.post(f"/api/task?project_path={project_path}", json=task_data)

    assert response.status_code == 200
    res = response.json()
    assert res["name"] == "Test Task"
    assert res["description"] == "This is a test task"
    assert "path" in res
    assert res["id"] is not None
    assert res["priority"] == 2


def test_create_task_project_not_found(client, tmp_path):
    non_existent_path = tmp_path / "non_existent"

    task_data = {
        "name": "Test Task",
        "description": "This is a test task",
    }

    response = client.post(
        f"/api/task?project_path={non_existent_path}", json=task_data
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Parent project not found. Can't create task."


def test_create_task_project_load_error(client, tmp_path):
    project_path = tmp_path / "test_project"
    project_path.mkdir()

    task_data = {
        "name": "Test Task",
        "description": "This is a test task",
    }

    with patch("libs.core.kiln_ai.datamodel.Project.load_from_file") as mock_load:
        mock_load.side_effect = Exception("Failed to load project")

        response = client.post(f"/api/task?project_path={project_path}", json=task_data)

    assert response.status_code == 500
    assert "Failed to load parent project" in response.json()["message"]


def test_create_task_real_project(client, tmp_path):
    project_path = tmp_path / "real_project" / Project.base_filename()
    project_path.parent.mkdir()

    # Create a real Project
    project = Project(name="Real Project", path=str(project_path))
    project.save_to_file()

    task_data = {
        "name": "Real Task",
        "description": "This is a real task",
        "instruction": "Task instruction",
    }

    response = client.post(f"/api/task?project_path={project.path}", json=task_data)

    assert response.status_code == 200
    res = response.json()
    assert res["name"] == "Real Task"
    assert res["description"] == "This is a real task"
    assert res["instruction"] == "Task instruction"
    assert "path" in res
    assert res["id"] is not None
    assert res["priority"] == 2

    # Verify the task file on disk
    task_from_disk = Task.load_from_file(Path(res["path"]))

    assert task_from_disk.name == "Real Task"
    assert task_from_disk.description == "This is a real task"
    assert task_from_disk.instruction == "Task instruction"
    assert task_from_disk.id == res["id"]
    assert task_from_disk.priority == 2

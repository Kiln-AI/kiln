from unittest.mock import patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from kiln_ai.datamodel import (
    Project,
    Task,
)

from libs.studio.kiln_studio.custom_errors import connect_custom_errors
from libs.studio.kiln_studio.task_api import connect_task_api, task_from_id


@pytest.fixture
def app():
    app = FastAPI()
    connect_task_api(app)
    connect_custom_errors(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def project_and_task(tmp_path):
    project_path = tmp_path / "test_project" / "project.json"
    project_path.parent.mkdir()

    project = Project(name="Test Project", path=str(project_path))
    project.save_to_file()
    task = Task(
        name="Test Task",
        instruction="This is a test instruction",
        description="This is a test task",
        parent=project,
    )
    task.save_to_file()

    return project, task


def test_create_task_success(client, tmp_path):
    project_path = tmp_path / "test_project"
    project_path.mkdir()

    task_data = {
        "name": "Test Task",
        "description": "This is a test task",
        "instruction": "This is a test instruction",
    }

    with patch(
        "libs.studio.kiln_studio.task_api.project_from_id"
    ) as mock_project_from_id, patch(
        "libs.core.kiln_ai.datamodel.Task.save_to_file"
    ) as mock_save:
        mock_project_from_id.return_value = Project(
            name="Test Project", path=str(project_path)
        )
        mock_save.return_value = None

        response = client.post("/api/projects/project1-id/task", json=task_data)

    assert response.status_code == 200
    res = response.json()
    assert res["name"] == "Test Task"
    assert res["description"] == "This is a test task"
    assert res["id"] is not None
    assert res["priority"] == 2

    # Verify that project_from_id was called with the correct argument
    mock_project_from_id.assert_called_once_with("project1-id")


def test_create_task_project_not_found(client, tmp_path):
    task_data = {
        "name": "Test Task",
        "description": "This is a test task",
    }

    response = client.post("/api/projects/FAKEPROJECTID/task", json=task_data)

    assert response.status_code == 404
    assert response.json()["message"] == "Project not found. ID: FAKEPROJECTID"


def test_create_task_project_load_error(client, tmp_path):
    project_path = tmp_path / "test_project"
    project_path.mkdir()

    task_data = {
        "name": "Test Task",
        "description": "This is a test task",
    }

    with patch("libs.studio.kiln_studio.task_api.project_from_id") as mock_load:
        mock_load.side_effect = HTTPException(
            status_code=404, detail="Project not found"
        )

        response = client.post("/api/projects/FAKEPROJECTID/task", json=task_data)

    assert response.status_code == 404
    assert "Project not found" in response.json()["message"]


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
    with patch(
        "libs.studio.kiln_studio.task_api.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.return_value = project

        response = client.post("/api/projects/project1-id/task", json=task_data)

    assert response.status_code == 200
    res = response.json()
    assert res["name"] == "Real Task"
    assert res["description"] == "This is a real task"
    assert res["instruction"] == "Task instruction"
    assert res["id"] is not None
    assert res["priority"] == 2

    # Verify the task file on disk
    task_from_disk = project.tasks()[0]

    assert task_from_disk.name == "Real Task"
    assert task_from_disk.description == "This is a real task"
    assert task_from_disk.instruction == "Task instruction"
    assert task_from_disk.id == res["id"]
    assert task_from_disk.priority == 2


def test_get_task_success(client, project_and_task):
    project, task = project_and_task

    with patch(
        "libs.studio.kiln_studio.task_api.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.return_value = project
        response = client.get(f"/api/projects/project1-id/tasks/{task.id}")

    assert response.status_code == 200
    res = response.json()
    assert res["name"] == "Test Task"
    assert res["description"] == "This is a test task"
    assert res["id"] == task.id
    assert res["instruction"] == "This is a test instruction"


def test_get_task_not_found(client, project_and_task):
    project, _ = project_and_task

    with patch(
        "libs.studio.kiln_studio.task_api.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.return_value = project
        response = client.get("/api/projects/project1-id/tasks/non_existent_task_id")

    assert response.status_code == 404
    assert response.json()["message"] == "Task not found. ID: non_existent_task_id"


def test_get_task_project_not_found(client):
    with patch(
        "libs.studio.kiln_studio.task_api.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.side_effect = HTTPException(
            status_code=404, detail="Project not found"
        )
        response = client.get("/api/projects/non_existent_project_id/tasks/task_id")

    assert response.status_code == 404
    assert "Project not found" in response.json()["message"]


def test_task_from_id_success(project_and_task):
    project, task = project_and_task

    with patch(
        "libs.studio.kiln_studio.task_api.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.return_value = project
        result = task_from_id("project1-id", task.id)

    assert isinstance(result, Task)
    assert result.id == task.id
    assert result.name == "Test Task"
    assert result.description == "This is a test task"


def test_task_from_id_not_found(project_and_task):
    project, _ = project_and_task

    with patch(
        "libs.studio.kiln_studio.task_api.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.return_value = project
        with pytest.raises(HTTPException) as exc_info:
            task_from_id("project1-id", "non_existent_task_id")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Task not found. ID: non_existent_task_id"

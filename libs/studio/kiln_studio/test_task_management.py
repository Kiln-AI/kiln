from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from kiln_ai.adapters.base_adapter import AdapterRun
from kiln_ai.adapters.langchain_adapters import LangChainPromptAdapter
from kiln_ai.datamodel import Project, Task

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
        "libs.studio.kiln_studio.task_management.project_from_id"
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

    with patch("libs.studio.kiln_studio.task_management.project_from_id") as mock_load:
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
        "libs.studio.kiln_studio.task_management.project_from_id"
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


def test_get_task_success(client, tmp_path):
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

    with patch(
        "libs.studio.kiln_studio.task_management.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.return_value = project
        response = client.get(f"/api/projects/project1-id/task/{task.id}")

    assert response.status_code == 200
    res = response.json()
    assert res["name"] == "Test Task"
    assert res["description"] == "This is a test task"
    assert res["id"] == task.id


def test_get_task_not_found(client, tmp_path):
    project_path = tmp_path / "test_project" / "project.json"
    project_path.parent.mkdir()

    project = Project(name="Test Project", path=str(project_path))
    project.save_to_file()
    with patch(
        "libs.studio.kiln_studio.task_management.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.return_value = project
        response = client.get("/api/projects/project1-id/task/non_existent_task_id")

    assert response.status_code == 404
    assert response.json()["message"] == "Task not found. ID: non_existent_task_id"


def test_get_task_project_not_found(client):
    with patch(
        "libs.studio.kiln_studio.task_management.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.side_effect = HTTPException(
            status_code=404, detail="Project not found"
        )
        response = client.get("/api/projects/non_existent_project_id/task/task_id")

    assert response.status_code == 404
    assert "Project not found" in response.json()["message"]


@pytest.fixture
def mock_config():
    with patch("kiln_ai.utils.config.Config.shared") as MockConfig:
        # Mock the Config class
        mock_config_instance = MockConfig.return_value
        mock_config_instance.open_ai_api_key = "test_key"
        yield mock_config_instance


@pytest.mark.asyncio
async def test_run_task_success(client, tmp_path):
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

    run_task_request = {
        "model_name": "gpt_4o",
        "provider": "openai",
        "plaintext_input": "Test input",
    }

    with patch(
        "libs.studio.kiln_studio.task_management.project_from_id"
    ) as mock_project_from_id, patch.object(
        LangChainPromptAdapter, "invoke_returning_run", new_callable=AsyncMock
    ) as mock_invoke, patch("kiln_ai.utils.config.Config.shared") as MockConfig:
        mock_project_from_id.return_value = project
        mock_invoke.return_value = AdapterRun(run=None, output="Test output")

        # Mock the Config class
        mock_config_instance = MockConfig.return_value
        mock_config_instance.open_ai_api_key = "test_key"

        response = client.post(
            f"/api/projects/project1-id/task/{task.id}/run", json=run_task_request
        )

    assert response.status_code == 200
    res = response.json()
    assert res["output"]["plaintext_output"] == "Test output"
    assert res["output"]["structured_output"] is None
    assert res["run"] is None


@pytest.mark.asyncio
async def test_run_task_structured_output(client, tmp_path):
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

    run_task_request = {
        "model_name": "gpt_4o",
        "provider": "openai",
        "plaintext_input": "Test input",
    }

    with patch(
        "libs.studio.kiln_studio.task_management.project_from_id"
    ) as mock_project_from_id, patch.object(
        LangChainPromptAdapter, "invoke_returning_run", new_callable=AsyncMock
    ) as mock_invoke, patch("kiln_ai.utils.config.Config.shared") as MockConfig:
        mock_project_from_id.return_value = project
        mock_invoke.return_value = AdapterRun(run=None, output={"key": "value"})

        # Mock the Config class
        mock_config_instance = MockConfig.return_value
        mock_config_instance.open_ai_api_key = "test_key"
        mock_config_instance.user_id = "test_user"

        response = client.post(
            f"/api/projects/project1-id/task/{task.id}/run", json=run_task_request
        )

    res = response.json()
    assert response.status_code == 200
    assert res["output"]["plaintext_output"] is None
    assert res["output"]["structured_output"] == {"key": "value"}
    assert res["run"] is None


@pytest.mark.asyncio
async def test_run_task_not_found(client, tmp_path):
    project_path = tmp_path / "test_project" / "project.json"
    project_path.parent.mkdir()

    project = Project(name="Test Project", path=str(project_path))
    project.save_to_file()

    run_task_request = {
        "model_name": "gpt_4o",
        "provider": "openai",
        "plaintext_input": "Test input",
    }

    with patch(
        "libs.studio.kiln_studio.task_management.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.return_value = project
        response = client.post(
            "/api/projects/project1-id/task/non_existent_task_id/run",
            json=run_task_request,
        )

    assert response.status_code == 404
    assert response.json()["message"] == "Task not found. ID: non_existent_task_id"


@pytest.mark.asyncio
async def test_run_task_no_input(client, tmp_path, mock_config):
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

    run_task_request = {"model_name": "gpt_4o", "provider": "openai"}

    with patch(
        "libs.studio.kiln_studio.task_management.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.return_value = project
        response = client.post(
            f"/api/projects/project1-id/task/{task.id}/run", json=run_task_request
        )

    assert response.status_code == 422
    assert "Input should be a valid string" in response.json()["message"]


@pytest.mark.asyncio
async def test_run_task_structured_input(client, tmp_path):
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

    with patch.object(
        Task,
        "input_schema",
        return_value={
            "type": "object",
            "properties": {"key": {"type": "string"}},
        },
    ):
        task.save_to_file()

        run_task_request = {
            "model_name": "gpt_4o",
            "provider": "openai",
            "structured_input": {"key": "value"},
        }

        with patch(
            "libs.studio.kiln_studio.task_management.project_from_id"
        ) as mock_project_from_id, patch.object(
            LangChainPromptAdapter, "invoke_returning_run", new_callable=AsyncMock
        ) as mock_invoke, patch("kiln_ai.utils.config.Config.shared") as MockConfig:
            mock_project_from_id.return_value = project
            mock_invoke.return_value = AdapterRun(
                run=None, output="Structured input processed"
            )

            # Mock the Config class
            mock_config_instance = MockConfig.return_value
            mock_config_instance.open_ai_api_key = "test_key"
            mock_config_instance.user_id = "test_user"

            response = client.post(
                f"/api/projects/project1-id/task/{task.id}/run", json=run_task_request
            )

    assert response.status_code == 200
    res = response.json()
    assert res["output"]["plaintext_output"] == "Structured input processed"
    assert res["output"]["structured_output"] is None
    assert res["run"] is None

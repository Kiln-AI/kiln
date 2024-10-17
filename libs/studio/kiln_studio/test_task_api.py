from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from kiln_ai.adapters.base_adapter import AdapterRun
from kiln_ai.adapters.langchain_adapters import LangChainPromptAdapter
from kiln_ai.datamodel import (
    DataSource,
    DataSourceType,
    Project,
    Task,
    TaskOutput,
    TaskOutputRatingType,
    TaskRun,
)

from libs.studio.kiln_studio.custom_errors import connect_custom_errors
from libs.studio.kiln_studio.task_api import connect_task_api, deep_update


@pytest.fixture
def app():
    app = FastAPI()
    connect_task_api(app)
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
        "libs.studio.kiln_studio.task_api.project_from_id"
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
        "libs.studio.kiln_studio.task_api.project_from_id"
    ) as mock_project_from_id:
        mock_project_from_id.return_value = project
        response = client.get("/api/projects/project1-id/task/non_existent_task_id")

    assert response.status_code == 404
    assert response.json()["message"] == "Task not found. ID: non_existent_task_id"


def test_get_task_project_not_found(client):
    with patch(
        "libs.studio.kiln_studio.task_api.project_from_id"
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
        "libs.studio.kiln_studio.task_api.project_from_id"
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
    assert res["raw_output"] == "Test output"
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
        "libs.studio.kiln_studio.task_api.project_from_id"
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
    assert res["raw_output"] == '{"key": "value"}'
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
        "libs.studio.kiln_studio.task_api.project_from_id"
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
        "libs.studio.kiln_studio.task_api.project_from_id"
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
            "libs.studio.kiln_studio.task_api.project_from_id"
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
    assert res["raw_output"] == "Structured input processed"
    assert res["run"] is None


def test_deep_update_with_empty_source():
    source = {}
    update = {"a": 1, "b": {"c": 2}}
    result = deep_update(source, update)
    assert result == {"a": 1, "b": {"c": 2}}


def test_deep_update_with_existing_keys():
    source = {"a": 0, "b": {"c": 1}}
    update = {"a": 1, "b": {"d": 2}}
    result = deep_update(source, update)
    assert result == {"a": 1, "b": {"c": 1, "d": 2}}


def test_deep_update_with_nested_dicts():
    source = {"a": {"b": {"c": 1}}}
    update = {"a": {"b": {"d": 2}, "e": 3}}
    result = deep_update(source, update)
    assert result == {"a": {"b": {"c": 1, "d": 2}, "e": 3}}


def test_deep_update_with_non_dict_values():
    source = {"a": 1, "b": [1, 2, 3]}
    update = {"a": 2, "b": [4, 5, 6], "c": "new"}
    result = deep_update(source, update)
    assert result == {"a": 2, "b": [4, 5, 6], "c": "new"}


def test_deep_update_with_mixed_types():
    source = {"a": 1, "b": {"c": [1, 2, 3]}}
    update = {"a": "new", "b": {"c": 4, "d": {"e": 5}}}
    result = deep_update(source, update)
    assert result == {"a": "new", "b": {"c": 4, "d": {"e": 5}}}


def test_deep_update_with_none_values():
    # Test case 1: Basic removal of keys
    source = {"a": 1, "b": 2, "c": 3}
    update = {"a": None, "b": 4}
    result = deep_update(source, update)
    assert result == {"b": 4, "c": 3}

    # Test case 2: Nested dictionaries
    source = {"x": 1, "y": {"y1": 10, "y2": 20, "y3": {"y3a": 100, "y3b": 200}}, "z": 3}
    update = {"y": {"y2": None, "y3": {"y3b": None, "y3c": 300}}, "z": None}
    result = deep_update(source, update)
    assert result == {"x": 1, "y": {"y1": 10, "y3": {"y3a": 100, "y3c": 300}}}

    # Test case 3: Update with empty dictionary
    source = {"a": 1, "b": 2}
    update = {}
    result = deep_update(source, update)
    assert result == {"a": 1, "b": 2}

    # Test case 4: Update missing with none elements
    source = {"a": 1, "b": {"d": 1}}
    update = {"b": {"e": {"f": {"h": 1, "j": None}, "g": None}}}
    result = deep_update(source, update)
    assert result == {"a": 1, "b": {"d": 1, "e": {"f": {"h": 1}}}}

    # Test case 5: Mixed types
    source = {"a": 1, "b": {"x": 10, "y": 20}, "c": [1, 2, 3]}
    update = {"b": {"y": None, "z": 30}, "c": None, "d": 4}
    result = deep_update(source, update)
    assert result == {"a": 1, "b": {"x": 10, "z": 30}, "d": 4}

    # Test case 6: Update with
    source = {}
    update = {"a": {"b": None, "c": None}}
    result = deep_update(source, update)
    assert result == {"a": {}}

    # Test case 7: Update with
    source = {
        "output": {
            "rating": None,
            "model_type": "task_output",
        },
    }
    update = {
        "output": {
            "rating": {
                "value": 2,
                "type": "five_star",
                "requirement_ratings": {
                    "148753630565": None,
                    "988847661375": 3,
                    "474350686960": None,
                },
            }
        }
    }
    result = deep_update(source, update)
    assert result["output"]["rating"]["value"] == 2
    assert result["output"]["rating"]["type"] == "five_star"
    assert result["output"]["rating"]["requirement_ratings"] == {
        # "148753630565": None,
        "988847661375": 3,
        # "474350686960": None,
    }


def test_update_run_method():
    run = TaskRun(
        input="Test input",
        input_source=DataSource(
            type=DataSourceType.human, properties={"created_by": "Jane Doe"}
        ),
        output=TaskOutput(
            output="Test output",
            source=DataSource(
                type=DataSourceType.human, properties={"created_by": "Jane Doe"}
            ),
        ),
    )

    dumped = run.model_dump()
    merged = deep_update(dumped, {"input": "Updated input"})
    updated_run = TaskRun.model_validate(merged)
    assert updated_run.input == "Updated input"

    update = {
        "output": {"rating": {"value": 4, "type": TaskOutputRatingType.five_star}}
    }
    dumped = run.model_dump()
    merged = deep_update(dumped, update)
    updated_run = TaskRun.model_validate(merged)
    assert updated_run.output.rating.value == 4
    assert updated_run.output.rating.type == TaskOutputRatingType.five_star


@pytest.mark.asyncio
async def test_update_run(client, tmp_path):
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
    run = TaskRun(
        parent=task,
        input="Test input",
        input_source=DataSource(
            type=DataSourceType.human, properties={"created_by": "Jane Doe"}
        ),
        output=TaskOutput(
            output="Test output",
            source=DataSource(
                type=DataSourceType.human, properties={"created_by": "Jane Doe"}
            ),
        ),
    )
    run.save_to_file()

    test_cases = [
        {
            "name": "Update output rating",
            "patch": {
                "output": {
                    "rating": {"value": 4, "type": TaskOutputRatingType.five_star},
                }
            },
            "expected": {
                "output": {
                    "rating": {"value": 4, "type": TaskOutputRatingType.five_star},
                }
            },
        },
        {
            "name": "Update input",
            "patch": {
                "input": "Updated input",
            },
            "expected": {
                "input": "Updated input",
            },
        },
    ]

    for case in test_cases:
        with patch(
            "libs.studio.kiln_studio.task_api.project_from_id"
        ) as mock_project_from_id:
            mock_project_from_id.return_value = project

            response = client.patch(
                f"/api/projects/project1-id/task/{task.id}/run/{run.id}",
                json=case["patch"],
            )

            assert response.status_code == 200, f"Failed on case: {case['name']}"

    # Test error cases, including deep validation
    error_cases = [
        {
            "name": "Task not found",
            "task_id": "non_existent_task_id",
            "run_id": run.id,
            "expected_status": 404,
            "expected_detail": "Task not found. ID: non_existent_task_id",
            "updates": {"input": "Updated input"},
        },
        {
            "name": "Run not found",
            "task_id": task.id,
            "run_id": "non_existent_run_id",
            "expected_status": 404,
            "expected_detail": "Run not found. ID: non_existent_run_id",
            "updates": {"input": "Updated input"},
        },
        {
            "name": "Invalid input",
            "task_id": task.id,
            "run_id": run.id,
            "expected_status": 422,
            "expected_detail": "Input: Input should be a valid string",
            "updates": {"input": 123},
        },
        {
            "name": "Invalid rating without value",
            "task_id": task.id,
            "run_id": run.id,
            "expected_status": 422,
            "expected_detail": "Output.Rating.Type: Input should be 'five_star' or 'custom'",
            "updates": {
                "output": {
                    "rating": {"type": "invalid", "rating": 1},
                }
            },
        },
    ]

    for case in error_cases:
        with patch(
            "libs.studio.kiln_studio.task_api.project_from_id"
        ) as mock_project_from_id:
            mock_project_from_id.return_value = project

            response = client.patch(
                f"/api/projects/project1-id/task/{case['task_id']}/run/{case['run_id']}",
                json=case["updates"],
            )

            assert (
                response.status_code == case["expected_status"]
            ), f"Failed on case: {case['name']}"
            assert (
                response.json()["message"] == case["expected_detail"]
            ), f"Failed on case: {case['name']}"

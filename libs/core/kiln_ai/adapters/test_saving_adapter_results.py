from unittest.mock import patch

import pytest
from kiln_ai.adapters.base_adapter import AdapterInfo, BaseAdapter
from kiln_ai.datamodel import (
    DataSourceType,
    Project,
    Task,
)
from kiln_ai.utils.config import Config


class TestAdapter(BaseAdapter):
    async def _run(self, input: dict | str) -> dict | str:
        return "Test output"

    def adapter_info(self) -> AdapterInfo:
        return AdapterInfo(
            adapter_name="mock_adapter",
            model_name="mock_model",
            model_provider="mock_provider",
            prompt_builder_name="mock_prompt_builder",
        )


@pytest.fixture
def test_task(tmp_path):
    project = Project(name="test_project", path=tmp_path / "test_project.kiln")
    project.save_to_file()
    task = Task(
        parent=project,
        name="test_task",
        instruction="Task instruction",
    )
    task.save_to_file()
    return task


def test_save_run_isolation(test_task):
    adapter = TestAdapter(test_task)
    input_data = "Test input"
    output_data = "Test output"

    task_output = adapter.save_run(input_data, DataSourceType.human, output_data)

    # Check that the task input was saved correctly
    assert task_output.parent == test_task
    assert task_output.input == input_data
    assert task_output.source == DataSourceType.human

    # Check that the task output was saved correctly
    saved_outputs = task_output.outputs()
    assert len(saved_outputs) == 1
    saved_output = saved_outputs[0]
    assert saved_output.parent.id == task_output.id
    assert saved_output.output == output_data
    assert saved_output.source == DataSourceType.synthetic
    assert saved_output.rating is None

    # Verify that the data can be read back from disk
    reloaded_task = Task.load_from_file(test_task.path)
    reloaded_runs = reloaded_task.runs()
    assert len(reloaded_runs) == 1
    reloaded_run = reloaded_runs[0]
    assert reloaded_run.input == input_data
    assert reloaded_run.source == DataSourceType.human

    reloaded_outputs = reloaded_run.outputs()
    assert len(reloaded_outputs) == 1
    reloaded_output = reloaded_outputs[0]
    assert reloaded_output.parent.id == reloaded_run.id
    assert reloaded_output.output == output_data
    assert reloaded_output.source == DataSourceType.synthetic
    assert reloaded_output.rating is None
    assert reloaded_output.source_properties["adapter_name"] == "mock_adapter"
    assert reloaded_output.source_properties["model_name"] == "mock_model"
    assert reloaded_output.source_properties["model_provider"] == "mock_provider"
    assert (
        reloaded_output.source_properties["prompt_builder_name"]
        == "mock_prompt_builder"
    )
    creator = Config.shared().user_id
    if creator and creator != "":
        assert reloaded_output.source_properties["creator"] == creator
    else:
        assert "creator" not in reloaded_output.source_properties

    # Run again, with same input and different output. Should create a new TaskOutput under the same TaskRun.
    task_output = adapter.save_run(input_data, DataSourceType.human, "Different output")
    assert len(test_task.runs()) == 1
    assert len(task_output.outputs()) == 2
    outputs = task_output.outputs()
    assert len(outputs) == 2
    assert set(output.output for output in outputs) == {output_data, "Different output"}

    # run again with same input and same output. Should not create a new TaskOutput.
    task_output = adapter.save_run(input_data, DataSourceType.human, output_data)
    assert len(test_task.runs()) == 1
    assert len(task_output.outputs()) == 2
    outputs = task_output.outputs()
    assert len(outputs) == 2
    assert set(output.output for output in outputs) == {output_data, "Different output"}

    # run again with input of different type. Should create a new TaskRun and TaskOutput.
    task_output = adapter.save_run(input_data, DataSourceType.synthetic, output_data)
    assert len(test_task.runs()) == 2
    assert len(task_output.outputs()) == 1
    outputs = task_output.outputs()
    assert len(outputs) == 1
    assert outputs[0].output == output_data


@pytest.mark.asyncio
async def test_autosave_false(test_task):
    with patch("kiln_ai.utils.config.Config.shared") as mock_shared:
        mock_config = mock_shared.return_value
        mock_config.autosave_runs = False

        adapter = TestAdapter(test_task)
        input_data = "Test input"

        await adapter.invoke(input_data, DataSourceType.synthetic)

        # Check that no runs were saved
        assert len(test_task.runs()) == 0


@pytest.mark.asyncio
async def test_autosave_true(test_task):
    with patch("kiln_ai.utils.config.Config.shared") as mock_shared:
        mock_config = mock_shared.return_value
        mock_config.autosave_runs = True
        mock_config.user_id = "test_user"

        adapter = TestAdapter(test_task)
        input_data = "Test input"

        await adapter.invoke(input_data, DataSourceType.synthetic)

        # Check that an task input was saved
        task_outputs = test_task.runs()
        assert len(task_outputs) == 1
        assert task_outputs[0].input == input_data
        assert task_outputs[0].source == DataSourceType.synthetic
        assert len(task_outputs[0].outputs()) == 1
        assert task_outputs[0].outputs()[0].output == "Test output"
        assert task_outputs[0].outputs()[0].source_properties["creator"] == "test_user"
        assert task_outputs[0].outputs()[0].source == DataSourceType.synthetic
        output = task_outputs[0].outputs()[0]
        assert output.source_properties["adapter_name"] == "mock_adapter"
        assert output.source_properties["model_name"] == "mock_model"
        assert output.source_properties["model_provider"] == "mock_provider"
        assert output.source_properties["prompt_builder_name"] == "mock_prompt_builder"

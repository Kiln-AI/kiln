from unittest.mock import patch

import pytest
from kiln_ai.adapters.base_adapter import AdapterInfo, BaseAdapter
from kiln_ai.datamodel import (
    DataSource,
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

    task_input = adapter.save_run(input_data, DataSource.human, output_data)

    # Check that the task input was saved correctly
    assert task_input.parent == test_task
    assert task_input.input == input_data
    assert task_input.source == DataSource.human

    # Check that the task output was saved correctly
    saved_outputs = task_input.outputs()
    assert len(saved_outputs) == 1
    saved_output = saved_outputs[0]
    assert saved_output.parent.id == task_input.id
    assert saved_output.output == output_data
    assert saved_output.source == DataSource.synthetic
    assert saved_output.requirement_ratings == {}

    # Verify that the data can be read back from disk
    reloaded_task = Task.load_from_file(test_task.path)
    reloaded_runs = reloaded_task.runs()
    assert len(reloaded_runs) == 1
    reloaded_run = reloaded_runs[0]
    assert reloaded_run.input == input_data
    assert reloaded_run.source == DataSource.human

    reloaded_outputs = reloaded_run.outputs()
    assert len(reloaded_outputs) == 1
    reloaded_output = reloaded_outputs[0]
    assert reloaded_output.parent.id == reloaded_run.id
    assert reloaded_output.output == output_data
    assert reloaded_output.source == DataSource.synthetic
    assert reloaded_output.requirement_ratings == {}
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

    # Run again, with same input and different output. Should create a new TaskOutput under the same TaskInput.
    task_input = adapter.save_run(input_data, DataSource.human, "Different output")
    assert len(test_task.runs()) == 1
    assert len(task_input.outputs()) == 2
    outputs = task_input.outputs()
    assert len(outputs) == 2
    assert set(output.output for output in outputs) == {output_data, "Different output"}

    # run again with same input and same output. Should not create a new TaskOutput.
    task_input = adapter.save_run(input_data, DataSource.human, output_data)
    assert len(test_task.runs()) == 1
    assert len(task_input.outputs()) == 2
    outputs = task_input.outputs()
    assert len(outputs) == 2
    assert set(output.output for output in outputs) == {output_data, "Different output"}

    # run again with input of different type. Should create a new TaskInput and TaskOutput.
    task_input = adapter.save_run(input_data, DataSource.synthetic, output_data)
    assert len(test_task.runs()) == 2
    assert len(task_input.outputs()) == 1
    outputs = task_input.outputs()
    assert len(outputs) == 1
    assert outputs[0].output == output_data


@pytest.mark.asyncio
async def test_autosave_false(test_task):
    with patch("kiln_ai.utils.config.Config.shared") as mock_shared:
        mock_config = mock_shared.return_value
        mock_config.autosave_runs = False

        adapter = TestAdapter(test_task)
        input_data = "Test input"

        await adapter.invoke(input_data, DataSource.synthetic)

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

        await adapter.invoke(input_data, DataSource.synthetic)

        # Check that an task input was saved
        task_inputs = test_task.runs()
        assert len(task_inputs) == 1
        assert task_inputs[0].input == input_data
        assert task_inputs[0].source == DataSource.synthetic
        assert len(task_inputs[0].outputs()) == 1
        assert task_inputs[0].outputs()[0].output == "Test output"
        assert task_inputs[0].outputs()[0].source_properties["creator"] == "test_user"
        assert task_inputs[0].outputs()[0].source == DataSource.synthetic
        output = task_inputs[0].outputs()[0]
        assert output.source_properties["adapter_name"] == "mock_adapter"
        assert output.source_properties["model_name"] == "mock_model"
        assert output.source_properties["model_provider"] == "mock_provider"
        assert output.source_properties["prompt_builder_name"] == "mock_prompt_builder"

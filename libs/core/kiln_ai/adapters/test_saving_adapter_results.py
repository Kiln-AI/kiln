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


def test_save_example_isolation(test_task):
    adapter = TestAdapter(test_task)
    input_data = "Test input"
    output_data = "Test output"

    example = adapter.save_example(input_data, DataSource.human, output_data)

    # Check that the example was saved correctly
    assert example.parent == test_task
    assert example.input == input_data
    assert example.source == DataSource.human

    # Check that the example output was saved correctly
    saved_outputs = example.outputs()
    assert len(saved_outputs) == 1
    saved_output = saved_outputs[0]
    assert saved_output.parent.id == example.id
    assert saved_output.output == output_data
    assert saved_output.source == DataSource.synthetic
    assert saved_output.requirement_ratings == {}

    # Verify that the data can be read back from disk
    reloaded_task = Task.load_from_file(test_task.path)
    reloaded_examples = reloaded_task.examples()
    assert len(reloaded_examples) == 1
    reloaded_example = reloaded_examples[0]
    assert reloaded_example.input == input_data
    assert reloaded_example.source == DataSource.human

    reloaded_outputs = reloaded_example.outputs()
    assert len(reloaded_outputs) == 1
    reloaded_output = reloaded_outputs[0]
    assert reloaded_output.parent.id == reloaded_example.id
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

    # Run again, with same input and different output. Should create a new ExampleOutput under the same Example.
    example = adapter.save_example(input_data, DataSource.human, "Different output")
    assert len(test_task.examples()) == 1
    assert len(example.outputs()) == 2
    outputs = example.outputs()
    assert len(outputs) == 2
    assert set(output.output for output in outputs) == {output_data, "Different output"}

    # run again with same input and same output. Should not create a new ExampleOutput.
    example = adapter.save_example(input_data, DataSource.human, output_data)
    assert len(test_task.examples()) == 1
    assert len(example.outputs()) == 2
    outputs = example.outputs()
    assert len(outputs) == 2
    assert set(output.output for output in outputs) == {output_data, "Different output"}

    # run again with input of different type. Should create a new Example and ExampleOutput.
    example = adapter.save_example(input_data, DataSource.synthetic, output_data)
    assert len(test_task.examples()) == 2
    assert len(example.outputs()) == 1
    outputs = example.outputs()
    assert len(outputs) == 1
    assert outputs[0].output == output_data


@pytest.mark.asyncio
async def test_autosave_false(test_task):
    with patch("kiln_ai.utils.config.Config.shared") as mock_shared:
        mock_config = mock_shared.return_value
        mock_config.autosave_examples = False

        adapter = TestAdapter(test_task)
        input_data = "Test input"

        await adapter.invoke(input_data, DataSource.synthetic)

        # Check that no examples were saved
        assert len(test_task.examples()) == 0


@pytest.mark.asyncio
async def test_autosave_true(test_task):
    with patch("kiln_ai.utils.config.Config.shared") as mock_shared:
        mock_config = mock_shared.return_value
        mock_config.autosave_examples = True
        mock_config.user_id = "test_user"

        adapter = TestAdapter(test_task)
        input_data = "Test input"

        await adapter.invoke(input_data, DataSource.synthetic)

        # Check that an example was saved
        examples = test_task.examples()
        assert len(examples) == 1
        assert examples[0].input == input_data
        assert examples[0].source == DataSource.synthetic
        assert len(examples[0].outputs()) == 1
        assert examples[0].outputs()[0].output == "Test output"
        assert examples[0].outputs()[0].source_properties["creator"] == "test_user"
        assert examples[0].outputs()[0].source == DataSource.synthetic
        output = examples[0].outputs()[0]
        assert output.source_properties["adapter_name"] == "mock_adapter"
        assert output.source_properties["model_name"] == "mock_model"
        assert output.source_properties["model_provider"] == "mock_provider"
        assert output.source_properties["prompt_builder_name"] == "mock_prompt_builder"

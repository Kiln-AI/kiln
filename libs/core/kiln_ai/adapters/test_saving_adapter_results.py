from unittest.mock import AsyncMock, patch

import pytest
from kiln_ai.adapters.base_adapter import BaseAdapter
from kiln_ai.datamodel import (
    Example,
    ExampleOutput,
    ExampleOutputSource,
    ExampleSource,
    Project,
    Task,
)
from kiln_ai.utils.config import Config


class TestAdapter(BaseAdapter):
    async def _run(self, input: dict | str) -> dict | str:
        return "Test output"


@pytest.fixture
def test_task(tmp_path):
    project = Project(name="test_project", path=tmp_path / "test_project.kiln")
    project.save_to_file()
    task = Task(parent=project, name="test_task")
    task.save_to_file()
    return task


def test_save_example_isolation(test_task):
    adapter = TestAdapter(test_task)
    input_data = "Test input"
    output_data = "Test output"

    example = adapter.save_example(input_data, output_data)

    # Check that the example was saved correctly
    assert example.parent == test_task
    assert example.input == input_data
    assert example.source == ExampleSource.synthetic

    # Check that the example output was saved correctly
    saved_outputs = example.outputs()
    assert len(saved_outputs) == 1
    saved_output = saved_outputs[0]
    assert saved_output.parent.id == example.id
    assert saved_output.output == output_data
    assert saved_output.source == ExampleOutputSource.synthetic
    assert saved_output.source_properties == {"creator": Config.shared().user_id}
    assert saved_output.requirement_ratings == {}

    # Verify that the data can be read back from disk
    reloaded_task = Task.load_from_file(test_task.path)
    reloaded_examples = reloaded_task.examples()
    assert len(reloaded_examples) == 1
    reloaded_example = reloaded_examples[0]
    assert reloaded_example.input == input_data
    assert reloaded_example.source == ExampleSource.synthetic

    reloaded_outputs = reloaded_example.outputs()
    assert len(reloaded_outputs) == 1
    reloaded_output = reloaded_outputs[0]
    assert reloaded_output.parent.id == reloaded_example.id
    assert reloaded_output.output == output_data
    assert reloaded_output.source == ExampleOutputSource.synthetic
    assert reloaded_output.source_properties == {"creator": Config.shared().user_id}
    assert reloaded_output.requirement_ratings == {}


@pytest.mark.asyncio
async def test_autosave_false(test_task):
    with patch("kiln_ai.utils.config.Config.shared") as mock_shared:
        mock_config = mock_shared.return_value
        mock_config.autosave_examples = False

        adapter = TestAdapter(test_task)
        input_data = "Test input"

        await adapter.invoke(input_data)

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

        await adapter.invoke(input_data)

        # Check that an example was saved
        examples = test_task.examples()
        assert len(examples) == 1
        assert examples[0].input == input_data
        assert len(examples[0].outputs()) == 1
        assert examples[0].outputs()[0].output == "Test output"
        assert examples[0].outputs()[0].source_properties["creator"] == "test_user"

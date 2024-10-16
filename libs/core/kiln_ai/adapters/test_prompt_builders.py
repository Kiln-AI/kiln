import json

from kiln_ai.adapters.base_adapter import AdapterInfo, BaseAdapter
from kiln_ai.adapters.prompt_builders import MultiShotPromptBuilder, SimplePromptBuilder
from kiln_ai.adapters.test_prompt_adaptors import build_test_task
from kiln_ai.adapters.test_structured_output import build_structured_output_test_task
from kiln_ai.datamodel import (
    DataSource,
    DataSourceType,
    Project,
    Task,
    TaskOutput,
    TaskOutputRating,
    TaskRun,
)


def test_simple_prompt_builder(tmp_path):
    task = build_test_task(tmp_path)
    builder = SimplePromptBuilder(task=task)
    input = "two plus two"
    prompt = builder.build_prompt()
    assert (
        "You are an assistant which performs math tasks provided in plain text."
        in prompt
    )

    assert "1) " + task.requirements[0].instruction in prompt
    assert "2) " + task.requirements[1].instruction in prompt
    assert "3) " + task.requirements[2].instruction in prompt

    user_msg = builder.build_user_message(input)
    assert input in user_msg
    assert input not in prompt


class MockAdapter(BaseAdapter):
    def adapter_specific_instructions(self) -> str | None:
        return "You are a mock, send me the response!"

    def _run(self, input: str) -> str:
        return "mock response"

    def adapter_info(self) -> AdapterInfo:
        return AdapterInfo(
            adapter_name="mock_adapter",
            model_name="mock_model",
            model_provider="mock_provider",
        )


def test_simple_prompt_builder_structured_output(tmp_path):
    task = build_structured_output_test_task(tmp_path)
    builder = SimplePromptBuilder(task=task)
    builder.adapter = MockAdapter(task)
    input = "Cows"
    prompt = builder.build_prompt()
    assert "You are an assistant which tells a joke, given a subject." in prompt

    # check adapter instructions are included
    assert "You are a mock, send me the response!" in prompt

    user_msg = builder.build_user_message(input)
    assert input in user_msg
    assert input not in prompt


def test_multi_shot_prompt_builder(tmp_path):
    # Create a project and task hierarchy
    project = Project(name="Test Project", path=(tmp_path / "test_project.kiln"))
    project.save_to_file()
    task = Task(
        name="Test Task",
        instruction="You are an assistant which tells a joke, given a subject.",
        parent=project,
        input_json_schema=json.dumps(
            {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                },
                "required": ["subject"],
            }
        ),
        output_json_schema=json.dumps(
            {
                "type": "object",
                "properties": {"joke": {"type": "string"}},
                "required": ["joke"],
            }
        ),
    )
    task.save_to_file()

    check_example_outputs(task, 0)

    # Create an task input, but with no output
    e1 = TaskRun(
        input='{"subject": "Cows"}',
        input_source=DataSource(
            type=DataSourceType.human,
            properties={"creator": "john_doe"},
        ),
        parent=task,
        output=TaskOutput(
            output='{"joke": "Moo I am a cow joke."}',
            source=DataSource(
                type=DataSourceType.human,
                properties={"creator": "john_doe"},
            ),
        ),
    )
    e1.save_to_file()

    ## still zero since not fixed and not rated highly
    check_example_outputs(task, 0)

    e1.output.rating = TaskOutputRating(value=4)
    e1.save_to_file()
    # Now that it's highly rated, it should be included
    check_example_outputs(task, 1)

    e2 = TaskRun(
        input='{"subject": "Dogs"}',
        input_source=DataSource(
            type=DataSourceType.human,
            properties={"creator": "john_doe"},
        ),
        parent=task,
        output=TaskOutput(
            output='{"joke": "This is a ruff joke."}',
            source=DataSource(
                type=DataSourceType.human,
                properties={"creator": "john_doe"},
            ),
            rating=TaskOutputRating(value=4, reason="Bark"),
        ),
    )
    e2.save_to_file()
    check_example_outputs(task, 2)


def check_example_outputs(task: Task, count: int):
    prompt_builder = MultiShotPromptBuilder(task=task)
    prompt = prompt_builder.build_prompt()
    assert "# Instruction" in prompt
    assert task.instruction in prompt
    if count == 0:
        assert "# Example Outputs" not in prompt
    else:
        assert "# Example Outputs" in prompt
        assert f"## Example {count}" in prompt


def test_prompt_builder_name():
    assert SimplePromptBuilder.prompt_builder_name() == "simple_prompt_builder"
    assert MultiShotPromptBuilder.prompt_builder_name() == "multi_shot_prompt_builder"

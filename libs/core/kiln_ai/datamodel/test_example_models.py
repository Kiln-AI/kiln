import json

import pytest
from kiln_ai.datamodel import (
    Example,
    ExampleOutput,
    ExampleOutputSource,
    ExampleSource,
    Project,
    ReasonRating,
    Task,
    TaskDeterminism,
    TaskRequirement,
)
from pydantic import ValidationError


def test_example_model_validation(tmp_path):
    # Valid example
    task = Task(name="Test Task", path=tmp_path / Task.base_filename())
    task.save_to_file()
    valid_example = Example(
        parent=task,
        input="Test input",
        source=ExampleSource.human,
        source_properties={"creator": "John Doe"},
    )
    assert valid_example.input == "Test input"
    assert valid_example.source == ExampleSource.human
    assert valid_example.source_properties == {"creator": "John Doe"}

    # Invalid source
    with pytest.raises(ValidationError):
        Example(
            parent=task,
            input="Test input",
            source="invalid_source",
            source_properties={},
        )

    # Missing required field
    with pytest.raises(ValidationError):
        Example(parent=task, source=ExampleSource.human, source_properties={})

    # Invalid source_properties type
    with pytest.raises(ValidationError):
        Example(
            parent=task,
            input="Test input",
            source=ExampleSource.human,
            source_properties="invalid",
        )


def test_example_relationship(tmp_path):
    task = Task(name="Test Task", path=tmp_path / Task.base_filename())
    task.save_to_file()
    example = Example(
        parent=task,
        input="Test input",
        source=ExampleSource.human,
        source_properties={},
    )
    assert example.relationship_name() == "examples"
    assert example.parent_type().__name__ == "Task"


def test_example_output_model_validation(tmp_path):
    # Valid example output
    task = Task(name="Test Task", path=tmp_path / Task.base_filename())
    task.save_to_file()
    example = Example(input="Test input", source=ExampleSource.human, parent=task)
    example.save_to_file()
    valid_output = ExampleOutput(
        parent=example,
        output="Test output",
        source=ExampleOutputSource.human,
        source_properties={"creator": "Jane Doe"},
        requirement_ratings={},
    )
    assert valid_output.output == "Test output"
    assert valid_output.source == ExampleOutputSource.human
    assert valid_output.source_properties == {"creator": "Jane Doe"}
    assert len(valid_output.requirement_ratings) == 0

    # Invalid source
    with pytest.raises(ValidationError):
        ExampleOutput(
            path="/test/path",
            output="Test output",
            source="invalid_source",
            source_properties={},
            requirement_ratings={},
        )

    # Missing required field
    with pytest.raises(ValidationError):
        ExampleOutput(
            path="/test/path",
            source=ExampleOutputSource.human,
            source_properties={},
            requirement_ratings={},
        )

    # Invalid rating in ReasonRating
    with pytest.raises(ValidationError):
        ExampleOutput(
            path="/test/path",
            output="Test output",
            source=ExampleOutputSource.human,
            source_properties={},
            requirement_ratings={
                "req1": ReasonRating(rating=6, reason="Invalid rating")
            },
        )

    # Invalid requirement_ratings type
    with pytest.raises(ValidationError):
        ExampleOutput(
            path="/test/path",
            output="Test output",
            source=ExampleOutputSource.human,
            source_properties={},
            requirement_ratings="invalid",
        )


def test_structured_output_workflow(tmp_path):
    tmp_project_file = (
        tmp_path / "test_structured_output_examples" / Project.base_filename()
    )
    # Create project
    project = Project(name="Test Project", path=str(tmp_project_file))
    project.save_to_file()

    # Create task with requirements
    task = Task(
        name="Structured Output Task",
        parent=project,
        instruction="Generate a JSON object with name and age",
        determinism=TaskDeterminism.semantic_match,
        output_json_schema=json.dumps(
            {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                "required": ["name", "age"],
            }
        ),
    )
    task.save_to_file()

    req1 = TaskRequirement(
        name="Req1", instruction="Name must be capitalized", parent=task
    )
    req2 = TaskRequirement(name="Req2", instruction="Age must be positive", parent=task)
    req1.save_to_file()
    req2.save_to_file()

    # Create examples
    examples = []
    for source in ExampleSource:
        for _ in range(2):
            example = Example(
                input="Generate info for John Doe",
                source=source,
                parent=task,
            )
            example.save_to_file()
            examples.append(example)

    # Create outputs
    outputs = []
    for example in examples:
        output = ExampleOutput(
            output='{"name": "John Doe", "age": 30}',
            source=ExampleOutputSource.human,
            source_properties={"creator": "john_doe"},
            parent=example,
        )
        output.save_to_file()
        outputs.append(output)

    # Update outputs with ratings
    for output in outputs:
        output.rating = ReasonRating(rating=4, reason="Good output")
        output.requirement_ratings = {
            req1.id: ReasonRating(rating=5, reason="Name is capitalized"),
            req2.id: ReasonRating(rating=5, reason="Age is positive"),
        }
        output.save_to_file()

    # Update outputs with fixed_output
    outputs[0].fixed_output = '{"name": "John Doe", "age": 31}'
    outputs[0].save_to_file()

    # Load from disk and validate
    loaded_project = Project.load_from_file(tmp_project_file)
    loaded_task = loaded_project.tasks()[0]

    assert loaded_task.name == "Structured Output Task"
    assert len(loaded_task.requirements()) == 2
    assert len(loaded_task.examples()) == 4

    loaded_examples = loaded_task.examples()
    for example in loaded_examples:
        outputs = example.outputs()
        assert len(outputs) == 1
        output = outputs[0]
        assert output.rating is not None
        assert len(output.requirement_ratings) == 2

    # Find the example with the fixed output
    example_with_fixed_output = next(
        (
            example
            for example in loaded_examples
            if example.outputs()[0].fixed_output is not None
        ),
        None,
    )
    assert example_with_fixed_output is not None, "No example found with fixed output"
    assert (
        example_with_fixed_output.outputs()[0].fixed_output
        == '{"name": "John Doe", "age": 31}'
    )


def test_example_output_requirement_rating_keys(tmp_path):
    # Create a project, task, and example hierarchy
    project = Project(name="Test Project", path=(tmp_path / "test_project"))
    project.save_to_file()
    task = Task(name="Test Task", parent=project)
    task.save_to_file()
    example = Example(input="Test input", source="human", parent=task)
    example.save_to_file()

    # Create task requirements
    req1 = TaskRequirement(name="Requirement 1", parent=task)
    req1.save_to_file()
    req2 = TaskRequirement(name="Requirement 2", parent=task)
    req2.save_to_file()
    # Valid case: all requirement IDs are valid
    valid_output = ExampleOutput(
        output="Test output",
        source="human",
        source_properties={"creator": "john_doe"},
        parent=example,
        requirement_ratings={
            req1.id: {"rating": 5, "reason": "Excellent"},
            req2.id: {"rating": 4, "reason": "Good"},
        },
    )
    valid_output.save_to_file()
    assert valid_output.requirement_ratings is not None

    # Invalid case: unknown requirement ID
    with pytest.raises(
        ValueError,
        match="Requirement ID .* is not a valid requirement ID for this task",
    ):
        output = ExampleOutput(
            output="Test output",
            source="human",
            source_properties={"creator": "john_doe"},
            parent=example,
            requirement_ratings={
                "unknown_id": {"rating": 4, "reason": "Good"},
            },
        )
        output.save_to_file()


def test_example_output_schema_validation(tmp_path):
    # Create a project, task, and example hierarchy
    project = Project(name="Test Project", path=(tmp_path / "test_project"))
    project.save_to_file()
    task = Task(
        name="Test Task",
        parent=project,
        output_json_schema=json.dumps(
            {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                "required": ["name", "age"],
            }
        ),
    )
    task.save_to_file()
    example = Example(
        input="Test input",
        source="human",
        parent=task,
        source_properties={"creator": "john_doe"},
    )
    example.save_to_file()

    # Create an example output with a valid schema
    valid_output = ExampleOutput(
        output='{"name": "John Doe", "age": 30}',
        source="human",
        source_properties={"creator": "john_doe"},
        parent=example,
    )
    valid_output.save_to_file()

    # changing to invalid output
    with pytest.raises(ValueError):
        valid_output.output = '{"name": "John Doe", "age": "thirty"}'
        valid_output.save_to_file()

    # Invalid case: output does not match task output schema
    with pytest.raises(ValueError):
        output = ExampleOutput(
            output='{"name": "John Doe", "age": "thirty"}',
            source="human",
            source_properties={"creator": "john_doe"},
            parent=example,
        )
        output.save_to_file()


def test_example_input_schema_validation(tmp_path):
    # Create a project and task hierarchy
    project = Project(name="Test Project", path=(tmp_path / "test_project"))
    project.save_to_file()
    task = Task(
        name="Test Task",
        parent=project,
        input_json_schema=json.dumps(
            {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                "required": ["name", "age"],
            }
        ),
    )
    task.save_to_file()

    # Create an example with a valid input schema
    valid_example = Example(
        input='{"name": "John Doe", "age": 30}',
        source=ExampleSource.human,
        parent=task,
    )
    valid_example.save_to_file()

    # Changing to invalid input
    with pytest.raises(ValueError):
        valid_example.input = '{"name": "John Doe", "age": "thirty"}'
        valid_example.save_to_file()

    # Invalid case: input does not match task input schema
    with pytest.raises(ValueError):
        example = Example(
            input='{"name": "John Doe", "age": "thirty"}',
            source=ExampleSource.human,
            parent=task,
        )
        example.save_to_file()


def test_valid_human_example_output():
    output = ExampleOutput(
        output="Test output",
        source=ExampleOutputSource.human,
        source_properties={"creator": "John Doe"},
    )
    assert output.source == ExampleOutputSource.human
    assert output.source_properties["creator"] == "John Doe"


def test_invalid_human_example_output_missing_creator():
    with pytest.raises(
        ValidationError,
        match="must include \['creator'\]",
    ):
        ExampleOutput(
            output="Test output", source=ExampleOutputSource.human, source_properties={}
        )


def test_invalid_human_example_output_empty_creator():
    with pytest.raises(ValidationError, match="must not be empty string"):
        ExampleOutput(
            output="Test output",
            source=ExampleOutputSource.human,
            source_properties={"creator": ""},
        )


def test_valid_synthetic_example_output():
    output = ExampleOutput(
        output="Test output",
        source=ExampleOutputSource.synthetic,
        source_properties={
            "adapter_name": "TestAdapter",
            "model_name": "GPT-4",
            "model_provider": "OpenAI",
            "prompt_builder_name": "TestPromptBuilder",
        },
    )
    assert output.source == ExampleOutputSource.synthetic
    assert output.source_properties["adapter_name"] == "TestAdapter"
    assert output.source_properties["model_name"] == "GPT-4"
    assert output.source_properties["model_provider"] == "OpenAI"
    assert output.source_properties["prompt_builder_name"] == "TestPromptBuilder"


def test_invalid_synthetic_example_output_missing_keys():
    with pytest.raises(
        ValidationError, match="example output source_properties must include"
    ):
        ExampleOutput(
            output="Test output",
            source=ExampleOutputSource.synthetic,
            source_properties={"adapter_name": "TestAdapter", "model_name": "GPT-4"},
        )


def test_invalid_synthetic_example_output_empty_values():
    with pytest.raises(ValidationError, match="must not be empty string"):
        ExampleOutput(
            output="Test output",
            source=ExampleOutputSource.synthetic,
            source_properties={
                "adapter_name": "TestAdapter",
                "model_name": "",
                "model_provider": "OpenAI",
                "prompt_builder_name": "TestPromptBuilder",
            },
        )


def test_invalid_synthetic_example_output_non_string_values():
    with pytest.raises(ValidationError, match="Input should be a valid string"):
        ExampleOutput(
            output="Test output",
            source=ExampleOutputSource.synthetic,
            source_properties={
                "adapter_name": "TestAdapter",
                "model_name": "GPT-4",
                "model_provider": "OpenAI",
                "prompt_builder_name": 123,
            },
        )

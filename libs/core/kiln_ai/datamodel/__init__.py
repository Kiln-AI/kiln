from __future__ import annotations

import json
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Dict, Self

import jsonschema
import jsonschema.exceptions
from kiln_ai.datamodel.json_schema import JsonObjectSchema, schema_from_json_str
from pydantic import Field, model_validator

from .basemodel import ID_TYPE, KilnBaseModel, KilnParentedModel, KilnParentModel
from .json_schema import validate_schema

if TYPE_CHECKING:
    from . import Task

# Conventions:
# 1) Names are filename safe as they may be used as file names. They are informational and not to be used in prompts/training/validation.
# 2) Descrptions are for Kiln users to describe/understanding the purpose of this object. They must never be used in prompts/training/validation. Use "instruction/requirements" instead.

# Filename compatible names
NAME_REGEX = r"^[A-Za-z0-9 _-]+$"
NAME_FIELD = Field(min_length=1, max_length=120, pattern=NAME_REGEX)


class Priority(IntEnum):
    p0 = 0
    p1 = 1
    p2 = 2
    p3 = 3


class ReasonRating(KilnBaseModel):
    """
    A combination of a rating (1-5 stars) and a reason for the rating.

    The reason should explain why the rating is given (why it's high when high, or why it's low when low).
    """

    rating: int = Field(description="The rating (1-5 stars).", ge=1, le=5)
    reason: str | None = Field(
        default=None,
        description="The reason for the rating. The reason may be used in training, prompts and evaluation so it should be readable, concise, informative and not reference data outside of the task/input/output.",
        max_length=750,
    )
    comment: str | None = Field(
        default=None,
        description="A comment about the rating. Will never be used in training/prompts/evaluation, so it can be anything, such as notes for the team.",
    )


class ExampleOutputSource(str, Enum):
    """
    The source of the example output.
    """

    human = "human"
    synthetic = "synthetic"


class ExampleOutput(KilnParentedModel):
    """
    An example output from a specific Example input, to a Task.
    """

    output: str = Field(
        description="The output of the task. JSON formatted for structured output, plaintext for unstructured output."
    )
    source: ExampleOutputSource = Field(
        description="The source of the example output: human or synthetic."
    )
    # TODO: add structure/validation to this. For human creator_id. Model ID and verion and provider for models
    source_properties: Dict[str, str] = Field(
        default={},
        description="Additional properties of the source, e.g. the user name of the human who provided the output or the model that generated the output.",
    )
    rating: ReasonRating | None = Field(
        default=None,
        description="The rating of the output, along with a reason this rating was given.",
    )
    requirement_ratings: Dict[ID_TYPE, ReasonRating] = Field(
        default={},
        description="The ratings of the requirements of the task, along with a reason this rating was given. The keys are the ids of the requirements.",
    )
    fixed_output: str | None = Field(
        default=None,
        description="An version of the output with issues fixed by a human evaluator. This must be a 'fixed' version of the existing output, and not an entirely new output. If you wish to generate an ideal curatorial output example for this task unrelated to this output, generate a new ExampleOutput with type 'human' instead of using this field.",
    )

    @classmethod
    def relationship_name(cls):
        return "outputs"

    @classmethod
    def parent_type(cls):
        return Example

    def parent_example(self) -> Example | None:
        if not isinstance(self.parent, Example):
            return None
        return self.parent

    # TODO validators for output and fixed_output: validate they follow the tas

    @model_validator(mode="after")
    def validate_output_format(self) -> Self:
        task = self.task_for_validation()
        if task is None:
            # don't validate this relationship until we have a path or parent. Give them time to build it (but will catch it before saving)
            return self

        # validate output
        if task.output_json_schema is not None:
            try:
                validate_schema(json.loads(self.output), task.output_json_schema)
            except json.JSONDecodeError:
                raise ValueError("Output is not a valid JSON object")
            except jsonschema.exceptions.ValidationError as e:
                raise ValueError(f"Output does not match task output schema: {e}")
        return self

    def task_for_validation(self) -> Task | None:
        example = self.parent
        if example is None:
            return None
        if not isinstance(example, Example):
            raise ValueError("ExampleOutput must have a valid parent Example")

        task = example.parent
        if task is None:
            return None
        if not isinstance(task, Task):
            raise ValueError(
                "ExampleOutput's parent Example must have a valid parent Task"
            )
        return task

    @model_validator(mode="after")
    def validate_requirement_rating_keys(self) -> Self:
        if len(self.requirement_ratings) == 0:
            return self
        task = self.task_for_validation()
        if task is None:
            # don't validate this relationship until we have a path or parent. Give them time to build it (but will catch it before saving)
            return self

        valid_requirement_ids = {req.id for req in task.requirements()}
        for key in self.requirement_ratings.keys():
            if key not in valid_requirement_ids:
                raise ValueError(
                    f"Requirement ID '{key}' is not a valid requirement ID for this task"
                )
        return self

    @model_validator(mode="after")
    def validate_source_properties(self) -> Self:
        if self.source == ExampleOutputSource.synthetic:
            required_keys = {
                "adapter_name",
                "model_name",
                "model_provider",
                "prompt_builder_name",
            }
        elif self.source == ExampleOutputSource.human:
            required_keys = {"creator"}
        else:
            raise ValueError(f"Invalid source type: {self.source}")

        missing_keys = []
        for key in required_keys:
            if key not in self.source_properties:
                missing_keys.append(key)
            elif self.source_properties[key] == "":
                raise ValueError(
                    f"example output source_properties[{key}] must not be empty string for {self.source} outputs"
                )
        if len(missing_keys) > 0:
            raise ValueError(
                f"example output source_properties must include {missing_keys} for {self.source} outputs"
            )
        return self


class ExampleSource(str, Enum):
    """
    The source of the example input.
    """

    human = "human"
    synthetic = "synthetic"


class Example(KilnParentedModel, KilnParentModel, parent_of={"outputs": ExampleOutput}):
    """
    An example input to a specific Task.
    """

    input: str = Field(
        description="The inputs to the task. JSON formatted for structured input, plaintext for unstructured input."
    )
    source: ExampleSource = Field(
        description="The source of the example input: human or synthetic."
    )
    # TODO add structure/validation to this. For human creator_id. Model: synthetic data tool and model version
    source_properties: Dict[str, str] = Field(
        default={},
        description="Additional properties of the source, e.g. the name of the human who provided the input or the model that generated the input.",
    )

    @classmethod
    def relationship_name(cls):
        return "examples"

    @classmethod
    def parent_type(cls):
        return Task

    # Needed for typechecking. TODO P2: fix this in KilnParentModel
    def outputs(self) -> list[ExampleOutput]:
        return super().outputs()  # type: ignore

    def parent_task(self) -> Task | None:
        if not isinstance(self.parent, Task):
            return None
        return self.parent

    @model_validator(mode="after")
    def validate_input_format(self) -> Self:
        task = self.parent
        if task is None:
            # don't validate this relationship until we have a path or parent. Give them time to build it (but will catch it before saving)
            return self
        if not isinstance(task, Task):
            raise ValueError(
                "ExampleOutput's parent Example must have a valid parent Task"
            )

        # validate output
        if task.input_json_schema is not None:
            try:
                validate_schema(json.loads(self.input), task.input_json_schema)
            except json.JSONDecodeError:
                raise ValueError("Input is not a valid JSON object")
            except jsonschema.exceptions.ValidationError as e:
                raise ValueError(f"Input does not match task input schema: {e}")
        return self


class TaskRequirement(KilnParentedModel):
    name: str = NAME_FIELD
    description: str = Field(default="")
    instruction: str = Field(default="")
    priority: Priority = Field(default=Priority.p2)

    @classmethod
    def relationship_name(cls):
        return "requirements"

    @classmethod
    def parent_type(cls):
        return Task


class TaskDeterminism(str, Enum):
    deterministic = "deterministic"  # Expect exact match
    semantic_match = "semantic_match"  # Expect same meaning, but flexible on expression of the meaning
    flexible = "flexible"  # Flexible on semantic output. Eval should be custom based on parsing requirements.


class Task(
    KilnParentedModel,
    KilnParentModel,
    parent_of={"requirements": TaskRequirement, "examples": Example},
):
    name: str = NAME_FIELD
    description: str = Field(default="")
    priority: Priority = Field(default=Priority.p2)
    determinism: TaskDeterminism = Field(default=TaskDeterminism.flexible)
    instruction: str = Field(default="")
    # TODO: make this required, or formalize the default message output schema
    output_json_schema: JsonObjectSchema | None = None
    input_json_schema: JsonObjectSchema | None = None

    def output_schema(self) -> Dict | None:
        if self.output_json_schema is None:
            return None
        return schema_from_json_str(self.output_json_schema)

    def input_schema(self) -> Dict | None:
        if self.input_json_schema is None:
            return None
        return schema_from_json_str(self.input_json_schema)

    @classmethod
    def relationship_name(cls):
        return "tasks"

    @classmethod
    def parent_type(cls):
        return Project

    # Needed for typechecking. TODO P2: fix this in KilnParentModel
    def requirements(self) -> list[TaskRequirement]:
        return super().requirements()  # type: ignore

    # Needed for typechecking. TODO P2: fix this in KilnParentModel
    def examples(self) -> list[Example]:
        return super().examples()  # type: ignore


class Project(KilnParentModel, parent_of={"tasks": Task}):
    name: str = NAME_FIELD
    description: str = Field(default="")

    # Needed for typechecking. TODO P2: fix this in KilnParentModel
    def tasks(self) -> list[Task]:
        return super().tasks()  # type: ignore

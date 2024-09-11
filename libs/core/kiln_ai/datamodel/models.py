from enum import Enum, IntEnum
from typing import Dict

from kiln_ai.datamodel.json_schema import JsonObjectSchema, schema_from_json_str
from pydantic import Field

from .basemodel import ID_TYPE, KilnBaseModel, KilnParentedModel

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
        description="Additional properties of the source, e.g. the name of the human who provided the output or the model that generated the output.",
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

    # TODO validators for output and fixed_output: validate they follow the tas
    # TODO validator that requirement_rating keys are requirement IDs


class ExampleSource(str, Enum):
    """
    The source of the example input.
    """

    human = "human"
    synthetic = "synthetic"


class Example(KilnParentedModel):
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

    def outputs(self) -> list[ExampleOutput]:
        return ExampleOutput.all_children_of_parent_path(self.path)


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


class Task(KilnParentedModel):
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

    def requirements(self) -> list[TaskRequirement]:
        return TaskRequirement.all_children_of_parent_path(self.path)

    def examples(self) -> list[Example]:
        return Example.all_children_of_parent_path(self.path)


class Project(KilnBaseModel):
    name: str = NAME_FIELD
    description: str = Field(default="")

    def tasks(self) -> list[Task]:
        return Task.all_children_of_parent_path(self.path)

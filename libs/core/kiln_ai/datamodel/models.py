import json
from enum import Enum, IntEnum
from typing import Dict

from kiln_ai.datamodel.json_schema import JsonObjectSchema, schema_from_json_str
from pydantic import Field

from .basemodel import KilnBaseModel, KilnParentedModel

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
        return schema_from_json_str(self.output_json_schema)

    def input_schema(self) -> Dict | None:
        return schema_from_json_str(self.input_json_schema)

    @classmethod
    def relationship_name(cls):
        return "tasks"

    @classmethod
    def parent_type(cls):
        return Project

    def requirements(self) -> list[TaskRequirement]:
        return TaskRequirement.all_children_of_parent_path(self.path)


class Project(KilnBaseModel):
    name: str = NAME_FIELD
    description: str = Field(default="")

    def tasks(self) -> list[Task]:
        return Task.all_children_of_parent_path(self.path)

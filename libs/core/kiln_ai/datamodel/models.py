from .basemodel import KilnBaseModel, KilnParentedModel
from pydantic import Field

NAME_REGEX = r"^[A-Za-z0-9 _-]+$"
NAME_FIELD = Field(min_length=1, max_length=120, pattern=NAME_REGEX)


# Child of Project
class Task(KilnParentedModel):
    name: str = NAME_FIELD

    @classmethod
    def relationship_name(cls):
        return "tasks"

    @classmethod
    def parent_type(cls):
        return Project


class Project(KilnBaseModel):
    name: str = NAME_FIELD

    def tasks(self) -> list[Task]:
        return Task.all_children_of_parent_path(self.path)

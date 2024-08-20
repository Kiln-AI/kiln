from .basemodel import KilnBaseModel, KilnParentedModel
from pydantic import Field

NAME_REGEX = r"^[A-Za-z0-9 _-]+$"
NAME_FIELD = Field(min_length=1, max_length=120, pattern=NAME_REGEX)


class Project(KilnBaseModel):
    name: str = NAME_FIELD


class Task(KilnParentedModel):
    name: str = NAME_FIELD

    def relationship_name(self) -> str:
        return "tasks"

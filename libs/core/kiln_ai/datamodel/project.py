from .basemodel import KilnBaseModel
from pydantic import Field

NAME_REGEX = r"^[A-Za-z0-9 _-]+$"
NAME_FIELD = Field(min_length=1, max_length=120, pattern=NAME_REGEX)


class KilnProject(KilnBaseModel):
    name: str = NAME_FIELD


class KilnTask(KilnBaseModel):
    name: str = NAME_FIELD

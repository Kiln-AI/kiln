from .basemodel import KilnBaseModel


class KilnProject(KilnBaseModel):
    name: str


class KilnTask(KilnBaseModel):
    name: str

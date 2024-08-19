from pydantic import BaseModel
from typing import Optional


class KilnProject(BaseModel):
    version: int = 1
    name: str
    path: Optional[str] = None

    def __init__(self, name: str, path: Optional[str] = None):
        # TODO: learn about pydantic init
        super().__init__(name=name, path=path)
        if path is not None and name is not None:
            # path and name are mutually exclusive for constructor, name comes from path if passed
            raise ValueError("path and name are mutually exclusive")

from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path
from typing import Type, TypeVar

T = TypeVar("T", bound="KilnBaseModel")


class KilnBaseModel(BaseModel):
    version: int = 1
    path: Optional[Path] = None

    @classmethod
    def load_from_file(cls: Type[T], path: Path) -> T:
        with open(path, "r") as file:
            m = cls.model_validate_json(file.read(), strict=True)
        m.path = path
        return m

    def save_to_file(self) -> None:
        if self.path is None:
            raise ValueError(
                f"Cannot save to file because 'path' is not set. Class: {self.__class__.__name__}, "
                f"id: {getattr(self, 'id', None)}, path: {self.path}"
            )
        data = self.model_dump(exclude={"path"})
        with open(self.path, "w") as file:
            json.dump(data, file, indent=4)

        print(f"Project saved to {self.path}")

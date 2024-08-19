from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path
from typing import Type, TypeVar

T = TypeVar("T", bound="KilnBaseModel")


class KilnBaseModel(BaseModel):
    v: int = 1  # schema_version
    path: Optional[Path] = None

    @classmethod
    def load_from_file(cls: Type[T], path: Path) -> T:
        with open(path, "r") as file:
            m = cls.model_validate_json(file.read(), strict=True)
        m.path = path
        if m.v > m.max_schema_version():
            raise ValueError(
                f"Cannot load from file because the schema version is higher than the current version. Upgrade kiln to the latest version. "
                f"Class: {m.__class__.__name__}, id: {getattr(m, 'id', None)}, path: {path}, "
                f"version: {m.v}, max version: {m.max_schema_version()}"
            )
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

    # increment for breaking changes
    def max_schema_version(self) -> int:
        return 1

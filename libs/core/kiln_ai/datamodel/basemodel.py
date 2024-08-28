import json
import re
import uuid
from abc import ABCMeta, abstractmethod
from builtins import classmethod
from pathlib import Path
from typing import Optional, Type, TypeVar

from pydantic import BaseModel, Field, computed_field, field_validator

# ID is a 10 digit hex string
ID_FIELD = Field(default_factory=lambda: uuid.uuid4().hex[:10].upper())
T = TypeVar("T", bound="KilnBaseModel")


def snake_case(s: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()


class KilnBaseModel(BaseModel):
    v: int = 1  # schema_version
    path: Optional[Path] = Field(default=None, exclude=True)

    @computed_field()
    def model_type(self) -> str:
        return self.type_name()

    # if changing the model name, should keep the original name here for parsing old files
    @classmethod
    def type_name(cls) -> str:
        return snake_case(cls.__name__)

    # used as /obj_folder/base_filename.kiln
    @classmethod
    def base_filename(cls) -> str:
        return cls.type_name() + ".kiln"

    @classmethod
    def load_from_folder(cls: Type[T], folderPath: Path) -> T:
        path = folderPath / cls.base_filename()
        return cls.load_from_file(path)

    @classmethod
    def load_from_file(cls: Type[T], path: Path) -> T:
        with open(path, "r") as file:
            file_data = file.read()
            # TODO P2 perf: parsing the JSON twice here.
            # Once for model_type, once for model. Can't call model_validate with parsed json because enum types break; they get strings instead of enums.
            parsed_json = json.loads(file_data)
            m = cls.model_validate_json(file_data, strict=True)
            file_data = None
        m.path = path
        if m.v > m.max_schema_version():
            raise ValueError(
                f"Cannot load from file because the schema version is higher than the current version. Upgrade kiln to the latest version. "
                f"Class: {m.__class__.__name__}, id: {getattr(m, 'id', None)}, path: {path}, "
                f"version: {m.v}, max version: {m.max_schema_version()}"
            )
        if parsed_json["model_type"] != cls.type_name():
            raise ValueError(
                f"Cannot load from file because the model type is incorrect. Expected {cls.type_name()}, got {parsed_json['model_type']}. "
                f"Class: {m.__class__.__name__}, id: {getattr(m, 'id', None)}, path: {path}, "
                f"version: {m.v}, max version: {m.max_schema_version()}"
            )
        return m

    def save_to_file(self) -> None:
        path = self.build_path()
        if path is None:
            raise ValueError(
                f"Cannot save to file because 'path' is not set. Class: {self.__class__.__name__}, "
                f"id: {getattr(self, 'id', None)}, path: {path}"
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        json_data = self.model_dump_json(indent=2)
        with open(path, "w") as file:
            file.write(json_data)
        # save the path so even if something like name changes, the file doesn't move
        self.path = path

    def build_path(self) -> Path | None:
        if self.path is not None:
            return self.path
        return None

    # increment for breaking changes
    def max_schema_version(self) -> int:
        return 1


class KilnParentedModel(KilnBaseModel, metaclass=ABCMeta):
    id: str = ID_FIELD
    parent: Optional[KilnBaseModel] = Field(default=None, exclude=True)

    @classmethod
    @abstractmethod
    def relationship_name(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def parent_type(cls) -> Type[KilnBaseModel]:
        pass

    @field_validator("parent")
    @classmethod
    def check_parent_type(cls, v: Optional[KilnBaseModel]) -> Optional[KilnBaseModel]:
        if v is not None:
            expected_parent_type = cls.parent_type()
            if not isinstance(v, expected_parent_type):
                raise ValueError(
                    f"Parent must be of type {expected_parent_type}, but was {type(v)}"
                )
        return v

    def build_child_dirname(self) -> Path:
        # Default implementation for readable folder names.
        # {id} - {name}/{type}.kiln
        path = self.id
        name = getattr(self, "name", None)
        if name is not None:
            path = f"{path} - {name[:32]}"
        return Path(path)

    def build_path(self) -> Path | None:
        # if specifically loaded from an existing path, keep that no matter what
        # this ensures the file structure is easy to use with git/version control
        # and that changes to things like name (which impacts default path) don't leave dangling files
        if self.path is not None:
            return self.path
        # Build a path under parent_folder/relationship/file.kiln
        if self.parent is None:
            return None
        parent_path = self.parent.build_path()
        if parent_path is None:
            return None
        parent_folder = parent_path.parent
        if parent_folder is None:
            return None
        return (
            parent_folder
            / self.relationship_name()
            / self.build_child_dirname()
            / self.__class__.base_filename()
        )

    @classmethod
    def all_children_of_parent_path(cls: Type[T], parent_path: Path | None) -> list[T]:
        if parent_path is None:
            raise ValueError("Parent path must be set to load children")
        # Determine the parent folder
        if parent_path.is_file():
            parent_folder = parent_path.parent
        else:
            parent_folder = parent_path

        # Ignore type error: this is abstract base class, but children must implement relationship_name
        relationship_folder = parent_folder / Path(cls.relationship_name())  # type: ignore

        if not relationship_folder.exists() or not relationship_folder.is_dir():
            return []

        # Collect all /relationship/{id}/{base_filename.kiln} files in the relationship folder
        children = []
        for child_file in relationship_folder.glob(f"**/{cls.base_filename()}"):
            child = cls.load_from_file(child_file)
            children.append(child)

        return children

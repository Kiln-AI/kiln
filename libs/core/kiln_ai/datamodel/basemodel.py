from pydantic import BaseModel, computed_field, Field, field_validator
from typing import Optional
from pathlib import Path
from typing import Type, TypeVar
from abc import ABCMeta, abstractmethod
import uuid
from builtins import classmethod


# ID is a 10 digit hex string
ID_FIELD = Field(default_factory=lambda: uuid.uuid4().hex[:10].upper())
T = TypeVar("T", bound="KilnBaseModel")


class KilnBaseModel(BaseModel):
    v: int = 1  # schema_version
    path: Optional[Path] = Field(default=None, exclude=True)

    @computed_field()
    def type(self) -> str:
        return self.type_name()

    # override this to set the type name explicitly
    def type_name(self) -> str:
        return self.__class__.__name__

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

    @abstractmethod
    def relationship_name(self) -> str:
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

    def build_child_filename(self) -> Path:
        # Default implementation for readable filenames.
        # Can be overridden, but probably shouldn't be.
        # {id} - {name}.kiln
        path = self.id
        name = getattr(self, "name", None)
        if name is not None:
            path = f"{path} - {name[:32]}"
        path = f"{path}.kiln"
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
        return parent_folder / self.relationship_name() / self.build_child_filename()

    @classmethod
    def all_children_of_parent_path(cls, parent_path: Path) -> list:
        # Determine the parent folder
        if parent_path.is_file():
            parent_folder = parent_path.parent
        else:
            parent_folder = parent_path

        rn = cls().relationship_name()
        print(rn)
        relationship_folder = parent_folder / cls().relationship_name()

        if not relationship_folder.exists() or not relationship_folder.is_dir():
            return []

        # Collect all .kiln files in the relationship folder
        children = []
        for child_file in relationship_folder.glob("*.kiln"):
            child = cls.load_from_file(child_file)
            children.append(child)

        return children

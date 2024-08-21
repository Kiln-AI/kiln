import json
import pytest
from kiln_ai.datamodel.basemodel import KilnBaseModel, KilnParentedModel
from pathlib import Path
from typing import Optional


@pytest.fixture
def test_file(tmp_path) -> Path:
    test_file_path = tmp_path / "test_model.json"
    data = {"v": 1}

    with open(test_file_path, "w") as file:
        json.dump(data, file, indent=4)

    return test_file_path


@pytest.fixture
def test_newer_file(tmp_path) -> Path:
    test_file_path = tmp_path / "test_model_sv.json"
    data = {"v": 99}

    with open(test_file_path, "w") as file:
        json.dump(data, file, indent=4)

    return test_file_path


def test_load_from_file(test_file):
    model = KilnBaseModel.load_from_file(test_file)
    assert model.v == 1
    assert model.path == test_file


def test_save_to_file(test_file):
    model = KilnBaseModel(path=test_file)
    model.save_to_file()

    with open(test_file, "r") as file:
        data = json.load(file)

    assert data["v"] == 1


def test_save_to_file_without_path():
    model = KilnBaseModel()
    with pytest.raises(ValueError):
        model.save_to_file()


def test_max_schema_version(test_newer_file):
    with pytest.raises(ValueError):
        KilnBaseModel.load_from_file(test_newer_file)


def test_type_name():
    model = KilnBaseModel()
    assert model.type == "KilnBaseModel"


# Instance of the parented model for abstract methods
class NamedParentedModel(KilnParentedModel):
    @classmethod
    def relationship_name(cls) -> str:
        return "tests"

    @classmethod
    def parent_type(cls):
        return KilnBaseModel


def test_parented_model_path_gen(tmp_path):
    parent = KilnBaseModel(path=tmp_path)
    child = NamedParentedModel(parent=parent)
    child_path = child.build_path()
    assert child_path.name == "named_parented_model.kiln"
    assert child_path.parent.name == child.id
    assert child_path.parent.parent.name == "tests"
    assert child_path.parent.parent.parent == tmp_path.parent


class BaseParentExample(KilnBaseModel):
    pass


# Instance of the parented model for abstract methods, with default name builder
class DefaultParentedModel(KilnParentedModel):
    name: Optional[str] = None

    @classmethod
    def relationship_name(self):
        return "children"

    @classmethod
    def parent_type(cls):
        return BaseParentExample


def test_build_default_child_filename(tmp_path):
    parent = BaseParentExample(path=tmp_path)
    child = DefaultParentedModel(parent=parent)
    child_path = child.build_path()
    assert child_path.name == "default_parented_model.kiln"
    assert child_path.parent.name == child.id
    assert child_path.parent.parent.name == "children"
    assert child_path.parent.parent.parent == tmp_path.parent
    # now with name
    child = DefaultParentedModel(parent=parent, name="Name")
    child_path = child.build_path()
    assert child_path.name == "default_parented_model.kiln"
    assert child_path.parent.name == child.id + " - Name"
    assert child_path.parent.parent.name == "children"
    assert child_path.parent.parent.parent == tmp_path.parent


def test_serialize_child(tmp_path):
    parent = BaseParentExample(path=tmp_path)
    child = DefaultParentedModel(parent=parent, name="Name")

    expected_path = child.build_path()
    assert child.path is None
    child.save_to_file()

    # ensure we save exact path
    assert child.path is not None
    assert child.path == expected_path

    # should have made the directory, and saved the file
    with open(child.path, "r") as file:
        data = json.load(file)

    assert data["v"] == 1
    assert data["name"] == "Name"
    assert data["type"] == "DefaultParentedModel"
    assert len(data["id"]) == 10
    assert child.path.parent.name == child.id + " - Name"
    assert child.path.parent.parent.name == "children"
    assert child.path.parent.parent.parent == tmp_path.parent

    # change name, see it serializes, but path stays the same
    child.name = "Name2"
    child.save_to_file()
    assert child.path == expected_path
    with open(child.path, "r") as file:
        data = json.load(file)
    assert data["name"] == "Name2"


def test_save_to_set_location(tmp_path):
    # Keeps the OG path if parent and path are both set
    parent = BaseParentExample(path=tmp_path)
    child_path = tmp_path.parent / "child.kiln"
    child = DefaultParentedModel(path=child_path, parent=parent, name="Name")
    assert child.build_path() == child_path

    # check file created at child_path, not the default smart path
    assert not child_path.exists()
    child.save_to_file()
    assert child_path.exists()

    # if we don't set the path, use the parent + smartpath
    child2 = DefaultParentedModel(parent=parent, name="Name2")
    assert child2.build_path().parent.name == child2.id + " - Name2"
    assert child2.build_path().parent.parent.name == "children"
    assert child2.build_path().parent.parent.parent == tmp_path.parent


def test_parent_without_path():
    # no path from parent or direct path
    parent = BaseParentExample()
    child = DefaultParentedModel(parent=parent, name="Name")
    with pytest.raises(ValueError):
        child.save_to_file()


def test_parent_wrong_type():
    # DefaultParentedModel is parented to BaseParentExample, not KilnBaseModel
    parent = KilnBaseModel()
    with pytest.raises(ValueError):
        DefaultParentedModel(parent=parent, name="Name")


def test_load_children(test_file):
    # Set up parent and children models
    parent = BaseParentExample.load_from_file(test_file)

    child1 = DefaultParentedModel(parent=parent, name="Child1")
    child2 = DefaultParentedModel(parent=parent, name="Child2")
    child3 = DefaultParentedModel(parent=parent, name="Child3")

    # Ensure the children are saved correctly
    child1.save_to_file()
    child2.save_to_file()
    child3.save_to_file()

    # Load children from parent path
    children = DefaultParentedModel.all_children_of_parent_path(test_file)

    # Verify that all children are loaded correctly
    assert len(children) == 3
    names = [child.name for child in children]
    assert "Child1" in names
    assert "Child2" in names
    assert "Child3" in names
    assert all(child.type == "DefaultParentedModel" for child in children)


def test_base_filename():
    model = DefaultParentedModel(name="Test")
    assert model.base_filename() == "default_parented_model.kiln"
    model = NamedParentedModel(name="Test")
    assert model.base_filename() == "named_parented_model.kiln"
    assert NamedParentedModel.base_filename() == "named_parented_model.kiln"


def test_load_from_folder(test_file):
    parent = BaseParentExample.load_from_file(test_file)
    child1 = DefaultParentedModel(parent=parent, name="Child1")
    child1.save_to_file()

    loaded_child1 = DefaultParentedModel.load_from_folder(child1.path.parent)
    assert loaded_child1.name == "Child1"

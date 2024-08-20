import json
import pytest
from kiln_ai.datamodel.project import Project


@pytest.fixture
def test_file(tmp_path):
    test_file_path = tmp_path / "test_project.json"
    data = {"v": 1, "name": "Test Project"}

    with open(test_file_path, "w") as file:
        json.dump(data, file, indent=4)

    return test_file_path


def test_load_from_file(test_file):
    project = Project.load_from_file(test_file)
    assert project.v == 1
    assert project.name == "Test Project"
    assert project.path == test_file


def test_save_to_file(test_file):
    project = Project(name="Test Project", path=test_file)
    project.save_to_file()

    with open(test_file, "r") as file:
        data = json.load(file)

    assert data["v"] == 1
    assert data["name"] == "Test Project"


def test_save_to_file_without_path():
    project = Project(name="Test Project")
    with pytest.raises(ValueError):
        project.save_to_file()


def test_name_validation():
    Project(name="Test Project")
    Project(name="Te st_Proj-ect 1234567890")
    Project(name=("a" * 120))  # longest

    # a string with 120 characters

    with pytest.raises(ValueError):
        Project(name="Test Project!")
        Project(name="Test.Project")
        Project(name=("a" * 121))  # too long
        Project(name=("a"))  # too short


def test_auto_type_name():
    model = Project(name="Test Project")
    assert model.type == "Project"

import json
import pytest
from kiln_ai.datamodel.project import KilnProject


@pytest.fixture
def test_file(tmp_path):
    test_file_path = tmp_path / "test_project.json"
    data = {"version": 1, "name": "Test Project"}

    with open(test_file_path, "w") as file:
        json.dump(data, file, indent=4)

    return test_file_path


def test_load_from_file(test_file):
    project = KilnProject.load_from_file(test_file)
    assert project.version == 1
    assert project.name == "Test Project"
    assert project.path == test_file


def test_save_to_file(test_file):
    project = KilnProject(name="Test Project", path=test_file)
    project.save_to_file()

    with open(test_file, "r") as file:
        data = json.load(file)

    assert data["version"] == 1
    assert data["name"] == "Test Project"


def test_save_to_file_without_path():
    project = KilnProject(name="Test Project")
    with pytest.raises(ValueError):
        project.save_to_file()
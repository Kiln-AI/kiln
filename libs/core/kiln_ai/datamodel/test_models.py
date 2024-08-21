import json
import pytest
from kiln_ai.datamodel.models import Project, Task


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


def test_project_init():
    project = Project(name="test")
    assert project.name == "test"


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
    Project(name="Te st_Proj- 1234567890")
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


def test_load_tasks(test_file):
    # Set up a project model
    project = Project.load_from_file(test_file)

    # Set up multiple task models under the project
    task1 = Task(parent=project, name="Task1")
    task2 = Task(parent=project, name="Task2")
    task3 = Task(parent=project, name="Task3")

    # Ensure the tasks are saved correctly
    task1.save_to_file()
    task2.save_to_file()
    task3.save_to_file()

    # Load tasks from the project
    # tasks = project.tasks()
    tasks = Task.all_children_of_parent_path(test_file)

    # Verify that all tasks are loaded correctly
    assert len(tasks) == 3
    names = [task.name for task in tasks]
    assert "Task1" in names
    assert "Task2" in names
    assert "Task3" in names
    assert all(task.type == "Task" for task in tasks)


# verify error on non-saved model
def test_load_children_no_path(test_file):
    project = Project(name="Test Project")
    with pytest.raises(ValueError):
        project.tasks()

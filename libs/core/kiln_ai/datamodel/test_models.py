import json
import pytest
from kiln_ai.datamodel.models import Project, Task, TaskType


@pytest.fixture
def test_project_file(tmp_path):
    test_file_path = tmp_path / "project.json"
    data = {"v": 1, "name": "Test Project", "model_type": "project"}

    with open(test_file_path, "w") as file:
        json.dump(data, file, indent=4)

    return test_file_path


@pytest.fixture
def test_task_file(tmp_path):
    test_file_path = tmp_path / "task.json"
    data = {"v": 1, "name": "Test Task", "model_type": "task"}

    with open(test_file_path, "w") as file:
        json.dump(data, file, indent=4)

    return test_file_path


def test_load_from_file(test_project_file):
    project = Project.load_from_file(test_project_file)
    assert project.v == 1
    assert project.name == "Test Project"
    assert project.path == test_project_file


def test_project_init():
    project = Project(name="test")
    assert project.name == "test"


def test_save_to_file(test_project_file):
    project = Project(
        name="Test Project", description="Test Description", path=test_project_file
    )
    project.save_to_file()

    with open(test_project_file, "r") as file:
        data = json.load(file)

    assert data["v"] == 1
    assert data["name"] == "Test Project"
    assert data["description"] == "Test Description"


def test_task_serialization(test_project_file):
    project = Project.load_from_file(test_project_file)
    task = Task(
        parent=project,
        name="Test Task",
        type=TaskType.LANG_SINGLE,
        description="Test Description",
        instruction="Test Base Task Instruction",
    )

    task.save_to_file()

    parsed_task = Task.all_children_of_parent_path(test_project_file)[0]
    assert parsed_task.name == "Test Task"
    assert parsed_task.description == "Test Description"
    assert parsed_task.instruction == "Test Base Task Instruction"


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
    assert model.model_type == "project"


def test_load_tasks(test_project_file):
    # Set up a project model
    project = Project.load_from_file(test_project_file)

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
    tasks = Task.all_children_of_parent_path(test_project_file)

    # Verify that all tasks are loaded correctly
    assert len(tasks) == 3
    names = [task.name for task in tasks]
    assert "Task1" in names
    assert "Task2" in names
    assert "Task3" in names
    assert all(task.model_type == "task" for task in tasks)


# verify error on non-saved model
def test_load_children_no_path():
    project = Project(name="Test Project")
    with pytest.raises(ValueError):
        project.tasks()


def test_check_model_type(test_project_file, test_task_file):
    project = Project.load_from_file(test_project_file)
    task = Task.load_from_file(test_task_file)
    assert project.model_type == "project"
    assert task.model_type == "task"

    with pytest.raises(ValueError):
        project = Project.load_from_file(test_task_file)

    with pytest.raises(ValueError):
        task = Task.load_from_file(test_project_file)

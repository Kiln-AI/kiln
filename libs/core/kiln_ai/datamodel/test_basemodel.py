import json
import pytest
from kiln_ai.datamodel.basemodel import KilnBaseModel


@pytest.fixture
def test_file(tmp_path):
    test_file_path = tmp_path / "test_model.json"
    data = {"version": 1}

    with open(test_file_path, "w") as file:
        json.dump(data, file, indent=4)

    return test_file_path


def test_load_from_file(test_file):
    model = KilnBaseModel.load_from_file(test_file)
    assert model.version == 1
    assert model.path == test_file


def test_save_to_file(test_file):
    model = KilnBaseModel(path=test_file)
    model.save_to_file()

    with open(test_file, "r") as file:
        data = json.load(file)

    assert data["version"] == 1


def test_save_to_file_without_path():
    model = KilnBaseModel()
    with pytest.raises(ValueError):
        model.save_to_file()

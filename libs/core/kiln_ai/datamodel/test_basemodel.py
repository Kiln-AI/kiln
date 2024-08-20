import json
import pytest
from kiln_ai.datamodel.basemodel import KilnBaseModel
from pathlib import Path


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

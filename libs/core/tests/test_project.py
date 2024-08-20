import kiln_ai.coreadd as coreadd
import kiln_ai.datamodel as datamodel


def test_coreadd():
    assert coreadd.add(1, 1) == 2


def test_project_init():
    project = datamodel.Project(name="test")
    assert project.name == "test"

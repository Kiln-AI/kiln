import kilnai.coreadd as coreadd
import kilnai.datamodel as datamodel


def test_coreadd():
    assert coreadd.add(1, 1) == 2


def test_project_init():
    project = datamodel.KilnProject(name="test")
    assert project.name == "test"

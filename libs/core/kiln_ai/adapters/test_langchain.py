import kiln_ai.datamodel.models as models
import kiln_ai.adapters.langchain_adapter as ad
import pytest
import os

from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()


async def test_langchain(tmp_path):
    if os.getenv("GROQ_API_KEY") is None:
        pytest.skip("GROQ_API_KEY not set")

    project = models.Project(name="test", path=tmp_path / "test.kiln")
    project.save_to_file()
    assert project.name == "test"

    task = models.Task(parent=project, name="test task")
    task.save_to_file()
    assert task.name == "test task"
    task.instruction = (
        "You are an assistant which performs math tasks provided in plain text."
    )

    r1 = models.TaskRequirement(
        parent=task,
        name="BEDMAS",
        instruction="You follow order of mathematical operation (BEDMAS)",
    )
    r1.save_to_file()
    r2 = models.TaskRequirement(
        parent=task,
        name="only basic math",
        instruction="If the problem has anything other than addition, subtraction, multiplication, division, and brackets, you will not answer it. Reply instead with 'I'm just a basic calculator, I don't know how to do that'.",
    )
    r2.save_to_file()
    assert len(task.requirements()) == 2

    adapter = ad.ExperimentalKilnAdapter(task)
    answer = await adapter.run()
    assert "64" in answer

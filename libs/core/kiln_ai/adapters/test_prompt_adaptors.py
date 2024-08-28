import kiln_ai.datamodel.models as models
from kiln_ai.adapters.prompt_adapters import SimplePromptAdapter
import pytest
import os
from pathlib import Path


@pytest.mark.paid
async def test_groq(tmp_path):
    if os.getenv("GROQ_API_KEY") is None:
        pytest.skip("GROQ_API_KEY not set")
    await run_simple_test(tmp_path, "llama_3_1_8b", "groq")


@pytest.mark.paid
async def test_openai(tmp_path):
    if os.getenv("OPENAI_API_KEY") is None:
        pytest.skip("OPENAI_API_KEY not set")
    await run_simple_test(tmp_path, "gpt_4o_mini", "openai")


@pytest.mark.paid
async def test_amazon_bedrock(tmp_path):
    if (
        os.getenv("AWS_SECRET_ACCESS_KEY") is None
        or os.getenv("AWS_ACCESS_KEY_ID") is None
    ):
        pytest.skip("AWS keys not set")
    await run_simple_test(tmp_path, "llama_3_1_8b", "amazon_bedrock")


async def test_mock(tmp_path):
    task = build_test_task(tmp_path)
    adapter = SimplePromptAdapter(task, model_name="fake_parrot", provider="mock")
    answer = await adapter.run(
        "You should answer the following question: four plus six times 10"
    )
    assert "mock response" in answer


def build_test_task(tmp_path: Path):
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
    return task


async def run_simple_test(tmp_path: Path, model_name: str, provider: str):
    task = build_test_task(tmp_path)
    adapter = SimplePromptAdapter(task, model_name=model_name, provider=provider)
    answer = await adapter.run(
        "You should answer the following question: four plus six times 10"
    )
    assert "64" in answer

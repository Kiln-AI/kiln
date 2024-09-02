import os
from pathlib import Path

import kiln_ai.datamodel.models as models
import pytest
from kiln_ai.adapters.ml_model_list import built_in_models, ollama_online
from kiln_ai.adapters.prompt_adapters import SimplePromptAdapter
from langchain_core.language_models.fake_chat_models import FakeListChatModel


@pytest.mark.paid
async def test_groq(tmp_path):
    if os.getenv("GROQ_API_KEY") is None:
        pytest.skip("GROQ_API_KEY not set")
    await run_simple_test(tmp_path, "llama_3_1_8b", "groq")


@pytest.mark.ollama
async def test_ollama_phi(tmp_path):
    # Check if Ollama API is running
    if not await ollama_online():
        pytest.skip("Ollama API not running. Expect it running on localhost:11434")

    await run_simple_test(tmp_path, "phi_3_5", "ollama")


@pytest.mark.ollama
async def test_autoselect_provider(tmp_path):
    # Check if Ollama API is running
    if not await ollama_online():
        pytest.skip("Ollama API not running. Expect it running on localhost:11434")

    await run_simple_test(tmp_path, "phi_3_5")


@pytest.mark.ollama
async def test_ollama_llama(tmp_path):
    # Check if Ollama API is running
    if not await ollama_online():
        pytest.skip("Ollama API not running. Expect it running on localhost:11434")

    await run_simple_test(tmp_path, "llama_3_1_8b", "ollama")


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
    mockChatModel = FakeListChatModel(responses=["mock response"])
    adapter = SimplePromptAdapter(task, custom_model=mockChatModel)
    answer = await adapter.run("You are a mock, send me the response!")
    assert "mock response" in answer


@pytest.mark.paid
@pytest.mark.ollama
async def test_all_built_in_models(tmp_path):
    task = build_test_task(tmp_path)
    for model in built_in_models:
        for provider in model.providers:
            try:
                print(f"Running {model.model_name} {provider.name}")
                await run_simple_task(task, model.model_name, provider.name)
            except Exception as e:
                raise RuntimeError(
                    f"Error running {model.model_name} {provider}"
                ) from e


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


async def run_simple_test(tmp_path: Path, model_name: str, provider: str | None = None):
    task = build_test_task(tmp_path)
    return await run_simple_task(task, model_name, provider)


async def run_simple_task(task: models.Task, model_name: str, provider: str):
    adapter = SimplePromptAdapter(task, model_name=model_name, provider=provider)
    answer = await adapter.run(
        "You should answer the following question: four plus six times 10"
    )
    assert "64" in answer

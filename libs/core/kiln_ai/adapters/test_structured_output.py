from pathlib import Path
from typing import Dict

import kiln_ai.datamodel.models as models
import pytest
from kiln_ai.adapters.base_adapter import BaseAdapter
from kiln_ai.adapters.langchain_adapters import LangChainPromptAdapter
from kiln_ai.adapters.ml_model_list import (
    built_in_models,
    ollama_online,
)
from kiln_ai.datamodel.test_models import json_joke_schema


@pytest.mark.paid
async def test_structured_output_groq(tmp_path):
    await run_structured_output_test(tmp_path, "llama_3_1_8b", "groq")


@pytest.mark.paid
async def test_structured_output_bedrock(tmp_path):
    await run_structured_output_test(tmp_path, "llama_3_1_8b", "amazon_bedrock")


@pytest.mark.ollama
async def test_structured_output_ollama_phi(tmp_path):
    # https://python.langchain.com/v0.2/docs/how_to/structured_output/#advanced-specifying-the-method-for-structuring-outputs
    pytest.skip(
        "not working yet - phi3.5 does not support tools. Need json_mode + format in prompt"
    )
    await run_structured_output_test(tmp_path, "phi_3_5", "ollama")


@pytest.mark.ollama
async def test_structured_output_gpt_4o_mini(tmp_path):
    await run_structured_output_test(tmp_path, "gpt_4o_mini", "openai")


@pytest.mark.ollama
async def test_structured_output_ollama_llama(tmp_path):
    if not await ollama_online():
        pytest.skip("Ollama API not running. Expect it running on localhost:11434")
    await run_structured_output_test(tmp_path, "llama_3_1_8b", "ollama")


class MockAdapter(BaseAdapter):
    def __init__(self, kiln_task: models.Task, response: Dict | str | None):
        super().__init__(kiln_task)
        self.response = response

    async def _run(self, input: str) -> Dict | str:
        return self.response


async def test_mock_unstructred_response(tmp_path):
    task = build_structured_output_test_task(tmp_path)

    # don't error on valid response
    adapter = MockAdapter(task, response={"setup": "asdf", "punchline": "asdf"})
    answer = await adapter.invoke("You are a mock, send me the response!")
    assert answer["setup"] == "asdf"
    assert answer["punchline"] == "asdf"

    # error on response that doesn't match schema
    adapter = MockAdapter(task, response={"setup": "asdf"})
    with pytest.raises(Exception):
        answer = await adapter.invoke("You are a mock, send me the response!")

    adapter = MockAdapter(task, response="string instead of dict")
    with pytest.raises(RuntimeError):
        # Not a structed response so should error
        answer = await adapter.invoke("You are a mock, send me the response!")

    # Should error, expecting a string, not a dict
    project = models.Project(name="test", path=tmp_path / "test.kiln")
    task = models.Task(parent=project, name="test task")
    task.instruction = (
        "You are an assistant which performs math tasks provided in plain text."
    )
    adapter = MockAdapter(task, response={"dict": "value"})
    with pytest.raises(RuntimeError):
        answer = await adapter.invoke("You are a mock, send me the response!")


@pytest.mark.paid
@pytest.mark.ollama
async def test_all_built_in_models_structured_output(tmp_path):
    for model in built_in_models:
        if not model.supports_structured_output:
            print(
                f"Skipping {model.name} because it does not support structured output"
            )
            continue
        for provider in model.providers:
            if not provider.supports_structured_output:
                print(
                    f"Skipping {model.name} {provider.name} because it does not support structured output"
                )
                continue
            try:
                print(f"Running {model.name} {provider}")
                await run_structured_output_test(tmp_path, model.name, provider.name)
            except Exception as e:
                raise RuntimeError(f"Error running {model.name} {provider}") from e


def build_structured_output_test_task(tmp_path: Path):
    project = models.Project(name="test", path=tmp_path / "test.kiln")
    project.save_to_file()
    task = models.Task(
        parent=project,
        name="test task",
        instruction="You are an assistant which tells a joke, given a subject.",
    )
    task.output_json_schema = json_joke_schema
    schema = task.output_schema()
    assert schema is not None
    assert schema["properties"]["setup"]["type"] == "string"
    assert schema["properties"]["punchline"]["type"] == "string"
    task.save_to_file()
    assert task.name == "test task"
    assert len(task.requirements()) == 0
    return task


async def run_structured_output_test(tmp_path: Path, model_name: str, provider: str):
    task = build_structured_output_test_task(tmp_path)
    a = LangChainPromptAdapter(task, model_name=model_name, provider=provider)
    parsed = await a.invoke("Cows")  # a joke about cows
    if parsed is None or not isinstance(parsed, Dict):
        raise RuntimeError(f"structured response is not a dict: {parsed}")
    assert parsed["setup"] is not None
    assert parsed["punchline"] is not None
    if "rating" in parsed and parsed["rating"] is not None:
        rating = parsed["rating"]
        # Note: really should be an int according to json schema, but mistral returns a string
        if isinstance(rating, str):
            rating = int(rating)
        assert rating >= 0
        assert rating <= 10

import json
from pathlib import Path

import kiln_ai.datamodel.models as models
import pytest
from kiln_ai.adapters.ml_model_list import model_options
from kiln_ai.adapters.prompt_adapters import SimplePromptAdapter
from kiln_ai.datamodel.test_models import json_joke_schema


@pytest.mark.paid
async def test_structured_output_groq(tmp_path):
    await run_structured_output_test(tmp_path, "llama_3_1_8b", "groq")


@pytest.mark.paid
async def test_all_built_in_models_structured_output(tmp_path):
    # iterate all options in model_options
    for model_name in model_options:
        for provider in model_options[model_name]:
            await run_structured_output_test(tmp_path, model_name, provider)


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
    a = SimplePromptAdapter(task, model_name="llama_3_1_8b", provider="groq")
    result = await a.run("Cows")  # a joke about cows
    parsed = json.loads(result)
    assert parsed["setup"] is not None
    assert parsed["punchline"] is not None
    rating = parsed["rating"]
    if rating is not None:
        assert rating >= 0
        assert rating <= 10

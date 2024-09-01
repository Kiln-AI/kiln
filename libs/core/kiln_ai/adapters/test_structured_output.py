import json

import kiln_ai.datamodel.models as models
import pytest
from kiln_ai.adapters.prompt_adapters import SimplePromptAdapter
from kiln_ai.datamodel.test_models import json_joke_schema


@pytest.mark.paid
async def test_structured_output(tmp_path):
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
    a = SimplePromptAdapter(task, model_name="llama_3_1_8b", provider="groq")
    result = await a.run("Cows")  # a joke about cows
    parsed = json.loads(result)
    assert parsed["setup"] is not None
    assert parsed["punchline"] is not None
    rating = parsed["rating"]
    if rating is not None:
        assert rating >= 0
        assert rating <= 10

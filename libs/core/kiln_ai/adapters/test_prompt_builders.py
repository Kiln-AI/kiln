from kiln_ai.adapters.base_adapter import BaseAdapter
from kiln_ai.adapters.prompt_builders import SimplePromptBuilder
from kiln_ai.adapters.test_prompt_adaptors import build_test_task
from kiln_ai.adapters.test_structured_output import build_structured_output_test_task


def test_simple_prompt_builder(tmp_path):
    task = build_test_task(tmp_path)
    builder = SimplePromptBuilder(task=task)
    input = "two plus two"
    prompt = builder.build_prompt(input)
    assert (
        "You are an assistant which performs math tasks provided in plain text."
        in prompt
    )

    # TODO this should be a user message later
    assert input in prompt

    assert "1) " + task.requirements()[0].instruction in prompt
    assert "2) " + task.requirements()[1].instruction in prompt
    assert "3) " + task.requirements()[2].instruction in prompt


class MockAdapter(BaseAdapter):
    def adapter_specific_instructions(self) -> str | None:
        return "You are a mock, send me the response!"

    def _run(self, input: str) -> str:
        return "mock response"


def test_simple_prompt_builder_structured_output(tmp_path):
    task = build_structured_output_test_task(tmp_path)
    builder = SimplePromptBuilder(task=task)
    builder.adapter = MockAdapter(task)
    input = "Cows"
    prompt = builder.build_prompt(input)
    assert "You are an assistant which tells a joke, given a subject." in prompt

    # TODO this should be a user message later
    assert input in prompt

    # check adapter instructions are included
    assert "You are a mock, send me the response!" in prompt

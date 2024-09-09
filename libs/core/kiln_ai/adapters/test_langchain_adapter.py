from kiln_ai.adapters.langchain_adapters import LangChainPromptAdapter
from kiln_ai.adapters.test_prompt_adaptors import build_test_task


def test_langchain_adapter_munge_response(tmp_path):
    task = build_test_task(tmp_path)
    lca = LangChainPromptAdapter(
        kiln_task=task, model_name="gpt_4o_mini", provider="openai"
    )
    # Mistral Large tool calling format is a bit different
    response = {
        "name": "task_response",
        "arguments": {
            "setup": "Why did the cow join a band?",
            "punchline": "Because she wanted to be a moo-sician!",
        },
    }
    munged = lca._munge_response(response)
    assert munged["setup"] == "Why did the cow join a band?"
    assert munged["punchline"] == "Because she wanted to be a moo-sician!"

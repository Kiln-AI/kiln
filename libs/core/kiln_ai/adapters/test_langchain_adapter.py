from kiln_ai.adapters.langchain_adapters import LangChainPromptAdapter
from kiln_ai.adapters.test_prompt_adaptors import build_test_task
from langchain_groq import ChatGroq


def test_langchain_adapter_munge_response(tmp_path):
    task = build_test_task(tmp_path)
    lca = LangChainPromptAdapter(
        kiln_task=task, model_name="llama_3_1_8b", provider="ollama"
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

    # non mistral format should continue to work
    munged = lca._munge_response(response["arguments"])
    assert munged["setup"] == "Why did the cow join a band?"
    assert munged["punchline"] == "Because she wanted to be a moo-sician!"


def test_langchain_adapter_infer_model_name(tmp_path):
    task = build_test_task(tmp_path)
    custom = ChatGroq(model="llama-3.1-8b-instant", groq_api_key="test")

    lca = LangChainPromptAdapter(kiln_task=task, custom_model=custom)

    model_info = lca.adapter_info()
    assert model_info.model_name == "custom.langchain:llama-3.1-8b-instant"
    assert model_info.model_provider == "custom.langchain:ChatGroq"


def test_langchain_adapter_info(tmp_path):
    task = build_test_task(tmp_path)

    lca = LangChainPromptAdapter(
        kiln_task=task, model_name="llama_3_1_8b", provider="ollama"
    )

    model_info = lca.adapter_info()
    assert model_info.adapter_name == "kiln_langchain_adapter"
    assert model_info.model_name == "llama_3_1_8b"
    assert model_info.model_provider == "ollama"

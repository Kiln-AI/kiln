from enum import Enum
from typing import Dict

from langchain_aws import ChatBedrock
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI


class ModelName(str, Enum):
    llama_3_1_8b = "llama_3_1_8b"
    gpt_4o_mini = "gpt_4o_mini"
    gpt_4o = "gpt_4o"


class ModelProviders(str, Enum):
    openai = "openai"
    groq = "groq"
    amazon_bedrock = "amazon_bedrock"


# Each model only supports some providers, and requires different configuration
model_options: Dict[ModelName, Dict[ModelProviders, Dict]] = {
    ModelName.llama_3_1_8b: {
        ModelProviders.groq: {
            "model": "llama-3.1-8b-instant",
        },
        ModelProviders.amazon_bedrock: {
            "model_id": "meta.llama3-1-8b-instruct-v1:0",
            "region_name": "us-west-2",  # Llama 3.1 only in west-2
        },
    },
    ModelName.gpt_4o_mini: {
        ModelProviders.openai: {"model": "gpt-4o-mini"},
    },
    ModelName.gpt_4o: {
        ModelProviders.openai: {"model": "gpt-4o"},
    },
}


def langchain_model_from(model_name: str, provider: str) -> BaseChatModel:
    if model_name not in ModelName.__members__:
        raise ValueError(f"Invalid model_name: {model_name}")
    model_name = ModelName(model_name)
    if provider not in ModelProviders.__members__:
        raise ValueError(f"Invalid provider: {provider}")
    provider = ModelProviders(provider)

    model_hosts = model_options[model_name]
    if model_hosts is None:
        raise ValueError(f"Model {model_name} not found")
    model_provider_props = model_hosts[provider]
    if model_provider_props is None:
        raise ValueError(f"Provider {provider} not found for model {model_name}")

    if provider == ModelProviders.openai:
        return ChatOpenAI(**model_provider_props)
    elif provider == ModelProviders.groq:
        return ChatGroq(**model_provider_props)
    elif provider == ModelProviders.amazon_bedrock:
        return ChatBedrock(**model_provider_props)

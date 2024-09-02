import os
from enum import Enum
from typing import Dict, List

import httpx
from langchain_aws import ChatBedrock
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class ModelProviders(str, Enum):
    openai = "openai"
    groq = "groq"
    amazon_bedrock = "amazon_bedrock"
    ollama = "ollama"


class ModelFamily(str, Enum):
    gpt = "gpt"
    llama = "llama"
    phi = "phi"
    mistral = "mistral"


class ModelName(str, Enum):
    llama_3_1_8b = "llama_3_1_8b"
    llama_3_1_70b = "llama_3_1_70b"
    gpt_4o_mini = "gpt_4o_mini"
    gpt_4o = "gpt_4o"
    phi_3_5 = "phi_3_5"
    mistral_large = "mistral_large"


class KilnModel(BaseModel):
    model_family: str
    model_name: str
    provider_config: Dict[ModelProviders, Dict]
    supports_structured_output: bool = True


built_in_models: List[KilnModel] = [
    # GPT 4o Mini
    KilnModel(
        model_family=ModelFamily.gpt,
        model_name=ModelName.gpt_4o_mini,
        provider_config={
            ModelProviders.openai: {
                "model": "gpt-4o-mini",
            },
        },
    ),
    # GPT 4o
    KilnModel(
        model_family=ModelFamily.gpt,
        model_name=ModelName.gpt_4o,
        provider_config={
            ModelProviders.openai: {
                "model": "gpt-4o",
            },
        },
    ),
    # Llama 3.1-8b
    KilnModel(
        model_family=ModelFamily.llama,
        model_name=ModelName.llama_3_1_8b,
        provider_config={
            ModelProviders.groq: {
                "model": "llama-3.1-8b-instant",
            },
            # Doesn't reliably work with tool calling / structured output
            # https://www.reddit.com/r/LocalLLaMA/comments/1ece00h/llama_31_8b_instruct_functiontool_calling_seems/
            # ModelProviders.amazon_bedrock: {
            #     "model_id": "meta.llama3-1-8b-instruct-v1:0",
            #     "region_name": "us-west-2",  # Llama 3.1 only in west-2
            # },
            ModelProviders.ollama: {
                "model": "llama3.1",
            },
        },
    ),
    # Llama 3.1 70b
    KilnModel(
        model_family=ModelFamily.llama,
        model_name=ModelName.llama_3_1_70b,
        provider_config={
            ModelProviders.groq: {
                "model": "llama-3.1-70b-versatile",
            },
            ModelProviders.amazon_bedrock: {
                "model_id": "meta.llama3-1-70b-instruct-v1:0",
                "region_name": "us-west-2",  # Llama 3.1 only in west-2
            },
            # ModelProviders.ollama: {
            #    "model": "llama3.1:70b",
            # },
        },
    ),
    # Mistral Large
    KilnModel(
        model_family=ModelFamily.mistral,
        model_name=ModelName.mistral_large,
        provider_config={
            ModelProviders.amazon_bedrock: {
                "model_id": "mistral.mistral-large-2407-v1:0",
                "region_name": "us-west-2",  # only in west-2
            },
        },
    ),
    # Phi 3.5
    KilnModel(
        model_family=ModelFamily.phi,
        model_name=ModelName.phi_3_5,
        supports_structured_output=False,
        provider_config={
            ModelProviders.ollama: {
                "model": "phi3.5",
            },
        },
    ),
]


def langchain_model_from(
    model_name: str, provider_name: str | None = None
) -> BaseChatModel:
    if model_name not in ModelName.__members__:
        raise ValueError(f"Invalid model_name: {model_name}")

    # Select the model from built_in_models using the model_name
    model = next(filter(lambda m: m.model_name == model_name, built_in_models))
    if model is None:
        raise ValueError(f"Model {model_name} not found")

    # If a provider is provided, select the provider from the model's provider_config
    provider: ModelProviders | None = None
    if model.provider_config is None or len(model.provider_config) == 0:
        raise ValueError(f"Model {model_name} has no providers")
    if provider_name is None:
        # TODO: priority order
        provider_name = list(model.provider_config.keys())[0]
    if provider_name not in ModelProviders.__members__:
        raise ValueError(f"Invalid provider: {provider_name}")
    if provider_name not in model.provider_config:
        raise ValueError(f"Provider {provider_name} not found for model {model_name}")
    model_provider_props = model.provider_config[provider_name]
    provider = ModelProviders(provider_name)

    if provider == ModelProviders.openai:
        return ChatOpenAI(**model_provider_props)
    elif provider == ModelProviders.groq:
        return ChatGroq(**model_provider_props)
    elif provider == ModelProviders.amazon_bedrock:
        return ChatBedrock(**model_provider_props)
    elif provider == ModelProviders.ollama:
        return ChatOllama(**model_provider_props, base_url=ollama_base_url())


def ollama_base_url():
    env_base_url = os.getenv("OLLAMA_BASE_URL")
    if env_base_url is not None:
        return env_base_url
    return "http://localhost:11434"


async def ollama_online():
    try:
        httpx.get(ollama_base_url() + "/api/tags")
    except httpx.RequestError:
        return False
    return True

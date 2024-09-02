import os
from enum import Enum
from typing import Dict, List

import httpx
from langchain_aws import ChatBedrockConverse
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class ModelProviderName(str, Enum):
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


class KilnModelProvider(BaseModel):
    name: ModelProviderName
    # Allow overriding the model level setting
    supports_structured_output: bool = True
    provider_options: Dict = {}


class KilnModel(BaseModel):
    model_family: str
    model_name: str
    providers: List[KilnModelProvider]
    supports_structured_output: bool = True


built_in_models: List[KilnModel] = [
    # GPT 4o Mini
    KilnModel(
        model_family=ModelFamily.gpt,
        model_name=ModelName.gpt_4o_mini,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.openai,
                provider_options={"model": "gpt-4o-mini"},
            ),
        ],
    ),
    # GPT 4o
    KilnModel(
        model_family=ModelFamily.gpt,
        model_name=ModelName.gpt_4o,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.openai,
                provider_options={"model": "gpt-4o"},
            ),
        ],
    ),
    # Llama 3.1-8b
    KilnModel(
        model_family=ModelFamily.llama,
        model_name=ModelName.llama_3_1_8b,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.groq,
                provider_options={"model": "llama-3.1-8b-instant"},
            ),
            KilnModelProvider(
                name=ModelProviderName.amazon_bedrock,
                # bedrock llama doesn't support structured output, should check again latet
                supports_structured_output=False,
                provider_options={
                    "model": "meta.llama3-1-8b-instruct-v1:0",
                    "region_name": "us-west-2",  # Llama 3.1 only in west-2
                },
            ),
            KilnModelProvider(
                name=ModelProviderName.ollama,
                provider_options={"model": "llama3.1"},
            ),
        ],
    ),
    # Llama 3.1 70b
    KilnModel(
        model_family=ModelFamily.llama,
        model_name=ModelName.llama_3_1_70b,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.groq,
                provider_options={"model": "llama-3.1-70b-versatile"},
            ),
            KilnModelProvider(
                name=ModelProviderName.amazon_bedrock,
                # bedrock llama doesn't support structured output, should check again latet
                supports_structured_output=False,
                provider_options={
                    "model": "meta.llama3-1-70b-instruct-v1:0",
                    "region_name": "us-west-2",  # Llama 3.1 only in west-2
                },
            ),
            # TODO: enable once tests update to check if model is available
            # KilnModelProvider(
            #     provider=ModelProviders.ollama,
            #     provider_options={"model": "llama3.1:70b"},
            # ),
        ],
    ),
    # Mistral Large
    KilnModel(
        model_family=ModelFamily.mistral,
        model_name=ModelName.mistral_large,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.amazon_bedrock,
                provider_options={
                    "model": "mistral.mistral-large-2407-v1:0",
                    "region_name": "us-west-2",  # only in west-2
                },
            ),
            # TODO: enable once tests update to check if model is available
            # KilnModelProvider(
            #     provider=ModelProviders.ollama,
            #     provider_options={"model": "mistral-large"},
            # ),
        ],
    ),
    # Phi 3.5
    KilnModel(
        model_family=ModelFamily.phi,
        model_name=ModelName.phi_3_5,
        supports_structured_output=False,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.ollama,
                provider_options={"model": "phi3.5"},
            ),
        ],
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
    provider: KilnModelProvider | None = None
    if model.providers is None or len(model.providers) == 0:
        raise ValueError(f"Model {model_name} has no providers")
    elif provider_name is None:
        # TODO: priority order
        provider = model.providers[0]
    else:
        provider = next(
            filter(lambda p: p.name == provider_name, model.providers), None
        )
    if provider is None:
        raise ValueError(f"Provider {provider_name} not found for model {model_name}")

    if provider.name == ModelProviderName.openai:
        return ChatOpenAI(**provider.provider_options)
    elif provider.name == ModelProviderName.groq:
        return ChatGroq(**provider.provider_options)
    elif provider.name == ModelProviderName.amazon_bedrock:
        return ChatBedrockConverse(**provider.provider_options)
    elif provider.name == ModelProviderName.ollama:
        return ChatOllama(**provider.provider_options, base_url=ollama_base_url())
    else:
        raise ValueError(f"Invalid model or provider: {model_name} - {provider_name}")


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

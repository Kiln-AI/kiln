import os
from enum import Enum
from os import getenv
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
    openrouter = "openrouter"


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
    mistral_nemo = "mistral_nemo"


class KilnModelProvider(BaseModel):
    name: ModelProviderName
    # Allow overriding the model level setting
    supports_structured_output: bool = True
    provider_options: Dict = {}


class KilnModel(BaseModel):
    family: str
    name: str
    providers: List[KilnModelProvider]
    supports_structured_output: bool = True


built_in_models: List[KilnModel] = [
    # GPT 4o Mini
    KilnModel(
        family=ModelFamily.gpt,
        name=ModelName.gpt_4o_mini,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.openai,
                provider_options={"model": "gpt-4o-mini"},
            ),
            KilnModelProvider(
                name=ModelProviderName.openrouter,
                provider_options={"model": "openai/gpt-4o-mini"},
            ),
        ],
    ),
    # GPT 4o
    KilnModel(
        family=ModelFamily.gpt,
        name=ModelName.gpt_4o,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.openai,
                provider_options={"model": "gpt-4o"},
            ),
            KilnModelProvider(
                name=ModelProviderName.openrouter,
                provider_options={"model": "openai/gpt-4o-2024-08-06"},
            ),
        ],
    ),
    # Llama 3.1-8b
    KilnModel(
        family=ModelFamily.llama,
        name=ModelName.llama_3_1_8b,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.groq,
                provider_options={"model": "llama-3.1-8b-instant"},
            ),
            KilnModelProvider(
                name=ModelProviderName.amazon_bedrock,
                provider_options={
                    "model": "meta.llama3-1-8b-instruct-v1:0",
                    "region_name": "us-west-2",  # Llama 3.1 only in west-2
                },
            ),
            KilnModelProvider(
                name=ModelProviderName.ollama,
                provider_options={"model": "llama3.1"},
            ),
            KilnModelProvider(
                name=ModelProviderName.openrouter,
                provider_options={"model": "meta-llama/llama-3.1-8b-instruct"},
            ),
        ],
    ),
    # Llama 3.1 70b
    KilnModel(
        family=ModelFamily.llama,
        name=ModelName.llama_3_1_70b,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.groq,
                provider_options={"model": "llama-3.1-70b-versatile"},
            ),
            KilnModelProvider(
                name=ModelProviderName.amazon_bedrock,
                # TODO: this should work but a bug in the bedrock response schema
                supports_structured_output=False,
                provider_options={
                    "model": "meta.llama3-1-70b-instruct-v1:0",
                    "region_name": "us-west-2",  # Llama 3.1 only in west-2
                },
            ),
            KilnModelProvider(
                name=ModelProviderName.openrouter,
                provider_options={"model": "meta-llama/llama-3.1-70b-instruct"},
            ),
            # TODO: enable once tests update to check if model is available
            # KilnModelProvider(
            #     provider=ModelProviders.ollama,
            #     provider_options={"model": "llama3.1:70b"},
            # ),
        ],
    ),
    # Mistral Nemo
    KilnModel(
        family=ModelFamily.mistral,
        name=ModelName.mistral_nemo,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.openrouter,
                provider_options={"model": "mistralai/mistral-nemo"},
            ),
        ],
    ),
    # Mistral Large
    KilnModel(
        family=ModelFamily.mistral,
        name=ModelName.mistral_large,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.amazon_bedrock,
                provider_options={
                    "model": "mistral.mistral-large-2407-v1:0",
                    "region_name": "us-west-2",  # only in west-2
                },
            ),
            KilnModelProvider(
                name=ModelProviderName.openrouter,
                provider_options={"model": "mistralai/mistral-large"},
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
        family=ModelFamily.phi,
        name=ModelName.phi_3_5,
        supports_structured_output=False,
        providers=[
            KilnModelProvider(
                name=ModelProviderName.ollama,
                provider_options={"model": "phi3.5"},
            ),
            KilnModelProvider(
                name=ModelProviderName.openrouter,
                provider_options={"model": "microsoft/phi-3.5-mini-128k-instruct"},
            ),
        ],
    ),
]


def langchain_model_from(name: str, provider_name: str | None = None) -> BaseChatModel:
    if name not in ModelName.__members__:
        raise ValueError(f"Invalid name: {name}")

    # Select the model from built_in_models using the name
    model = next(filter(lambda m: m.name == name, built_in_models))
    if model is None:
        raise ValueError(f"Model {name} not found")

    # If a provider is provided, select the provider from the model's provider_config
    provider: KilnModelProvider | None = None
    if model.providers is None or len(model.providers) == 0:
        raise ValueError(f"Model {name} has no providers")
    elif provider_name is None:
        # TODO: priority order
        provider = model.providers[0]
    else:
        provider = next(
            filter(lambda p: p.name == provider_name, model.providers), None
        )
    if provider is None:
        raise ValueError(f"Provider {provider_name} not found for model {name}")

    if provider.name == ModelProviderName.openai:
        return ChatOpenAI(**provider.provider_options)
    elif provider.name == ModelProviderName.groq:
        return ChatGroq(**provider.provider_options)
    elif provider.name == ModelProviderName.amazon_bedrock:
        return ChatBedrockConverse(**provider.provider_options)
    elif provider.name == ModelProviderName.ollama:
        return ChatOllama(**provider.provider_options, base_url=ollama_base_url())
    elif provider.name == ModelProviderName.openrouter:
        api_key = getenv("OPENROUTER_API_KEY")
        if api_key is None:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable must be set to use OpenRouter. "
                "Get your API key from https://openrouter.ai/settings/keys"
            )
        base_url = getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"
        return ChatOpenAI(
            **provider.provider_options,
            openai_api_key=api_key,  # type: ignore[arg-type]
            openai_api_base=base_url,  # type: ignore[arg-type]
            # TODO: should pass these
            # model_kwargs={
            #     "headers": {
            #         "HTTP-Referer": "https://kiln-ai.com",
            #         "X-Title": "KilnAI",
            #     }
            # },
        )
    else:
        raise ValueError(f"Invalid model or provider: {name} - {provider_name}")


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

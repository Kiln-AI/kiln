import os

import requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from langchain_aws import ChatBedrockConverse

from libs.core.kiln_ai.adapters.ml_model_list import ModelProviderName, built_in_models
from libs.core.kiln_ai.utils.config import Config


def connect_provider_management(app: FastAPI):
    @app.post("/provider/ollama/connect")
    def connect_ollama():
        # Tags is a list of Ollama models. Proves Ollama is running, and models are available.
        try:
            tags = requests.get("http://localhost:11434/api/tags", timeout=5).json()
        except requests.exceptions.ConnectionError:
            return JSONResponse(
                status_code=417,
                content={"message": "Failed to connect. Ensure Ollama app is running."},
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Failed to connect to Ollama: {e}"},
            )

        # Build a list of models we support for Ollama from the built-in model list
        supported_ollama_models = [
            provider.provider_options["model"]
            for model in built_in_models
            for provider in model.providers
            if provider.name == ModelProviderName.ollama
        ]

        if "models" in tags:
            models = tags["models"]
            if isinstance(models, list):
                model_names = [model["model"] for model in models]
                available_supported_models = [
                    model
                    for model in model_names
                    if model in supported_ollama_models
                    or model in [f"{m}:latest" for m in supported_ollama_models]
                ]
                if available_supported_models:
                    Config.shared().ollama_base_url = "http://localhost:11434"
                    return {
                        "message": "Ollama connected",
                        "models": available_supported_models,
                    }

        return JSONResponse(
            status_code=417,
            content={
                "message": "Ollama is running, but no supported models are installed. Install one or more supported model, like 'ollama pull phi3.5'."
            },
        )

    @app.post("/provider/connect_api_key")
    async def connect_api_key(payload: dict):
        provider = payload.get("provider")
        key_data = payload.get("key_data")
        if not isinstance(key_data, dict) or not isinstance(provider, str):
            return JSONResponse(
                status_code=400,
                content={"message": "Invalid key_data or provider"},
            )

        api_key_providers = ["openai", "groq", "bedrock", "openrouter"]
        if provider not in api_key_providers:
            return JSONResponse(
                status_code=400,
                content={"message": f"Provider {provider} not supported"},
            )

        if provider == "openai" and isinstance(key_data["API Key"], str):
            return await connect_openai(key_data["API Key"])
        elif provider == "groq" and isinstance(key_data["API Key"], str):
            return await connect_groq(key_data["API Key"])
        elif provider == "openrouter" and isinstance(key_data["API Key"], str):
            return await connect_openrouter(key_data["API Key"])
        elif (
            provider == "bedrock"
            and isinstance(key_data["Access Key"], str)
            and isinstance(key_data["Secret Key"], str)
        ):
            return await connect_bedrock(key_data["Access Key"], key_data["Secret Key"])
        else:
            return JSONResponse(
                status_code=400,
                content={"message": f"Provider {provider} missing API key"},
            )


async def connect_openrouter(key: str):
    try:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        # invalid body, but we just want to see if the key is valid
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={},
        )

        # 401 def means invalid API key
        if response.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={
                    "message": "Failed to connect to OpenRouter. Invalid API key."
                },
            )
        else:
            # No 401 means key is valid (even it it's an error, which we expect with empty body)
            Config.shared().open_router_api_key = key

            return JSONResponse(
                status_code=200,
                content={"message": "Connected to OpenRouter"},
            )
            # Any non-200 status code is an error
    except Exception as e:
        # unexpected error
        return JSONResponse(
            status_code=400,
            content={"message": f"Failed to connect to OpenRouter. Error: {str(e)}"},
        )


async def connect_openai(key: str):
    try:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        response = requests.get("https://api.openai.com/v1/models", headers=headers)

        # 401 def means invalid API key, so special case it
        if response.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={"message": "Failed to connect to OpenAI. Invalid API key."},
            )

        # Any non-200 status code is an error
        response.raise_for_status()
        # If the request is successful, the function will continue
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"message": f"Failed to connect to OpenAI. Error: {str(e)}"},
        )

    # It worked! Save the key and return success
    Config.shared().open_ai_api_key = key

    return JSONResponse(
        status_code=200,
        content={"message": "Connected to OpenAI"},
    )


async def connect_groq(key: str):
    try:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        response = requests.get(
            "https://api.groq.com/openai/v1/models", headers=headers
        )

        if "invalid_api_key" in response.text:
            return JSONResponse(
                status_code=401,
                content={"message": "Failed to connect to Groq. Invalid API key."},
            )

        # Any non-200 status code is an error
        response.raise_for_status()
        # If the request is successful, the function will continue
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"message": f"Failed to connect to Groq. Error: {str(e)}"},
        )

    # It worked! Save the key and return success
    Config.shared().groq_api_key = key

    return JSONResponse(
        status_code=200,
        content={"message": "Connected to Groq"},
    )


async def connect_bedrock(access_key: str, secret_key: str):
    try:
        # Langchain API is not good... need to use env vars. Pop these in finally block
        os.environ["AWS_ACCESS_KEY_ID"] = access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key

        # Fake model, but will get a credential error before AWS realizes it's wrong
        # Ensures we don't spend money on a test call
        llm = ChatBedrockConverse(
            model="fake_model",
            region_name="us-west-2",
        )
        llm.invoke("Hello, how are you?")
    except Exception as e:
        # Check for specific error messages indicating invalid credentials
        print(e)
        if "UnrecognizedClientException" in str(
            e
        ) or "InvalidSignatureException" in str(e):
            return JSONResponse(
                status_code=401,
                content={
                    "message": "Failed to connect to Bedrock. Invalid credentials."
                },
            )
        else:
            # We still expect an error (fake model), but not for invalid credentials which means success!
            Config.shared().bedrock_access_key = access_key
            Config.shared().bedrock_secret_key = secret_key
            return JSONResponse(
                status_code=200,
                content={"message": "Connected to Bedrock"},
            )

    finally:
        os.environ.pop("AWS_ACCESS_KEY_ID")
        os.environ.pop("AWS_SECRET_ACCESS_KEY")

    # we shouldn't get here, but if we do, something went wrong
    return JSONResponse(
        status_code=400,
        content={"message": "Unknown Bedrock Error"},
    )

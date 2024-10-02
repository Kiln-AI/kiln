import requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse

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

        print(f"Connecting API key for {provider}: {key_data}")
        if provider == "openai" and isinstance(key_data["API Key"], str):
            return await connect_openai(key_data["API Key"])

        return JSONResponse(
            status_code=400,
            content={"message": f"Provider {provider} not supported"},
        )

    async def connect_openai(key: str):
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            response = requests.get("https://api.openai.com/v1/models", headers=headers)
            response.raise_for_status()
            # If the request is successful, the function will continue
        except requests.RequestException as e:
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"Failed to connect to OpenAI. Likely invalid API key. Error: {str(e)}"
                },
            )

        # Save the key
        Config.shared().open_ai_api_key = key

        return JSONResponse(
            status_code=200,
            content={"message": "Connected to OpenAI"},
        )

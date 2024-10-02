import requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from libs.core.kiln_ai.adapters.ml_model_list import ModelProviderName, built_in_models


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

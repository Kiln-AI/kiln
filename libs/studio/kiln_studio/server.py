import os
from pathlib import Path
from typing import Union

import requests
import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .settings import connect_settings
from .webhost import connect_webhost


def make_app():
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/ping")
    def ping():
        return "pong"

    @app.post("/provider/ollama/connect")
    def connect_ollama():
        # Tags is a list of Ollama models. Proves Ollama is running, and models are available.
        try:
            tags = requests.get("http://localhost:11434/api/tags", timeout=5).json()
        except requests.exceptions.ConnectionError:
            return JSONResponse(
                status_code=417,
                content={
                    "message": "Failed to connect to Ollama. Ensure Ollama app is running."
                },
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"message": f"Failed to connect to Ollama: {e}"},
            )

        if "models" in tags:
            models = tags["models"]
            if isinstance(models, list):
                model_names = [model["model"] for model in models]
                # TODO P2: check there's at least 1 model we support
                if len(model_names) > 0:
                    return {"message": "Ollama connected", "models": model_names}

        return JSONResponse(
            status_code=417,
            content={"message": "Ollama not connected, or no Ollama models installed."},
        )

    connect_settings(app)
    connect_webhost(app)

    return app


if __name__ == "__main__":
    app = make_app()
    uvicorn.run(app, host="127.0.0.1", port=8757)

import os
import sys
from pathlib import Path
from typing import Union

import requests
import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


def studio_path():
    try:
        # pyinstaller path
        base_path = sys._MEIPASS  # type: ignore
        return os.path.join(base_path, "./web_ui/build")
    except Exception:
        base_path = os.path.join(os.path.dirname(__file__), "..")
        return os.path.join(base_path, "../../app/web_ui/build")


# File server that maps /foo/bar to /foo/bar.html (Starlette StaticFiles only does index.html)
class HTMLStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
            if response.status_code != 404:
                return response
        except Exception as e:
            # catching HTTPException explicitly not working for some reason
            if getattr(e, "status_code", None) != 404:
                # Don't raise on 404, fall through to return the .html version
                raise e
        #  Try the .html version of the file if the .html version exists, for 404s
        return await super().get_response(f"{path}.html", scope)


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

    def settings_path(create=True):
        settings_dir = os.path.join(Path.home(), ".kiln_ai")
        if create and not os.path.exists(settings_dir):
            os.makedirs(settings_dir)
        return os.path.join(settings_dir, "settings.yaml")

    def load_settings():
        if not os.path.isfile(settings_path(create=False)):
            return {}
        with open(settings_path(), "r") as f:
            settings = yaml.safe_load(f.read())
        return settings

    @app.post("/provider/ollama/connect")
    def connect_ollama():
        # Tags is a list of Ollama models. Proves Ollama is running, and models are available.
        try:
            tags = requests.get("http://localhost:11434/api/tags").json()
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

    @app.post("/setting")
    def update_settings(new_settings: dict[str, int | float | str | bool]):
        settings = load_settings()
        settings.update(new_settings)
        with open(settings_path(), "w") as f:
            f.write(yaml.dump(settings))
        return {"message": "Settings updated"}

    @app.get("/settings")
    def read_settings():
        settings = load_settings()
        return settings

    @app.get("/items/{item_id}")
    def read_item(item_id: int, q: Union[str, None] = None):
        return {"item_id": item_id, "q": q}

    # Web UI

    # Ensure studio_path exists (test servers don't necessarily create it)
    os.makedirs(studio_path(), exist_ok=True)
    # Serves the web UI at root
    app.mount("/", HTMLStaticFiles(directory=studio_path(), html=True), name="studio")

    @app.exception_handler(404)
    def not_found_exception_handler(request, exc):
        return FileResponse(os.path.join(studio_path(), "404.html"), status_code=404)

    return app


if __name__ == "__main__":
    app = make_app()
    uvicorn.run(app, host="127.0.0.1", port=8757)

from typing import Union

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
import yaml
from pathlib import Path
import sys


# TODO would rather this get passed. This class shouldn't know about desktop
def studio_path():
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.join(os.path.dirname(__file__), "..")

    return os.path.join(base_path, "studio/web_ui/build")


app = FastAPI()


def settings_path(create=True):
    funedir = os.path.join(Path.home(), ".fune")
    if create and not os.path.exists(funedir):
        os.makedirs(funedir)
    return os.path.join(funedir, "settings.yaml")


def load_settings():
    if not os.path.isfile(settings_path(create=False)):
        return {}
    with open(settings_path(), "r") as f:
        settings = yaml.safe_load(f.read())
    return settings


@app.post("/setting")
def update_settings(new_settings: dict):
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
app.mount("/", StaticFiles(directory=studio_path(), html=True), name="studio")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8759)

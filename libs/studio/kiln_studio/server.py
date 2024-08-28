import os
import sys
from pathlib import Path
from typing import Union

import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


# TODO would rather this get passed. This class shouldn't know about desktop
def studio_path():
    try:
        base_path = sys._MEIPASS  # type: ignore
        return os.path.join(base_path, "./web_ui/build")
    except Exception:
        base_path = os.path.join(os.path.dirname(__file__), "..")
        return os.path.join(base_path, "../../app/web_ui/build")


app = FastAPI()


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
app.mount("/", StaticFiles(directory=studio_path(), html=True), name="studio")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8757)

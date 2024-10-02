import os
from pathlib import Path

import yaml
from fastapi import FastAPI


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


def connect_settings(app: FastAPI):
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
    def read_item(item_id: int):
        return {"item_id": item_id}

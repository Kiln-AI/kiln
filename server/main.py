from typing import Union

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
import yaml
from pathlib import Path

dirname = os.path.dirname(__file__)
studio_path = os.path.join(dirname, 'studio')

app = FastAPI()

def settings_path(create=True):
    funedir = os.path.join(Path.home(), '.fune')
    if create and not os.path.exists(funedir):
        os.makedirs(funedir)
    return os.path.join(funedir, 'settings.yaml')

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

@app.get("/")
def read_root():
    return "root"

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

app.mount("/fune", StaticFiles(directory=studio_path, html=True), name="studio")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8759)
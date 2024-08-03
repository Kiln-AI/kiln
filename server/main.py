from typing import Union

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

dirname = os.path.dirname(__file__)
studio_path = os.path.join(dirname, 'studio')

app = FastAPI()

@app.get("/")
def read_root():
    return "root"


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

app.mount("/fune", StaticFiles(directory=studio_path, html=True), name="studio")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8759)
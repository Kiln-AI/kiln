from fastapi import FastAPI

from libs.core.kiln_ai.utils.config import Config


def connect_settings(app: FastAPI):
    @app.post("/settings")
    def update_settings(new_settings: dict[str, int | float | str | bool | None]):
        Config.shared().update_settings(new_settings)
        return Config.shared().settings()

    @app.get("/settings")
    def read_settings():
        settings = Config.shared().settings()
        return settings

    @app.get("/settings/{item_id}")
    def read_item(item_id: str):
        settings = Config.shared().settings()
        return {item_id: settings.get(item_id, None)}

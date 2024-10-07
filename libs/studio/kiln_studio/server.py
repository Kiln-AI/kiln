import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .custom_errors import connect_custom_errors
from .project_management import connect_project_management
from .provider_management import connect_provider_management
from .settings import connect_settings
from .task_management import connect_task_management
from .webhost import connect_webhost


def make_app():
    app = FastAPI()

    # Allow requests from localhost and 127.0.0.1
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

    connect_project_management(app)
    connect_provider_management(app)
    connect_task_management(app)
    connect_settings(app)
    connect_custom_errors(app)

    # Important: webhost must be last, it handles all other URLs
    connect_webhost(app)

    return app


app = make_app()
if __name__ == "__main__":
    auto_reload = os.environ.get("AUTO_RELOAD", "").lower() in ("true", "1", "yes")
    uvicorn.run(
        "libs.studio.kiln_studio.server:app",
        host="127.0.0.1",
        port=8757,
        reload=auto_reload,
    )

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .custom_errors import connect_custom_errors
from .project_api import connect_project_api
from .provider_api import connect_provider_api
from .run_api import connect_run_api
from .settings import connect_settings
from .task_api import connect_task_api
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

    connect_project_api(app)
    connect_provider_api(app)
    connect_task_api(app)
    connect_run_api(app)
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

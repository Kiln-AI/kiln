import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from libs.core.kiln_ai.datamodel import Project, Task


def connect_task_management(app: FastAPI):
    @app.post("/api/task")
    async def create_task(task: Task, project_path: str):
        if not os.path.exists(project_path):
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Parent project not found. Can't create task.",
                },
            )

        try:
            parent_project = Project.load_from_file(Path(project_path))
            task.parent = parent_project
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "message": f"Failed to load parent project: {e}",
                },
            )

        task.save_to_file()
        returnTask = task.model_dump()
        returnTask["path"] = task.path
        return returnTask

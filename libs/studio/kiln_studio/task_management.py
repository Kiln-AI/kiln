import os
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException

from libs.core.kiln_ai.datamodel import Project, Task


def connect_task_management(app: FastAPI):
    @app.post("/api/task")
    async def create_task(task_data: Dict[str, Any], project_path: str | None = None):
        if project_path is None or not os.path.exists(project_path):
            raise HTTPException(
                status_code=400,
                detail="Parent project not found. Can't create task.",
            )

        try:
            parent_project = Project.load_from_file(Path(project_path))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load parent project: {e}",
            )

        task = Task.validate_and_save_with_subrelations(
            task_data, parent=parent_project
        )
        if task is None:
            raise HTTPException(
                status_code=400,
                detail="Failed to create task.",
            )

        returnTask = task.model_dump()
        returnTask["path"] = task.path
        return returnTask

    @app.get("/api/tasks")
    async def get_tasks(project_path: str | None = None):
        if project_path is None or not os.path.exists(project_path):
            raise HTTPException(
                status_code=400,
                detail="Parent project not found. Can't get tasks.",
            )

        try:
            parent_project = Project.load_from_file(Path(project_path))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load parent project: {e}",
            )

        return parent_project.tasks()

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from kiln_ai.datamodel import Task

from libs.studio.kiln_studio.project_api import project_from_id


def connect_task_api(app: FastAPI):
    @app.post("/api/projects/{project_id}/task")
    async def create_task(project_id: str, task_data: Dict[str, Any]):
        parent_project = project_from_id(project_id)

        task = Task.validate_and_save_with_subrelations(
            task_data, parent=parent_project
        )
        if task is None:
            raise HTTPException(
                status_code=400,
                detail="Failed to create task.",
            )

        return task

    @app.get("/api/projects/{project_id}/tasks")
    async def get_tasks(project_id: str):
        parent_project = project_from_id(project_id)
        return parent_project.tasks()

    @app.get("/api/projects/{project_id}/task/{task_id}")
    async def get_task(project_id: str, task_id: str):
        parent_project = project_from_id(project_id)

        for task in parent_project.tasks():
            if task.id == task_id:
                return task

        raise HTTPException(
            status_code=404,
            detail=f"Task not found. ID: {task_id}",
        )

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from kiln_ai.adapters.langchain_adapters import LangChainPromptAdapter
from kiln_ai.datamodel import Task
from pydantic import BaseModel

from libs.studio.kiln_studio.project_management import project_from_id


class RunTaskRequest(BaseModel):
    model_name: str
    provider: str
    plaintext_input: str | None = None
    structured_input: Dict[str, Any] | None = None


class RunTaskResponse(BaseModel):
    plaintext_output: str | None = None
    structured_output: Dict[str, Any] | List[Any] | None = None


def connect_task_management(app: FastAPI):
    @app.post("/api/projects/{project_id}/task")
    async def create_task(project_id: str, task_data: Dict[str, Any]):
        print(f"Creating task for project {project_id} with data {task_data}")
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

    @app.post("/api/projects/{project_id}/task/{task_id}/run")
    async def run_task(project_id: str, task_id: str, request: RunTaskRequest):
        parent_project = project_from_id(project_id)
        task = next(
            (task for task in parent_project.tasks() if task.id == task_id), None
        )
        if task is None:
            raise HTTPException(
                status_code=404,
                detail=f"Task not found. ID: {task_id}",
            )

        adapter = LangChainPromptAdapter(
            task, model_name=request.model_name, provider=request.provider
        )

        input = request.plaintext_input
        if task.input_schema() is not None:
            input = request.structured_input

        if input is None:
            raise HTTPException(
                status_code=400,
                detail="No input provided. Ensure your provided the proper format (plaintext or structured).",
            )

        output = await adapter.invoke(input)
        response = RunTaskResponse()
        if isinstance(output, str):
            response.plaintext_output = output
        else:
            response.structured_output = output

        return response

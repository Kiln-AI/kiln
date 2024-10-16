import json
from asyncio import Lock
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from kiln_ai.adapters.langchain_adapters import LangChainPromptAdapter
from kiln_ai.datamodel import Task, TaskRun
from pydantic import BaseModel

from libs.studio.kiln_studio.project_management import project_from_id

# Add this at the module level
update_run_lock = Lock()


class RunTaskRequest(BaseModel):
    model_name: str
    provider: str
    plaintext_input: str | None = None
    structured_input: Dict[str, Any] | None = None


class RunTaskResponse(BaseModel):
    run: TaskRun | None = None
    raw_output: str | None = None


def deep_update(
    source: Dict[str, Any] | None, update: Dict[str, Any | None]
) -> Dict[str, Any]:
    if source is None:
        return {k: v for k, v in update.items() if v is not None}
    for key, value in update.items():
        if value is None:
            source.pop(key, None)
        elif isinstance(value, dict):
            if key not in source or not isinstance(source[key], dict):
                source[key] = {}
            source[key] = deep_update(source[key], value)
        else:
            source[key] = value
    return {k: v for k, v in source.items() if v is not None}


def connect_task_management(app: FastAPI):
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

    @app.post("/api/projects/{project_id}/task/{task_id}/run")
    async def run_task(
        project_id: str, task_id: str, request: RunTaskRequest
    ) -> RunTaskResponse:
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

        adapter_run = await adapter.invoke_returning_run(input)
        response_output = None
        if isinstance(adapter_run.output, str):
            response_output = adapter_run.output
        else:
            response_output = json.dumps(adapter_run.output)

        return RunTaskResponse(raw_output=response_output, run=adapter_run.run)

    @app.patch("/api/projects/{project_id}/task/{task_id}/run/{run_id}")
    async def update_run_route(
        project_id: str, task_id: str, run_id: str, run_data: Dict[str, Any]
    ) -> TaskRun:
        return await update_run(project_id, task_id, run_id, run_data)


async def update_run(
    project_id: str, task_id: str, run_id: str, run_data: Dict[str, Any]
) -> TaskRun:
    # Lock to prevent overwriting concurrent updates
    async with update_run_lock:
        parent_project = project_from_id(project_id)
        task = next(
            (task for task in parent_project.tasks() if task.id == task_id), None
        )
        if task is None:
            raise HTTPException(
                status_code=404,
                detail=f"Task not found. ID: {task_id}",
            )

        run = next((run for run in task.runs() if run.id == run_id), None)
        if run is None:
            raise HTTPException(
                status_code=404,
                detail=f"Run not found. ID: {run_id}",
            )

        # Update and save
        old_run_dumped = run.model_dump()
        merged = deep_update(old_run_dumped, run_data)
        updated_run = TaskRun.model_validate(merged)
        updated_run.path = run.path
        updated_run.save_to_file()
        return updated_run

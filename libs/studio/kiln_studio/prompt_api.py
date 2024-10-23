from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from kiln_ai.datamodel import Task
from pydantic import BaseModel

from libs.core.kiln_ai.adapters.prompt_builders import prompt_builder_from_ui_name
from libs.studio.kiln_studio.project_api import project_from_id
from libs.studio.kiln_studio.task_api import task_from_id


class PromptApiResponse(BaseModel):
    prompt: str
    prompt_builder_name: str
    ui_generator_name: str


def connect_prompt_api(app: FastAPI):
    @app.get("/api/projects/{project_id}/task/{task_id}/gen_prompt/{prompt_generator}")
    async def gen_prompt(
        project_id: str, task_id: str, prompt_generator: str
    ) -> PromptApiResponse:
        task = task_from_id(project_id, task_id)

        try:
            prompt_builder_class = prompt_builder_from_ui_name(prompt_generator)
            prompt_builder = prompt_builder_class(task)
            prompt = prompt_builder.build_prompt()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        return PromptApiResponse(
            prompt=prompt,
            prompt_builder_name=prompt_builder_class.prompt_builder_name(),
            ui_generator_name=prompt_generator,
        )

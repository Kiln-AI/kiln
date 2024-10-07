import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from libs.core.kiln_ai.datamodel import Project
from libs.core.kiln_ai.utils.config import Config


def default_project_path():
    return os.path.join(Path.home(), "Kiln Projects")


def connect_project_management(app: FastAPI):
    @app.post("/api/project")
    async def create_project(project: Project):
        project_path = os.path.join(default_project_path(), project.name)
        if os.path.exists(project_path):
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Project with this name already exists. Please choose a different name."
                },
            )

        os.makedirs(project_path)
        project_file = os.path.join(project_path, "project.json")
        project.path = Path(project_file)
        project.save_to_file()

        # add to projects list, and set as current project
        projects = Config.shared().projects
        if not isinstance(projects, list):
            projects = []
        if project_file not in projects:
            projects.append(project_file)
        Config.shared().update_settings(
            {"projects": projects, "current_project": project_file}
        )

        # Add path, which is usually excluded
        returnProject = project.model_dump()
        returnProject["path"] = project.path
        return returnProject

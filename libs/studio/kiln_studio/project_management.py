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
    async def create_project(project: dict):
        project_name = project.get("project_name")
        if not project_name or not isinstance(project_name, str):
            return JSONResponse(
                status_code=400, content={"message": "Project name is required"}
            )
        project_description = project.get("project_description")
        if not isinstance(project_description, str):
            return JSONResponse(
                status_code=400,
                content={"message": "Project description must be a string"},
            )
        # Check if project name is alphanumeric and under 65 characters
        if (
            not all(c.isalnum() or c.isspace() for c in project_name)
            or len(project_name) > 64
        ):
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Project name must contain only alphanumeric characters and spaces, and be at most 64 characters"
                },
            )
        project_path = os.path.join(default_project_path(), project_name)
        if os.path.exists(project_path):
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Project with this name already exists. Please choose a different name."
                },
            )

        os.makedirs(project_path)
        project_file = os.path.join(project_path, "project.json")
        kiln_project = Project(
            name=project_name,
            description=project_description,
            path=Path(project_file),
        )
        kiln_project.save_to_file()

        # add to projects list, and set as current project
        projects = Config.shared().projects
        if not isinstance(projects, list):
            projects = []
        if project_file not in projects:
            projects.append(project_file)
        Config.shared().update_settings(
            {"projects": projects, "current_project": project_file}
        )

        return JSONResponse(
            status_code=200,
            content={"message": "Project created successfully"},
        )

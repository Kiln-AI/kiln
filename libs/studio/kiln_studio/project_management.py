import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from libs.core.kiln_ai.datamodel import Project
from libs.core.kiln_ai.utils.config import Config


def default_project_path():
    return os.path.join(Path.home(), "Kiln Projects")


def connect_project_management(app: FastAPI):
    @app.post("/api/project")
    async def create_project(project: Project):
        project_path = os.path.join(default_project_path(), project.name)
        if os.path.exists(project_path):
            raise HTTPException(
                status_code=400,
                detail="Project with this name already exists. Please choose a different name.",
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

    @app.get("/api/projects")
    async def get_projects():
        project_paths = Config.shared().projects
        projects = []
        for project_path in project_paths:
            try:
                project = Project.load_from_file(project_path)
                json_project = project.model_dump()
                path = str(project.path)
                if path is None:
                    raise ValueError("Project path is None")
                json_project["path"] = path
                projects.append(json_project)
            except Exception as e:
                print(f"Error loading project, skipping: {project_path}: {e}")

        current_project_path = None
        if Config.shared().current_project is not None:
            current_project_path = str(Config.shared().current_project)

        # Check if the current project path is in the list of projects
        if not current_project_path or current_project_path not in [
            project["path"] for project in projects
        ]:
            current_project_path = projects[0]["path"] if len(projects) > 0 else None

        return {
            "projects": projects,
            "current_project_path": current_project_path,
        }

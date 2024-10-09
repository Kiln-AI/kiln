import { writable, get } from "svelte/store"
import { post_error_handler, createKilnError } from "./utils/error_handlers"

type ProjectInfo = {
  name: string
  description: string
  path: string
  created_at: Date
  created_by: string
}

type AllProjects = {
  projects: ProjectInfo[]
  current_project_path: string | null
  error: string | null
}

export const projects = writable<AllProjects | null>(null)

export function current_project(): ProjectInfo | null {
  const all_projects = get(projects)

  if (!all_projects) {
    return null
  }
  const current_project_path = all_projects.current_project_path
  if (!current_project_path) {
    return null
  }
  const project = all_projects.projects.find(
    (project) => project.path === current_project_path,
  )
  if (!project) {
    return null
  }
  return project
}

export async function load_projects() {
  try {
    const response = await fetch("http://localhost:8757/api/projects")
    const data = await response.json()
    post_error_handler(response, data)

    const all_projects: AllProjects = {
      projects: data.projects,
      current_project_path: data.current_project_path,
      error: null,
    }
    projects.set(all_projects)
  } catch (error: unknown) {
    const all_projects: AllProjects = {
      projects: [],
      current_project_path: null,
      error: "Issue loading projects. " + createKilnError(error).getMessage(),
    }
    projects.set(all_projects)
  }
}

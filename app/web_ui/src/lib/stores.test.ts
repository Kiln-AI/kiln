import { get } from "svelte/store"
import { projects, current_project, ui_state, default_ui_state } from "./stores"
import { describe, it, expect, beforeEach } from "vitest"

const testProject = {
  name: "Test Project",
  path: "/test/path",
  description: "Test Description",
  created_at: new Date(),
  created_by: "Test User",
}

describe("stores", () => {
  beforeEach(() => {
    // Reset the projects store before each test
    projects.set(null)
    current_project.set(null)
    ui_state.set(default_ui_state)
  })

  describe("projects store", () => {
    it("should initialize with null", () => {
      expect(get(projects)).toBeNull()
    })

    it("should update when set", () => {
      const testProjects = {
        projects: [testProject],
        current_project_path: "/test/path",
        error: null,
      }
      projects.set(testProjects)
      expect(get(projects)).toEqual(testProjects)
    })
  })

  describe("current_project", () => {
    it("should return null when projects store is null", () => {
      expect(get(current_project)).toBeNull()
    })

    it("should return null when current_project_path is null", () => {
      projects.set({
        projects: [testProject],
        error: null,
      })
      ui_state.set({
        current_project_path: null,
      })
      expect(get(current_project)).toBeNull()
    })

    it("should return null when no project matches current_project_path", () => {
      projects.set({
        projects: [testProject],
        error: null,
      })
      ui_state.set({
        current_project_path: "/non-existent/path",
      })
      expect(get(current_project)).toBeNull()
    })

    it("should return the correct project when it exists", () => {
      projects.set({
        projects: [testProject],
        error: null,
      })
      ui_state.set({
        current_project_path: "/test/path",
      })
      expect(get(current_project)).toEqual(testProject)
    })
  })
})

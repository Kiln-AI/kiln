import type { components } from "./api_schema"

// Project-Input is a variant with path
export type Project = components["schemas"]["Project-Input"]
export type Task = components["schemas"]["Task"]
export type TaskRun = components["schemas"]["TaskRun-Input"]
export type TaskRequirement = components["schemas"]["TaskRequirement"]
export type AvailableModels = components["schemas"]["AvailableModels"]
export type ProviderModels = components["schemas"]["ProviderModels"]

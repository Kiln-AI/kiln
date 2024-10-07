import { writable } from "svelte/store"

export const current_project = writable<string | null>(null)

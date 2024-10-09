<script lang="ts">
  import { current_project, projects } from "$lib/stores"
  import type { ProjectInfo, Task } from "$lib/stores"
  import { api_error_handler } from "$lib/utils/error_handlers"
  import { ui_state } from "$lib/stores"
  import { goto } from "$app/navigation"

  $: project_list = $projects?.projects || []
  let manually_selected_project: ProjectInfo | null = null
  let tasks_loading = false
  let tasks_loading_error: string | null = null
  let selected_project_tasks: Task[] = []

  function select_project(project: ProjectInfo) {
    manually_selected_project = project
    load_tasks(project)
  }

  $: selected_project = manually_selected_project || $current_project

  $: load_tasks(selected_project)

  async function load_tasks(project: ProjectInfo | null) {
    if (project == null) {
      tasks_loading = false
      tasks_loading_error = "No project selected"
      return
    }
    try {
      tasks_loading = true
      tasks_loading_error = null
      let pathUrl = encodeURIComponent(project?.path || "")
      const response = await fetch(
        `http://localhost:8757/api/tasks?project_path=${pathUrl}`,
      )
      const data = await response.json()
      api_error_handler(response, data)
      selected_project_tasks = data
    } catch (error) {
      tasks_loading_error = "Tasks failed to load: " + error
      selected_project_tasks = []
      console.error(error)
    } finally {
      tasks_loading = false
    }
  }

  function select_task(task: Task) {
    if (selected_project == null) {
      return
    }
    ui_state.update((state) => {
      return {
        ...state,
        current_task_id: task.id,
        current_project_path: selected_project.path,
      }
    })

    goto(`/`)
  }
</script>

<h1 class="text-2xl font-bold mb-6">Switch Project or Task</h1>

<div>
  <ul class="menu menu-md bg-base-200 rounded-box w-[500px]">
    {#each project_list as project}
      {#if project.path == selected_project?.path}
        <li>
          <h1>
            {project.name}
          </h1>
          <ul>
            {#if tasks_loading}
              <li
                class="flex justify-center place-items-center place-content-center h-32"
              >
                <span class="loading loading-spinner loading-md"></span>
              </li>
            {:else if tasks_loading_error}
              <li
                class="flex justify-center place-items-center place-content-center h-32"
              >
                <span class="flex flex-col">
                  <span class="font-bold">Error</span>
                  <span class="">{tasks_loading_error}</span>
                </span>
              </li>
            {:else}
              {#each selected_project_tasks as task}
                <li>
                  <button on:click={() => select_task(task)}>
                    <span class="badge badge-secondary badge-outline">Task</span
                    >
                    {task.name}
                  </button>
                </li>
              {/each}
            {/if}
          </ul>
        </li>
      {:else}
        <li>
          <button on:click={() => select_project(project)}>
            {project.name}
          </button>
        </li>
      {/if}
    {/each}
  </ul>
</div>

<script lang="ts">
  import { current_project, projects } from "$lib/stores"
  import type { ProjectInfo, Task } from "$lib/stores"
  import { api_error_handler } from "$lib/utils/error_handlers"
  import { ui_state } from "$lib/stores"
  import { goto } from "$app/navigation"

  let id = "select-tasks-menu-" + Math.random().toString(36)

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

    goto(`/`, { replaceState: true })

    // Close the menu
    const menu = document.getElementById(id)
    if (
      menu &&
      menu.parentElement &&
      menu.parentElement instanceof HTMLDetailsElement
    ) {
      menu.parentElement.open = false
    }
  }
</script>

<ul class="menu menu-md bg-base-200 rounded-box" {id}>
  {#each project_list as project}
    {#if project.path == selected_project?.path}
      <li>
        <h1 class="flex flex-row pr-1">
          <div class="grow">
            <span class="badge badge-secondary badge-outline">Project</span>
            {project.name}
          </div>
          <div>
            <svg
              fill="#000000"
              class="w-3 h-3"
              version="1.1"
              id="Layer_1"
              xmlns="http://www.w3.org/2000/svg"
              xmlns:xlink="http://www.w3.org/1999/xlink"
              viewBox="0 0 407.437 407.437"
              xml:space="preserve"
            >
              <polygon
                points="386.258,91.567 203.718,273.512 21.179,91.567 0,112.815 203.718,315.87 407.437,112.815 "
              />
            </svg>
          </div>
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
                  {task.name}
                </button>
              </li>
            {/each}
          {/if}
        </ul>
      </li>
    {:else}
      <li>
        <button
          on:click={() => select_project(project)}
          class="flex flex-row pr-1"
        >
          <div class="grow">
            <span class="badge badge-secondary badge-outline">Project</span>
            {project.name}
          </div>
          <div>
            <svg
              fill="#000000"
              class="w-3 h-3"
              version="1.1"
              id="Layer_1"
              xmlns="http://www.w3.org/2000/svg"
              xmlns:xlink="http://www.w3.org/1999/xlink"
              viewBox="0 0 407.436 407.436"
              xml:space="preserve"
            >
              <polygon
                points="203.718,91.567 0,294.621 21.179,315.869 203.718,133.924 386.258,315.869 407.436,294.621 "
              />
            </svg>
          </div>
        </button>
      </li>
    {/if}
  {/each}
  <li class="pt-4">
    <a href="/setup/create_project" class="font-medium">+ New Project</a>
  </li>
</ul>

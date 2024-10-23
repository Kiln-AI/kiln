<script lang="ts">
  import AppPage from "../../../../app_page.svelte"
  import EditTask from "../../../../../(fullscreen)/setup/(setup)/create_task/edit_task.svelte"
  import { onMount } from "svelte"
  import { createKilnError, KilnError } from "$lib/utils/error_handlers"
  import { page } from "$app/stores"
  import type { Task } from "$lib/types"
  import { client } from "$lib/api_client"

  $: project_id = $page.params.project_id
  $: task_id = $page.params.task_id

  let task: Task | null = null
  let loading = false
  let error: KilnError | null = null

  onMount(async () => {
    get_task()
  })

  async function get_task() {
    try {
      loading = true
      if (!project_id || !task_id) {
        throw new Error("Project or task ID not set.")
      }
      // Always load the task from the server, even if it's the current task. We want the freshest data.
      const { data: task_response, error: get_error } = await client.GET(
        "/api/projects/{project_id}/tasks/{task_id}",
        {
          params: {
            path: {
              project_id,
              task_id,
            },
          },
        },
      )
      if (get_error) {
        throw get_error
      }
      task = task_response
    } catch (e) {
      if (e instanceof Error && e.message.includes("Load failed")) {
        error = new KilnError(
          "Could not load task. It may belong to a project you don't have access to.",
          null,
        )
      } else {
        error = createKilnError(e)
      }
    } finally {
      loading = false
    }
  }
</script>

<div class="max-w-[900px]">
  <AppPage
    title="Edit Task"
    subtitle={task?.id ? `Task ID: ${task.id}` : undefined}
  >
    {#if loading}
      <div class="w-full min-h-[50vh] flex justify-center items-center">
        <div class="loading loading-spinner loading-lg"></div>
      </div>
    {:else if error}
      <div class="text-red-500">Error loading task: {error.getMessage()}</div>
    {:else if task}
      <EditTask {task} redirect_on_created={null} />
    {/if}
  </AppPage>
</div>

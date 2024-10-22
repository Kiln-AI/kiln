<script lang="ts">
  import AppPage from "../../../../../app_page.svelte"
  import Run from "../../../../../run/run.svelte"
  import { current_task } from "$lib/stores"
  import { page } from "$app/stores"
  import { onMount } from "svelte"
  import { client } from "$lib/api_client"
  import { createKilnError, KilnError } from "$lib/utils/error_handlers"
  import type { TaskRun } from "$lib/types"

  $: run_id = $page.params.run_id
  $: task_id = $page.params.task_id
  $: project_id = $page.params.project_id

  // TODO: we need to remove task_id from the URL, or load it by ID. $current_task is a lie
  let run: TaskRun | null = null
  let loading = true
  let load_error: KilnError | null = null

  onMount(async () => {
    try {
      const { data, error } = await client.GET(
        "/api/projects/{project_id}/tasks/{task_id}/runs/{run_id}",
        {
          params: {
            path: { project_id, task_id, run_id: run_id },
          },
        },
      )
      if (error) {
        throw error
      }
      run = data
    } catch (error) {
      load_error = createKilnError(error)
    } finally {
      loading = false
    }
  })
</script>

<div class="max-w-[1400px]">
  <AppPage
    title="Dataset Run"
    subtitle={run?.id ? `Run ID: ${run.id}` : undefined}
  >
    {#if loading}
      <div class="w-full min-h-[50vh] flex justify-center items-center">
        <div class="loading loading-spinner loading-lg"></div>
      </div>
    {:else if load_error}
      <div class="text-error">{load_error.getMessage()}</div>
    {:else if run && $current_task}
      <Run initial_run={run} task={$current_task} {project_id} />
    {:else}
      <div class="text-gray-500 text-lg">Run not found</div>
    {/if}
  </AppPage>
</div>

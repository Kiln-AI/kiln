<script lang="ts">
  import AppPage from "../../app_page.svelte"
  import EditTask from "../../../(fullscreen)/setup/(setup)/create_task/edit_task.svelte"
  import { current_task, load_current_task, current_project } from "$lib/stores"
  import { onMount } from "svelte"
  import { createKilnError, KilnError } from "$lib/utils/error_handlers"

  $: task = $current_task
  let loading = false
  let error: KilnError | null = null

  onMount(async () => {
    // refresh on load to be sure we have the latest task
    try {
      error = null
      loading = true
      await load_current_task($current_project)
      task = $current_task
    } catch (e: unknown) {
      console.error(e)
      error = createKilnError(e)
    } finally {
      loading = false
    }
  })

  error = createKilnError("Task not found ASDF")
</script>

<div class="max-w-[900px]">
  <AppPage
    title="Edit Task"
    subtitle={task?.id ? `Task ID: ${task.id}` : undefined}
  >
    {#if error}
      <div class="text-red-500">{error.getMessage()}</div>
    {:else if loading}
      <div class="w-full min-h-[50vh] flex justify-center items-center">
        <div class="loading loading-spinner loading-lg"></div>
      </div>
    {:else if task}
      <EditTask {task} redirect_on_created={null} />
    {:else}
      <div class="text-gray-500 text-lg">Task not found</div>
    {/if}
  </AppPage>
</div>

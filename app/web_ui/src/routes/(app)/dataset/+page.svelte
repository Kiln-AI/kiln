<script lang="ts">
  import AppPage from "../app_page.svelte"
  import { client } from "$lib/api_client"
  import type { TaskRun } from "$lib/types"
  import { type KilnError, createKilnError } from "$lib/utils/error_handlers"
  import { onMount } from "svelte"
  import { ui_state } from "$lib/stores"

  let runs: TaskRun[] | null = null
  let error: KilnError | null = null
  let loading = true

  onMount(async () => {
    get_runs()
  })

  async function get_runs() {
    try {
      loading = true
      if (!$ui_state.current_project_id || !$ui_state.current_task_id) {
        throw new Error("Project or task ID not set.")
      }
      const { data: runs_response, error: get_error } = await client.GET(
        "/api/projects/{project_id}/tasks/{task_id}/runs",
        {
          params: {
            path: {
              project_id: $ui_state.current_project_id,
              task_id: $ui_state.current_task_id,
            },
          },
        },
      )
      if (get_error) {
        throw get_error
      }
      runs = runs_response
    } catch (e) {
      error = createKilnError(e)
    } finally {
      loading = false
    }
  }

  function formatDate(dateString: string | undefined): string {
    if (!dateString) {
      return "Unknown"
    }
    const date = new Date(dateString)
    const currentYear = new Date().getFullYear()
    const options: Intl.DateTimeFormatOptions = {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }

    if (date.getFullYear() !== currentYear) {
      options.year = "numeric"
    }

    return date.toLocaleString("en-US", options)
  }

  function previewText(
    text: string | undefined | null,
    maxLength: number = 100,
  ): string | null {
    if (!text) return null
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength) + "..."
  }
</script>

<AppPage
  title="Dataset"
  subtitle="Explore your runs, sample data, and ratings for this task."
>
  {#if loading}
    <div class="w-full min-h-[50vh] flex justify-center items-center">
      <div class="loading loading-spinner loading-lg"></div>
    </div>
  {:else if runs}
    <div class="overflow-x-auto">
      <table class="table">
        <!-- head -->
        <thead>
          <tr>
            <th>ID</th>
            <th>Rating</th>
            <th>Created At</th>
            <th>Input Preview</th>
            <th>Output Preview</th>
          </tr>
        </thead>
        <tbody>
          {#each runs as run}
            <tr class="hover cursor-pointer">
              <th>{run.id}</th>
              <td>
                {run.output.rating && run.output.rating.value
                  ? run.output.rating.type === "five_star"
                    ? "★".repeat(run.output.rating.value)
                    : run.output.rating.value + "(custom score)"
                  : "Unrated"}
              </td>
              <td>{formatDate(run.created_at)}</td>
              <td>{previewText(run.input) || "No input"}</td>
              <td>{previewText(run.output?.output) || "No output"}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else if error}
    <div
      class="w-full min-h-[50vh] flex flex-col justify-center items-center gap-2"
    >
      <div class="font-medium">Error Loading Dataset</div>
      <div class="text-gray-500 text-sm">
        {error.getMessage() || "An unknown error occurred"}
      </div>
    </div>
  {/if}
</AppPage>

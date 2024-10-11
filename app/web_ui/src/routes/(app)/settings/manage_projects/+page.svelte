<script lang="ts">
  import AppPage from "../../app_page.svelte"
  import { projects, load_projects } from "$lib/stores"
  import { api_error_handler } from "$lib/utils/error_handlers"
  import type { ProjectInfo } from "$lib/stores"

  async function remove_project(project: ProjectInfo) {
    try {
      if (
        confirm(
          `Are you sure you want to remove the project "${project.name}"?\n\nThis will remove it from the UI, but won't delete files from your disk.`,
        )
      ) {
        const response = await fetch(
          `http://localhost:8757/api/projects/${project.id}`,
          {
            method: "DELETE",
          },
        )
        const data = await response.json()
        api_error_handler(response, data)
        if (!response.ok) {
          throw new Error(data.message)
        }
        await load_projects()
      }
    } catch (e) {
      alert("Failed to remove project.\n\nReason: " + e)
    }
  }
</script>

<AppPage
  title="Manage Projects"
  subtitle="Add or remove projects"
  action_button="Add Project"
  action_button_href="/settings/create_project"
>
  {#if $projects == null}
    <div class=" mx-auto py-8 px-24">
      <span class="loading loading-spinner loading-md"></span>
    </div>
  {:else if $projects.error}
    <div class="p-16">{$projects.error}</div>
  {:else if $projects.projects.length == 0}
    <div class="p-16">No projects found</div>
  {:else}
    <div class="grid grid-cols-[repeat(auto-fill,minmax(18rem,1fr))] gap-4">
      {#each $projects.projects as project}
        <div
          class="card card-bordered border-gray-500 shadow-md py-4 px-6 h-48"
        >
          <div class="flex flex-col h-full">
            <div class="grow">
              <div class="font-medium">{project.name}</div>
              <div class="text-xs text-gray-500">
                {project.path}
              </div>
            </div>
            <div class="flex-none flex flex-row gap-2 w-full">
              <a
                href={`/settings/create_task?project_id=${project.id}`}
                class="btn btn-xs flex-grow"
              >
                Add Task
              </a>
              <button
                on:click={() => remove_project(project)}
                class="btn btn-xs flex-grow"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</AppPage>

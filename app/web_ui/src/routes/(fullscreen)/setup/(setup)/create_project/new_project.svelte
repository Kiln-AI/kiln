<script lang="ts">
  import { onMount } from "svelte"
  import { goto } from "$app/navigation"

  export let created = false
  // Prevents flash of complete UI if we're going to redirect
  export let redirect_on_created: string | null = null
  export let project_name = ""
  let project_name_error = false
  export let project_description = ""
  let error_message = ""

  const create_project = async () => {
    try {
      if (!project_name) {
        project_name_error = true
        error_message = "Project name is required"
        return
      } else {
        project_name_error = false
      }

      const response = await fetch("http://localhost:8757/api/project", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_name: project_name,
          project_description: project_description,
        }),
      })
      const data = await response.json()
      if (response.status !== 200) {
        throw new Error(
          data["message"] || "Unknown error (status: " + response.status + ")",
        )
      }
      if (redirect_on_created) {
        goto(redirect_on_created)
      }
      created = true
    } catch (error) {
      if (
        error instanceof Error &&
        error.message === "The string did not match the expected pattern."
      ) {
        error_message = "Unexpected response from server"
      } else {
        error_message = error instanceof Error ? error.message : "Unknown error"
      }
    }
  }

  onMount(() => {
    const projectNameInput = document.getElementById("project_name")
    if (projectNameInput) {
      projectNameInput.focus()
    }
  })
</script>

<div class="flex flex-col gap-2 max-w-[800px] mx-auto">
  {#if !created}
    <form class="flex flex-col gap-2 max-w-[800px] lg:w-96 mx-auto">
      <label for="project_name" class="text-sm font-medium text-left"
        >Project Name</label
      >
      <input
        type="text"
        placeholder="Project Name"
        id="project_name"
        class="input input-bordered w-full {project_name_error
          ? 'input-error'
          : ''}"
        bind:value={project_name}
      />
      <label
        for="project_description"
        class="text-sm font-medium text-left pt-6 flex flex-row"
        ><span class="grow">Project Description</span>
        <span class="pl-1 text-xs text-gray-500 flex-none">Optional</span
        ></label
      >
      <textarea
        placeholder="Project Description"
        id="project_description"
        class="textarea textarea-bordered w-full h-24 mb-6 wrap-pre text-left align-top"
        bind:value={project_description}
      ></textarea>
      {#if error_message}
        <div class="text-sm text-center text-error">{error_message}</div>
      {/if}
      <button
        type="submit"
        class="btn btn-primary mt-2"
        on:click={create_project}>Create Project</button
      >
    </form>
  {:else if !redirect_on_created}
    <h2 class="text-xl font-medium text-center">Project Created!</h2>
    <p class="text-sm text-center">
      Your new project "{project_name}" has been created.
    </p>
  {/if}
</div>

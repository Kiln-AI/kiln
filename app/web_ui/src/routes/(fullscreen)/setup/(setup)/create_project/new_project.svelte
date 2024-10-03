<script lang="ts">
  import { onMount } from "svelte"

  export let created = false
  let project_name = ""

  const create_project = () => {
    console.log("create_project", project_name)
    created = true
  }

  onMount(() => {
    const projectNameInput = document.getElementById("project_name")
    if (projectNameInput) {
      projectNameInput.focus()
    }
  })
</script>

<div class="flex flex-col gap-2 max-w-[400px] mx-auto">
  {#if !created}
    <form class="flex flex-col gap-2">
      <label for="project_name" class="text-sm font-medium text-left"
        >Project Name</label
      >
      <input
        type="text"
        placeholder="Project Name"
        id="project_name"
        class="input input-bordered w-full max-w-[300px]"
        bind:value={project_name}
      />
      <button type="submit" class="btn btn-primary" on:click={create_project}
        >Create</button
      >
    </form>
  {:else}
    <h2 class="text-xl font-medium text-center">Project Created!</h2>
    <p class="text-sm text-center">
      Your new project "{project_name}" has been created.
    </p>
  {/if}
</div>

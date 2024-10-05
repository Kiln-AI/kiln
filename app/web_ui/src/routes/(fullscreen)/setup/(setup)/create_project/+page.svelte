<script lang="ts">
  import EditProject from "./edit_project.svelte"

  let project_name = ""
  let project_description = ""

  function example_project() {
    project_name = "Example Project"
    project_description = "This is an example project just to try things out."
  }
</script>

<div class="grow"></div>
<div class="flex-none flex flex-row items-center justify-center">
  <img src="/logo.svg" alt="logo" class="size-8 mb-3" />
</div>
<h1 class="text-2xl lg:text-4xl flex-none font-bold text-center">
  Create a Project
</h1>
<h3 class="text-base font-medium text-center mt-3 max-w-[600px] mx-auto">
  "Example" is fine if you're just trying things out.
</h3>
<h3 class="text-sm text-center mt-1 max-w-[600px] mx-auto">
  Just exploring?
  <button class="link text-primary" on:click={example_project}
    >Create an example</button
  >
</h3>

<div class="flex-none min-h-[50vh] py-8 px-4 h-full flex flex-col py-18">
  <EditProject
    redirect_on_created="/setup/create_task"
    bind:project_name
    bind:project_description
  />
</div>

<div class="grow-[1.5]"></div>

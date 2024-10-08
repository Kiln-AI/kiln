<script lang="ts">
  import EditTask from "./edit_task.svelte"
  import { type TaskRequirement } from "./task_types"

  let task_name = ""
  let task_description = ""
  let task_requirements: TaskRequirement[] = []
  let editTaskComponent: EditTask

  function example_task() {
    if (editTaskComponent.has_edits()) {
      if (
        !confirm("This will replace your current task edits. Are you sure?")
      ) {
        return
      }
    }

    task_name = "Example Task"
    task_description = "This is an example task"
    task_requirements = [
      {
        name: "Example Requirement",
        description: "This is an example requirement",
        instruction: "This is an example requirement",
        priority: 1,
      },
    ]
  }
</script>

<div class="grow"></div>
<div class="flex-none flex flex-row items-center justify-center">
  <img src="/logo.svg" alt="logo" class="size-8 mb-3" />
</div>
<h1 class="text-2xl lg:text-4xl flex-none font-bold text-center">
  Create a Task
</h1>
<h3 class="text-base font-medium text-center mt-3 max-w-[600px] mx-auto">
  Let's define what this model should do. We call this a "task".
</h3>
<h3 class="text-sm text-center mt-1 max-w-[600px] mx-auto">
  Just exploring?
  <button class="link text-primary" on:click={example_task}
    >Try an example.</button
  >
</h3>

<div class="flex-none min-h-[50vh] py-8 px-4 h-full flex flex-col py-18">
  <!-- TODO_P0 -->
  <EditTask
    redirect_on_created="/"
    bind:task_name
    bind:task_description
    bind:task_requirements
    bind:this={editTaskComponent}
  />
</div>

<div class="grow-[1.5]"></div>

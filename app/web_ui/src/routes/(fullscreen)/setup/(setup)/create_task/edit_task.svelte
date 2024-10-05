<script lang="ts">
  import { goto } from "$app/navigation"
  import { onMount } from "svelte"
  import { type TaskRequirement } from "./task_types"
  import { dev } from "$app/environment"

  // Prevents flash of complete UI if we're going to redirect
  export let redirect_on_created: string | null = null

  export let task_name: string = ""
  export let task_description: string = ""
  export let task_instructions: string = ""
  export let task_requirements: TaskRequirement[] = []

  export function has_edits() {
    let edited_requirement = false
    task_requirements.forEach((requirement) => {
      if (
        requirement.name ||
        requirement.description ||
        requirement.instructions
      ) {
        edited_requirement = true
      }
    })
    if (task_name || task_description || edited_requirement) {
      return true
    }
    return false
  }

  function add_requirement(focus = true) {
    console.log("add_requirement")
    task_requirements = [
      ...task_requirements,
      {
        name: "",
        description: "",
        instructions: "",
        priority: 1,
      },
    ]
    if (focus) {
      focus_field("requirement_name_" + (task_requirements.length - 1))
    }
  }

  // Add one empty requirement to start so the form isn't empty
  if (task_requirements.length === 0) {
    add_requirement(false)
  }

  function remove_requirement(index: number) {
    if (
      confirm(
        "Are you sure you want to remove requirement #" + (index + 1) + "?",
      )
    ) {
      task_requirements = task_requirements.filter((_, i) => i !== index)
      // Move the page to the "requirements_part" anchor
      const requirementsPart = document.getElementById("requirements_part")
      if (requirementsPart) {
        goto("#requirements_part")
        requirementsPart.scrollIntoView({ behavior: "smooth", block: "start" })
      }
    }
  }

  let error_fields: Record<string, string> = {}

  async function focus_field(field: string) {
    // Async as the forms' validation is also trying to set focus
    await new Promise((resolve) => setTimeout(resolve, 10))
    const input = document.getElementById(field)
    if (input) {
      input.focus()
    }
  }

  function validate(focus_on_error = false) {
    console.log("validate", task_name, task_description, task_instructions)
    error_fields = {}
    if (!task_name.trim()) {
      error_fields["task_name"] = "Task name is required"
    }
    if (!task_instructions.trim()) {
      error_fields["task_instructions"] = "Task instructions are required"
    }
    task_requirements.forEach((requirement, index) => {
      if (!requirement.name.trim()) {
        error_fields[`requirement_name_${index}`] =
          "Requirement #" + (index + 1) + " missing name"
      }
      if (!requirement.instructions.trim()) {
        error_fields[`requirement_instructions_${index}`] =
          "Requirement #" + (index + 1) + " missing instructions"
      }
    })

    if (focus_on_error && Object.keys(error_fields).length > 0) {
      focus_field(Object.keys(error_fields)[0])
    }
  }

  function create_task() {
    console.log("create_task", task_name, task_description)
    validate(true)
    if (Object.keys(error_fields).length > 0) {
      return
    }
    console.log("create_task", task_name, task_description)
    console.log("redirect_on_created", redirect_on_created)
  }

  onMount(() => {
    // Add onchange handlers to all inputs and textareas to clear errors
    const inputElements = document.querySelectorAll("input, textarea")
    inputElements.forEach((element) => {
      element.addEventListener("input", field_edited)
    })

    // Prevent losing data on refresh/navigation, without confirmation
    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload)
    }
  })
  function handleBeforeUnload(event: BeforeUnloadEvent) {
    if (!dev && has_edits()) {
      event.preventDefault()
    }
  }

  // Clear errors after editing a field to remove red
  function field_edited(e: Event) {
    const field = (e.target as HTMLElement).id
    if (error_fields[field]) {
      delete error_fields[field]
      error_fields = error_fields // Trigger reactivity
    }
  }
</script>

<div class="flex flex-col gap-2 max-w-[800px] mx-auto">
  <form class="flex flex-col gap-2 max-w-[800px] lg:w-[500px] mx-auto">
    <div class="text-xl font-bold">Part 1: Task Overview</div>
    <label for="task_name" class="text-sm font-medium text-left"
      >Task Name
      <div class="text-xs text-gray-500">
        A description for you and your team, not used by the model.
      </div>
    </label>
    <input
      type="text"
      placeholder="Task Name"
      id="task_name"
      class="input input-bordered w-full {error_fields['task_name']
        ? 'input-error'
        : ''}"
      required
      bind:value={task_name}
    />

    <label
      for="task_description"
      class="text-sm font-medium text-left pt-6 flex flex-col gap-1"
    >
      <div class="flex flex-row">
        <span class="grow">Task Description</span>
        <span class="pl-1 text-xs text-gray-500 flex-none">Optional</span>
      </div>
      <div class="text-xs text-gray-500">
        A description for you and your team, not used by the model.
      </div>
    </label>
    <textarea
      placeholder="Task Description"
      id="task_description"
      class="textarea textarea-bordered w-full h-18 wrap-pre text-left align-top
       {error_fields['task_description'] ? 'textarea-error' : ''}"
      bind:value={task_description}
    />

    <label
      for="task_instructions"
      class="text-sm font-medium text-left pt-6 flex flex-col gap-1"
    >
      <div class="flex flex-row">
        <span class="grow">Task Instructions</span>
      </div>
      <div class="text-xs text-gray-500">
        Required. This will form the basis of the model's prompt. Keep this high
        level, and define any details in the 'Requirements' section below.
      </div>
    </label>
    <textarea
      placeholder="Task Instructions"
      id="task_instructions"
      class="textarea textarea-bordered w-full h-18 wrap-pre text-left align-top
       {error_fields['task_instructions'] ? 'textarea-error' : ''}"
      bind:value={task_instructions}
      required
    />

    <div class="text-sm font-medium text-left pt-6 flex flex-col gap-1">
      <div class="text-xl font-bold" id="requirements_part">
        Part 2: Task Requirements
      </div>
      <div class="text-xs text-gray-500">
        Define any requirements for the task. These will become part of the
        prompt, but are also broken out for model evals and training.
      </div>
    </div>
    {#if task_requirements.length > 0}
      <div class="flex flex-col gap-3 mt-6">
        {#each task_requirements as requirement, req_index}
          <div class="flex flex-col gap-3">
            <div class="flex flex-row gap-1">
              <div class="grow flex flex-col gap-1">
                <label
                  for="requirement_name_{req_index}"
                  class="text-xs font-medium text-left text-gray-500"
                  >Requirement #{req_index + 1}: Name</label
                >
                <input
                  type="text"
                  placeholder="Requirement Name"
                  id="requirement_name_{req_index}"
                  class="input input-bordered w-full {error_fields[
                    'requirement_name_' + req_index
                  ]
                    ? 'input-error'
                    : ''}"
                  bind:value={requirement.name}
                />
              </div>
              <div class="flex flex-col gap-1">
                <label
                  for="requirement_priority_{req_index}"
                  class="text-xs font-medium text-left text-gray-500"
                  >Priority</label
                >
                <select
                  id="requirement_priority_{req_index}"
                  class="select select-bordered"
                  bind:value={requirement.priority}
                >
                  <option value={0}>P0 - Critical</option>
                  <option value={1}>P1 - High</option>
                  <option value={2}>P2 - Medium</option>
                  <option value={3}>P3 - Low</option>
                </select>
              </div>
            </div>
            <div class="grow flex flex-col gap-1">
              <label
                for="requirement_instructions_{req_index}"
                class="text-xs font-medium text-left text-gray-500"
                >Instructions</label
              >
              <textarea
                placeholder="Requirement Instructions"
                id="requirement_instructions_{req_index}"
                class="textarea textarea-bordered w-full h-18 wrap-pre text-left align-top
                 {error_fields['requirement_instructions_' + req_index]
                  ? 'textarea-error'
                  : ''}"
                bind:value={requirement.instructions}
              />
            </div>
            <div class="text-right text-xs pb-2">
              <button
                class="link"
                on:click={() => remove_requirement(req_index)}
              >
                Remove Requirement #{req_index + 1}
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}

    <div class="flex place-content-center">
      <button class="btn btn-sm" on:click={() => add_requirement(true)}>
        Add Requirement
      </button>
    </div>

    <div class="h-4" />

    {#if Object.keys(error_fields).length > 0}
      <div class="text-sm text-center text-error flex flex-col gap-1">
        <div>Please correct the following errors:</div>
        {#each Object.entries(error_fields) as [field, error]}
          <button class="text-xs link" on:click={() => focus_field(field)}
            >{error}</button
          >
        {/each}
      </div>
    {/if}
    <button type="submit" class="btn btn-primary mt-2" on:click={create_task}
      >Create Task</button
    >
  </form>
</div>

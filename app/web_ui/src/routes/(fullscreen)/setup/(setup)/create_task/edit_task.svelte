<script lang="ts">
  import { type TaskRequirement } from "./task_types"
  import FormElement from "$lib/utils/form_element.svelte"
  import FormList from "$lib/utils/form_list.svelte"
  import FormContainer from "$lib/utils/form_container.svelte"
  import { current_project } from "$lib/stores"

  // Prevents flash of complete UI if we're going to redirect
  export let redirect_on_created: string | null = null

  export let task_name: string = ""
  export let task_description: string = ""
  export let task_instructions: string = ""
  export let task_requirements: TaskRequirement[] = []
  let custom_error_message: string | null = null
  let submitting = false

  // Warn before unload if there's any user input
  $: warn_before_unload =
    [task_name, task_description, task_instructions].some((value) => !!value) ||
    task_requirements.some((req) => !!req.name || !!req.instructions)

  function create_task() {
    try {
      if (!$current_project) {
        custom_error_message =
          "You must create a project before creating a task"
        return
      }
      console.log("TODO_P0 redirect_on_created", redirect_on_created)
    } catch (error) {
      custom_error_message = "Unknown error creating task: " + error
    } finally {
      submitting = false
    }
  }
</script>

<div class="flex flex-col gap-2 max-w-[500px] lg:w-[500px] mx-auto">
  <FormContainer
    submit_label="Create Task"
    on:submit={create_task}
    bind:warn_before_unload
    bind:custom_error_message
    bind:submitting
  >
    <div class="text-xl font-bold">Part 1: Overview</div>
    <FormElement
      label="Task Name"
      id="task_name"
      description="A description for you and your team, not used by the model."
      bind:value={task_name}
    />

    <FormElement
      label="Task Description"
      inputType="textarea"
      id="task_description"
      description="A description for you and your team, not used by the model."
      optional={true}
      bind:value={task_description}
    />

    <FormElement
      label="Task Instructions"
      inputType="textarea"
      id="task_instructions"
      description="This will form the basis of the model's prompt. Keep this high level, and define any details in the 'Requirements' section below."
      bind:value={task_instructions}
    />

    <div class="text-sm font-medium text-left pt-6 flex flex-col gap-1">
      <div class="text-xl font-bold" id="requirements_part">
        Part 2: Requirements
      </div>
      <div class="text-xs text-gray-500">
        Define any requirements for the task. These will become part of the
        prompt, but are also broken out for model evals and training.
      </div>
    </div>

    <!-- Requirements Section -->
    <FormList
      content={task_requirements}
      content_label="Requirement"
      start_with_one={true}
      empty_content={{
        name: "",
        description: "",
        instructions: "",
        priority: 1,
      }}
      let:item_index
    >
      <div class="flex flex-col gap-3">
        <div class="flex flex-row gap-1">
          <div class="grow flex flex-col gap-1">
            <FormElement
              label="Requirement Name"
              id="requirement_name_{item_index}"
              light_label={true}
              bind:value={task_requirements[item_index].name}
            />
          </div>
          <div class="flex flex-col gap-1">
            <FormElement
              label="Priority"
              inputType="select"
              id="requirement_priority_{item_index}"
              light_label={true}
              select_options={[
                [0, "P0 - Critical"],
                [1, "P1 - High"],
                [2, "P2 - Medium"],
                [3, "P3 - Low"],
              ]}
              bind:value={task_requirements[item_index].priority}
            />
          </div>
        </div>
        <div class="grow flex flex-col gap-1">
          <FormElement
            label="Instructions"
            inputType="textarea"
            id="requirement_instructions_{item_index}"
            light_label={true}
            bind:value={task_requirements[item_index].instructions}
          />
        </div>
      </div>
    </FormList>
  </FormContainer>
</div>

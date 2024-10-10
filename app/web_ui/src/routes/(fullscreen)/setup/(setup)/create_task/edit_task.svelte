<script lang="ts">
  import { type TaskRequirement } from "./task_types"
  import FormElement from "$lib/utils/form_element.svelte"
  import FormList from "$lib/utils/form_list.svelte"
  import FormContainer from "$lib/utils/form_container.svelte"
  import SchemaSection from "./schema_section.svelte"
  import {
    example_schema_model,
    schema_from_model,
  } from "$lib/utils/json_schema_editor/json_schema_templates"
  import type { SchemaModel } from "$lib/utils/json_schema_editor/json_schema_templates"
  import { current_project } from "$lib/stores"
  import { goto } from "$app/navigation"
  import {
    KilnError,
    api_error_handler,
    createKilnError,
  } from "$lib/utils/error_handlers"
  import { ui_state, projects } from "$lib/stores"
  import { get } from "svelte/store"
  import { browser } from "$app/environment"
  import { page } from "$app/stores"

  // Prevents flash of complete UI if we're going to redirect
  export let redirect_on_created: string | null = null

  export let task_name: string = ""
  export let task_description: string = ""
  export let task_instructions: string = ""
  export let task_requirements: TaskRequirement[] = []
  export let task_input_plaintext = true
  export let task_input_schema: SchemaModel = example_schema_model()
  export let task_output_plaintext = true
  export let task_output_schema: SchemaModel = example_schema_model()

  let error: KilnError | null = null
  let submitting = false

  // Warn before unload if there's any user input
  $: warn_before_unload =
    [task_name, task_description, task_instructions].some((value) => !!value) ||
    task_requirements.some((req) => !!req.name || !!req.instruction)

  export let target_project_path: string | null = null

  $: {
    if (browser) {
      target_project_path =
        new URLSearchParams($page.url.searchParams).get("project_path") ||
        $current_project?.path ||
        null
    } else {
      target_project_path = $current_project?.path || null
    }
  }

  export let project_target_name: string | null = null
  $: {
    if (!target_project_path) {
      project_target_name = null
    } else {
      project_target_name =
        $projects?.projects.find((p) => p.path === target_project_path)?.name ||
        target_project_path
    }
  }

  async function create_task() {
    try {
      if (!target_project_path) {
        error = new KilnError(
          "You must create a project before creating a task",
          null,
        )
        return
      }
      let body: Record<string, unknown> = {
        name: task_name,
        description: task_description,
        instruction: task_instructions,
        requirements: task_requirements,
      }
      if (!task_input_plaintext) {
        body["input_json_schema"] = JSON.stringify(
          schema_from_model(task_input_schema),
        )
      }
      if (!task_output_plaintext) {
        body["output_json_schema"] = JSON.stringify(
          schema_from_model(task_output_schema),
        )
      }
      const project_path = target_project_path
      if (!project_path) {
        throw new KilnError("Current project not found", null)
      }
      const encodedProjectPath = encodeURIComponent(project_path)
      const response = await fetch(
        `http://localhost:8757/api/task?project_path=${encodedProjectPath}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        },
      )
      const data = await response.json()
      api_error_handler(response, data)
      error = null
      // Make this the current task
      ui_state.set({
        ...get(ui_state),
        current_task_id: data.id,
        current_project_path: target_project_path,
      })
      if (redirect_on_created) {
        goto(redirect_on_created)
      }
    } catch (e) {
      error = createKilnError(e)
    } finally {
      submitting = false
    }
  }

  export function has_edits(): boolean {
    let has_edited_requirements = task_requirements.some(
      (req) => !!req.name || !!req.instruction,
    )
    return (
      !!task_name ||
      !!task_description ||
      !!task_instructions ||
      has_edited_requirements ||
      !task_input_plaintext ||
      task_input_schema.properties.length > 0 ||
      !task_output_plaintext ||
      task_output_schema.properties.length > 0
    )
  }
</script>

<div class="flex flex-col gap-2 w-full">
  <FormContainer
    submit_label="Create Task"
    on:submit={create_task}
    bind:warn_before_unload
    bind:error
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
            bind:value={task_requirements[item_index].instruction}
          />
        </div>
      </div>
    </FormList>

    <div class="text-sm font-medium text-left pt-6 flex flex-col gap-1">
      <div class="text-xl font-bold" id="requirements_part">
        Part 3: Input Schema
      </div>
      <div class="text-xs text-gray-500">
        What kind of input will the model receive?
      </div>
    </div>

    <SchemaSection
      bind:schema_model={task_input_schema}
      bind:plaintext={task_input_plaintext}
    />

    <div class="text-sm font-medium text-left pt-6 flex flex-col gap-1">
      <div class="text-xl font-bold" id="requirements_part">
        Part 4: Output Schema
      </div>
      <div class="text-xs text-gray-500">
        What kind of output will the model produce?
      </div>
    </div>

    <SchemaSection
      bind:schema_model={task_output_schema}
      bind:plaintext={task_output_plaintext}
    />
  </FormContainer>
</div>

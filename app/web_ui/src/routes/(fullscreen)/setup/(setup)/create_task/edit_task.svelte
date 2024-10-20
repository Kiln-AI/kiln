<script lang="ts">
  import { type TaskRequirement } from "$lib/types"
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
  import { KilnError, createKilnError } from "$lib/utils/error_handlers"
  import { ui_state, projects } from "$lib/stores"
  import { get } from "svelte/store"
  import { page } from "$app/stores"
  import { client } from "$lib/api_client"

  // Prevents flash of complete UI if we're going to redirect
  export let redirect_on_created: string | null = "/"

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

  export let target_project_id: string | null = null

  $: {
    target_project_id =
      new URLSearchParams($page.url.searchParams).get("project_id") ||
      $current_project?.id ||
      null
  }

  export let project_target_name: string | null = null
  $: {
    if (!target_project_id) {
      project_target_name = null
    } else {
      project_target_name =
        $projects?.projects.find((p) => p.id === target_project_id)?.name ||
        "Project ID: " + target_project_id
    }
  }

  async function create_task() {
    try {
      if (!target_project_id) {
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
      const project_id = target_project_id
      if (!project_id) {
        throw new KilnError("Current project not found", null)
      }
      const { data, error: post_error } = await client.POST(
        "/api/projects/{project_id}/task",
        {
          params: {
            path: {
              project_id,
            },
          },
          // @ts-expect-error This API is not typed
          body: body,
        },
      )
      if (post_error) {
        throw post_error
      }

      error = null
      // Make this the current task
      ui_state.set({
        ...get(ui_state),
        current_task_id: data.id,
        current_project_id: target_project_id,
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
      (!task_input_plaintext && task_input_schema.properties.length > 0) ||
      (!task_output_plaintext && task_output_schema.properties.length > 0)
    )
  }

  function example_task() {
    if (has_edits()) {
      if (
        !confirm("This will replace your current task edits. Are you sure?")
      ) {
        return
      }
    }

    task_name = "Joke Generator"
    task_description = "An example task from the KilnAI team."
    task_instructions =
      "Generate a joke, given a theme. The theme will be provided as a word or phrase as the input to the model. The assistant should output a joke that is funny and relevant to the theme. The output should include a setup and punchline."
    task_requirements = [
      {
        name: "Keep on topic",
        instruction:
          "Keep the joke on topic. If the user specifies a theme, the joke must be related to that theme.",
        priority: 1,
      },
      {
        name: "Keep it clean",
        instruction:
          "Avoid any jokes that are offensive or inappropriate. Keep the joke clean and appropriate for all audiences.",
        priority: 2,
      },
      {
        name: "Be funny",
        instruction:
          "Make the joke funny and engaging. It should be something that someone would want to tell to their friends. Something clever, not just a simple pun.",
        priority: 1,
      },
    ]
    task_input_plaintext = true
    task_output_plaintext = false
    task_output_schema = {
      properties: [
        {
          title: "Setup",
          description: "The setup to the joke",
          type: "string",
          required: true,
        },
        {
          title: "Punchline",
          description: "The punchline to the joke",
          type: "string",
          required: true,
        },
      ],
    }
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
    <div>
      <div class="text-xl font-bold">Part 1: Overview</div>
      <h3 class="text-sm mt-1">
        Just exploring?
        <button class="link text-primary" on:click={example_task}
          >Try an example.</button
        >
      </h3>
    </div>
    <FormElement
      label="Task Name"
      id="task_name"
      description="A description for you and your team, not used by the model."
      bind:value={task_name}
      max_length={120}
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
              max_length={20}
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

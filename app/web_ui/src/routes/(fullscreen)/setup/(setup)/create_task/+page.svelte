<script lang="ts">
  import EditTask from "./edit_task.svelte"
  import { type TaskRequirement } from "./task_types"
  import type { SchemaModel } from "$lib/utils/json_schema_editor/json_schema_templates"
  import { example_schema_model } from "$lib/utils/json_schema_editor/json_schema_templates"

  let task_name = ""
  let task_description = ""
  let task_instructions = ""
  let task_requirements: TaskRequirement[] = []
  let task_input_schema: SchemaModel = example_schema_model
  let task_output_schema: SchemaModel = example_schema_model
  let task_input_plaintext = true
  let task_output_plaintext = true
  let editTaskComponent: EditTask

  function example_task() {
    if (editTaskComponent.has_edits()) {
      if (
        !confirm("This will replace your current task edits. Are you sure?")
      ) {
        return
      }
    }

    task_name = "Joke Generator"
    task_description = "An example task from the KilnAI team."
    task_instructions =
      "Generate a joke, given a theme. The theme will be provided as a word or phrase as the input to the model. The assistant should output a joke that is funny and relevant to the theme. The output should include a setup, punchline, and a rating of how funny it is on a scale of 1 to 10."
    task_requirements = [
      {
        name: "Keep on topic",
        instruction:
          "Keep the joke on topic. If the user specifies a theme, the joke must be related to that theme.",
        priority: 1,
      },
      {
        name: "Follow the style specified",
        instruction:
          "Follow the style specified in the input. For example, if the user specifies 'This joke should be for young children', follow that stylistic instruction.",
        priority: 2,
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
        {
          title: "Rating",
          description: "The rating of the joke, from 1 to 10",
          type: "integer",
          required: true,
        },
      ],
    }
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
    bind:task_input_schema
    bind:task_output_schema
    bind:task_input_plaintext
    bind:task_output_plaintext
    bind:task_instructions
    bind:this={editTaskComponent}
  />
</div>

<div class="grow-[1.5]"></div>

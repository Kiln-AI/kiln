<script lang="ts">
  import AppPage from "../app_page.svelte"
  import { current_task, current_project, ui_state } from "$lib/stores"
  import { createKilnError } from "$lib/utils/error_handlers"
  import FormContainer from "$lib/utils/form_container.svelte"
  import FormElement from "$lib/utils/form_element.svelte"
  import { KilnError } from "$lib/utils/error_handlers"
  import Run from "./run.svelte"
  import { client } from "$lib/api_client"
  import type { TaskRun } from "$lib/types"
  import AvailableModelsDropdown from "./available_models_dropdown.svelte"
  // TODO: implement checking input content
  let warn_before_unload = false
  // TODO UI for errors
  let error: KilnError | null = null
  let submitting = false
  let run_complete = false

  // TODO: also structured input
  let plaintext_input = ""

  // TODO: real values for adapters and models
  let prompt_method = "basic"
  let model: string = $ui_state.selected_model

  $: model_name = model.split("/")[1]
  $: provider = model.split("/")[0]

  let response: TaskRun | null = null
  $: run_focus = !response

  $: subtitle = $current_task ? "Task: " + $current_task.name : ""

  async function run_task() {
    try {
      submitting = true
      error = null
      response = null
      const {
        data, // only present if 2XX response
        error: fetch_error, // only present if 4XX or 5XX response
      } = await client.POST("/api/projects/{project_id}/tasks/{task_id}/run", {
        params: {
          path: {
            project_id: $current_project?.id || "",
            task_id: $current_task?.id || "",
          },
        },
        body: {
          model_name: model_name,
          provider: provider,
          plaintext_input: plaintext_input,
        },
      })
      if (fetch_error) {
        throw fetch_error
      }
      response = data
    } catch (e) {
      error = createKilnError(e)
    } finally {
      submitting = false
    }
  }

  function clear_all() {
    plaintext_input = ""
    response = null
  }

  function next_task_run() {
    // Keep the input, but clear the response
    response = null
    run_complete = false
  }
</script>

<AppPage
  title="Run"
  bind:subtitle
  action_button="Clear All"
  action_button_action={clear_all}
>
  <div class="max-w-[1400px]">
    <div class="flex flex-col xl:flex-row gap-8 xl:gap-16">
      <div class="grow">
        <div class="text-xl font-bold">Input</div>
        <FormContainer
          submit_label="Run"
          on:submit={run_task}
          bind:warn_before_unload
          bind:error
          bind:submitting
          bind:primary={run_focus}
        >
          <div class="flex flex-row gap-2 items-center"></div>
          <FormElement
            label="Plaintext Input"
            inputType="textarea"
            bind:value={plaintext_input}
            id="plaintext_input"
          />
        </FormContainer>
      </div>
      <div class="w-72 2xl:w-96 flex-none flex flex-col gap-4">
        <div class="text-xl font-bold">Options</div>
        <FormElement
          label="Prompt Method"
          inputType="select"
          bind:value={prompt_method}
          id="prompt_method"
          select_options={[
            ["basic", "Basic Prompt (Zero Shot)"],
            ["few_shot", "Few Shot"],
            ["many_shot", "Multi Shot"],
          ]}
        />
        <AvailableModelsDropdown bind:model />
      </div>
    </div>
    {#if $current_task && !submitting && response != null && $current_project?.id}
      <div class="mt-10 xl:mt-32">
        <Run
          initial_run={response}
          task={$current_task}
          project_id={$current_project.id}
          bind:model_name
          bind:provider
          bind:run_complete
        />
      </div>
    {/if}
  </div>
  {#if run_complete}
    <div class="flex flex-col md:flex-row gap-6 place-content-center mt-10">
      <p class="text-lg text-gray-500 mt-5">🎉 Ready for your next task?</p>
      <button
        class="btn btn-primary mt-2 min-w-48"
        on:click={() => next_task_run()}
      >
        Next Run
      </button>
    </div>
  {/if}
</AppPage>

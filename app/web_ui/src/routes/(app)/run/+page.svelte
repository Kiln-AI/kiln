<script lang="ts">
  import AppPage from "../app_page.svelte"
  import { current_task, current_project } from "$lib/stores"
  import { createKilnError } from "$lib/utils/error_handlers"
  import FormContainer from "$lib/utils/form_container.svelte"
  import FormElement from "$lib/utils/form_element.svelte"
  import { KilnError } from "$lib/utils/error_handlers"
  import Run from "./run.svelte"
  import { client } from "$lib/api_client"
  import type { TaskRun } from "$lib/types"

  // TODO: implement checking input content
  let warn_before_unload = false
  // TODO UI for errors
  let error: KilnError | null = null
  let submitting = false

  // TODO: also structured input
  let plaintext_input = ""

  // TODO: real values for adapters and models
  let prompt_method = "basic"
  let model = "openai/gpt_4o_mini"

  $: model_name = model.split("/")[1]
  $: provider = model.split("/")[0]

  let response: TaskRun | null = null

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
</script>

<AppPage title="Run" bind:subtitle>
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
        <FormElement
          label="Model"
          bind:value={model}
          id="model"
          inputType="select"
          select_options_grouped={[
            [
              "OpenAI",
              [
                ["openai/gpt_4o", "GPT 4o"],
                ["openai/gpt_4o_mini", "GPT 4o Mini"],
              ],
            ],
            [
              "OpenRouter",
              [
                ["openrouter/gpt_4o", "GPT 4o"],
                ["openrouter/gpt_4o_mini", "GPT 4o Mini"],
              ],
            ],
            [
              "Groq",
              [
                ["groq/llama_3_1_8b", "Llama 3.1 8b"],
                ["groq/llama_3_1_70b", "Llama 3.1 70b"],
              ],
            ],
            [
              "Ollama",
              [
                ["ollama/llama_3_1_8b", "Llama 3.1 8b"],
                ["ollama/llama_3_1_70b", "Llama 3.1 70b"],
              ],
            ],
            [
              "Amazon Bedrock",
              [
                ["amazon_bedrock/llama_3_1_8b", "Llama 3.1 8b"],
                ["amazon_bedrock/llama_3_1_70b", "Llama 3.1 70b"],
              ],
            ],
          ]}
        />
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
        />
      </div>
    {/if}
  </div>
</AppPage>

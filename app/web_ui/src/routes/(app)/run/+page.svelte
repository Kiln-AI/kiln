<script lang="ts">
  import AppPage from "../app_page.svelte"
  import { current_task, current_project } from "$lib/stores"
  import { createKilnError } from "$lib/utils/error_handlers"
  import FormContainer from "$lib/utils/form_container.svelte"
  import FormElement from "$lib/utils/form_element.svelte"
  import { KilnError } from "$lib/utils/error_handlers"
  import Run from "./run.svelte"
  import createClient from "openapi-fetch"
  import { type components, type paths } from "$lib/api_schema.d"
  import Output from "./output.svelte"

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

  // TODO: remove test data
  let response: components["schemas"]["RunTaskResponse"] | null = {
    run: {
      v: 1,
      id: "123",
      input: "asdf",
      model_type: "run",
      input_source: {
        type: "human",
        properties: {
          a: 1,
          b: "asdf",
        },
      },
      output: {
        v: 1,
        output: '{"a": 1, "b": "asdf"}',
        source: {
          type: "synthetic",
          properties: {
            model_type: "openai/gpt_4o_mini",
          },
        },
        model_type: "output",
        rating: {
          v: 1,
          id: "270303291267",
          created_at: "2024-10-16T10:24:00.872146",
          created_by: "scosman",
          type: "five_star",
          value: 4,
          requirement_ratings: {
            "570793306757": 3,
          },
          model_type: "task_output_rating",
        },
      },
    },
    raw_output:
      '{"setup": "Why did the scarecrow win an award?", "punchline": "Because he was outstanding in his field!"}',
  }

  $: subtitle = $current_task ? "Task: " + $current_task.name : ""

  async function run_task() {
    try {
      submitting = true
      error = null
      response = null
      const client = createClient<paths>({
        baseUrl: "http://localhost:8757",
      })
      const {
        data, // only present if 2XX response
        error: fetch_error, // only present if 4XX or 5XX response
      } = await client.POST("/api/projects/{project_id}/task/{task_id}/run", {
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
        // TODO: check error message extraction
        throw new Error("Failed to run task: " + fetch_error)
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
      <div class="w-72 2xl:w-96 flex flex-col gap-4">
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
    {#if $current_task && !submitting && response != null && $current_project}
      {#if response.run != null}
        <div class="mt-10 xl:mt-32">
          <Run
            initial_run={response?.run}
            task={$current_task}
            project_id={$current_project.id}
          />
        </div>
      {:else if response?.raw_output}
        <!-- The response.run object may be nil if the run isn't saved (env var option for this). We still want to show the output though. -->
        <div class="text-xl font-bold mt-10 mb-4">Run Output</div>
        <Output
          structured={!!$current_task?.output_json_schema}
          raw_output={response.raw_output}
        />
      {/if}
    {/if}
  </div>
</AppPage>

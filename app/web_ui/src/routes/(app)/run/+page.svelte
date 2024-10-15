<script lang="ts">
  import AppPage from "../app_page.svelte"
  import { current_task, current_project } from "$lib/stores"
  import type { RunOutput, RunResponse } from "$lib/stores"
  import { createKilnError } from "$lib/utils/error_handlers"
  import FormContainer from "$lib/utils/form_container.svelte"
  import FormElement from "$lib/utils/form_element.svelte"
  import { KilnError } from "$lib/utils/error_handlers"
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
  let response: RunResponse | null = {
    run: {
      id: "123",
    },
    output: {
      plaintext_output: "",
      structured_output: { a: 1, b: "asdf" },
    },
  }
  $: output = response?.output

  $: subtitle = $current_task ? "Task: " + $current_task.name : ""

  async function run_task() {
    try {
      submitting = true
      error = null
      response = null
      const fetch_response = await fetch(
        `http://localhost:8757/api/projects/${$current_project?.id}/task/${$current_task?.id}/run`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model_name: model_name,
            provider: provider,
            plaintext_input: plaintext_input,
          }),
        },
      )
      const data = await fetch_response.json()
      // Check if data conforms to RunResponse type
      if (isRunResponse(data)) {
        response = data
      } else {
        throw new Error("Invalid response format")
      }
    } catch (e) {
      error = createKilnError(e)
    } finally {
      submitting = false
    }
  }

  function isRunResponse(data: unknown): data is RunResponse {
    return (
      typeof data === "object" &&
      data !== null &&
      "run" in data &&
      "output" in data &&
      isRunOutput(data.output)
    )
  }

  // Add this type guard function
  function isRunOutput(data: unknown): data is RunOutput {
    // Implement the type check based on RunOutput structure
    // This is a basic example, adjust according to your RunOutput type
    return (
      typeof data === "object" &&
      data !== null &&
      (("plaintext_output" in data &&
        typeof data.plaintext_output === "string") ||
        ("structured_output" in data &&
          typeof data.structured_output === "object"))
    )
  }
</script>

<AppPage title="Run" bind:subtitle>
  <div class="flex flex-col gap-2 w-full max-w-[800px]">
    <FormContainer
      submit_label="Run"
      on:submit={run_task}
      bind:warn_before_unload
      bind:error
      bind:submitting
    >
      <div class="flex flex-row gap-2 items-center">
        <div class="text-xl font-bold">Inputs</div>
        <div class="grow"></div>
        <FormElement
          label="Prompt Method"
          inputType="select"
          bind:value={prompt_method}
          id="prompt_method"
          select_options={[
            ["basic", "Basic Prompt (Zero Shot)"],
            ["few_shot", "Few Shot (include a few examples)"],
            ["many_shot", "Multi Shot (include many examples)"],
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
      <FormElement
        label="Plaintext Input"
        inputType="textarea"
        bind:value={plaintext_input}
        id="plaintext_input"
      />
    </FormContainer>
  </div>
  <div
    class="mt-10 max-w-[1400px] {submitting || output == null ? 'hidden' : ''}"
  >
    <Output {response} json_schema={$current_task?.output_json_schema} />
  </div>
</AppPage>

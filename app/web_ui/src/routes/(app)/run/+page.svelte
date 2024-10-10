<script lang="ts">
  import AppPage from "../app_page.svelte"
  import { current_task, current_project } from "$lib/stores"
  import { createKilnError } from "$lib/utils/error_handlers"
  import FormContainer from "$lib/utils/form_container.svelte"
  import FormElement from "$lib/utils/form_element.svelte"
  import { KilnError } from "$lib/utils/error_handlers"

  // TODO: implement checking input content
  let warn_before_unload = false
  // TODO UI for errors
  let error: KilnError | null = null
  let submitting = false

  // TODO: also structured input
  let plaintext_input = ""

  // TODO: real values for adapters and models
  let prompt_method = "basic"
  let model = "gpt_4o"
  let provider = "openrouter"

  // TODO structured output and UI
  let output = ""

  $: subtitle = $current_task?.name ?? ""

  async function run_task() {
    try {
      submitting = true
      const response = await fetch(
        `http://localhost:8757/api/projects/${$current_project?.id}/task/${$current_task?.id}/run`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model_name: model,
            provider: provider,
            plaintext_input: plaintext_input,
          }),
        },
      )
      const data = await response.json()
      console.log(data)
      output = JSON.stringify(data, null, 2) // Pretty-print the output
    } catch (e) {
      error = createKilnError(e)
    }
    submitting = false
  }
</script>

<AppPage title="Run Task" bind:subtitle>
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
          select_options={[
            ["gpt_4o", "GPT-4o"],
            ["gpt_4o-mini", "GPT-4o-Mini"],
          ]}
        />
      </div>
      <FormElement
        label="Plaintext Input"
        bind:value={plaintext_input}
        id="plaintext_input"
      />
    </FormContainer>
  </div>
  <div class="mt-10">
    <div class="text-xl font-bold">Outputs</div>
    <div class="text-xl font-bold">{output}</div>
  </div>
</AppPage>

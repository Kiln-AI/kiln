<script lang="ts">
  import type { Task, TaskRequirement, RunResponse } from "$lib/stores"
  import { current_task } from "$lib/stores"
  import FormContainer from "$lib/utils/form_container.svelte"
  import FormElement from "$lib/utils/form_element.svelte"
  import Rating from "./rating.svelte"
  export let json_schema: string | null = null
  let repair_instructions: string | null = null

  export let response: RunResponse | null = null
  $: output = response?.output
  $: output_valid =
    output &&
    ((json_schema && output.structured_output) ||
      (!json_schema && output.plaintext_output))
  // TODO warn_before_onload

  let overall_rating: 1 | 2 | 3 | 4 | 5 | null = null
  let requirement_ratings: (1 | 2 | 3 | 4 | 5 | null)[] = []
  let prior_task: Task | null = null

  current_task.subscribe((task) => {
    if (task) {
      let original_ratings = requirement_ratings
      requirement_ratings = []
      for (const requirement of task.requirements) {
        // Look up prior rating, if any
        let prior_index = prior_task?.requirements.findIndex(
          (req: TaskRequirement) => req.id === requirement.id,
        )
        let value =
          prior_index && prior_index >= 0 ? original_ratings[prior_index] : null
        requirement_ratings.push(value)
      }
      prior_task = task
    }
  })

  function save_ratings() {
    console.log("Overall rating", overall_rating)
    $current_task?.requirements.forEach((req, index) => {
      console.log("Requirement", req.name, requirement_ratings[index])
    })
  }

  function attempt_repair() {
    console.log("Attempting repair")
  }
</script>

<div>
  {#if output && !output_valid}
    <div class="text-xl font-bold">Output Invalid</div>
    <p class="mt-2 mb-4">The output is not in the correct format.</p>
    <pre class="bg-base-200 p-4 rounded-lg">{JSON.stringify(
        output,
        null,
        2,
      )}</pre>
  {:else if output}
    <div class="flex flex-col xl:flex-row gap-8">
      <div class="grow">
        <div class="text-xl font-bold mb-1">Outputs</div>
        {#if json_schema && output.structured_output}
          <div class="text-xs font-medium text-gray-500 flex flex-row">
            <svg
              fill="currentColor"
              class="w-4 h-4 mr-[2px]"
              viewBox="0 0 56 56"
              xmlns="http://www.w3.org/2000/svg"
              ><path
                d="M 27.9999 51.9063 C 41.0546 51.9063 51.9063 41.0781 51.9063 28 C 51.9063 14.9453 41.0312 4.0937 27.9765 4.0937 C 14.8983 4.0937 4.0937 14.9453 4.0937 28 C 4.0937 41.0781 14.9218 51.9063 27.9999 51.9063 Z M 24.7655 40.0234 C 23.9687 40.0234 23.3593 39.6719 22.6796 38.8750 L 15.9296 30.5312 C 15.5780 30.0859 15.3671 29.5234 15.3671 29.0078 C 15.3671 27.9063 16.2343 27.0625 17.2655 27.0625 C 17.9452 27.0625 18.5077 27.3203 19.0702 28.0469 L 24.6718 35.2890 L 35.5702 17.8281 C 36.0155 17.1016 36.6249 16.75 37.2343 16.75 C 38.2655 16.75 39.2733 17.4297 39.2733 18.5547 C 39.2733 19.0703 38.9687 19.6328 38.6640 20.1016 L 26.7577 38.8750 C 26.2421 39.6484 25.5858 40.0234 24.7655 40.0234 Z"
              /></svg
            >
            Structure Valid
          </div>
          <pre
            class="mt-3 bg-base-200 p-4 rounded-lg whitespace-pre-wrap break-words">{JSON.stringify(
              output.structured_output,
              null,
              2,
            )}</pre>
        {:else if !json_schema && output.plaintext_output}
          <pre
            class="mt-4 bg-base-200 p-4 rounded-lg whitespace-pre-wrap break-words">{output.plaintext_output}</pre>
        {:else}
          Unexpected output type
        {/if}
      </div>

      <div>
        <div class="text-xl font-bold mt-10 lg:mt-0 mb-6">Output Rating</div>
        <div class="grid grid-cols-[auto,1fr] gap-4">
          <div class="font-medium flex items-center text-nowrap">
            Overall Rating:
          </div>
          <div class="flex items-center">
            <Rating bind:rating={overall_rating} size={7} />
          </div>
          {#if $current_task?.requirements}
            {#each $current_task.requirements as requirement, index}
              <div class="flex items-center">
                {requirement.name}:
              </div>
              <div class="flex items-center">
                <Rating bind:rating={requirement_ratings[index]} size={6} />
              </div>
            {/each}
          {/if}
        </div>
        <button class="mt-4 link" on:click={save_ratings}>Save Ratings</button>
      </div>
    </div>

    <div class="text-xl font-bold mt-10 mb-4">Repair Output</div>
    {#if overall_rating === 5}
      <p>Repair not needed.</p>
      <p class="pt-1 text-sm">
        If the response can be improved, reduce the overall rating to 4-stars or
        lower.
      </p>
    {:else if overall_rating == null}
      <p>You must set an overall rating before repairing.</p>
    {:else}
      <FormContainer submit_label="Attempt Repair" on:submit={attempt_repair}>
        <FormElement
          id="repair_instructions"
          label="Repair Instructions"
          inputType="textarea"
          bind:value={repair_instructions}
        />
      </FormContainer>
    {/if}
  {/if}
</div>

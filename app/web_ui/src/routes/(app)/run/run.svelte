<script lang="ts">
  import type { Task } from "$lib/stores"
  import FormContainer from "$lib/utils/form_container.svelte"
  import FormElement from "$lib/utils/form_element.svelte"
  import Rating from "./rating.svelte"
  let repair_instructions: string | null = null
  import createClient from "openapi-fetch"
  import { type components, type paths } from "$lib/api_schema.d"

  export let project_id: string
  export let task: Task
  export let initial_run: components["schemas"]["TaskRun"]
  let updated_run: components["schemas"]["TaskRun"] | null = null
  $: run = updated_run || initial_run
  $: formatted_output = task.output_json_schema
    ? JSON.stringify(JSON.parse(run.output.output), null, 2)
    : run.output.output

  // TODO warn_before_unload

  // TODO: we aren't loading existing ratings from the server
  let overall_rating: 1 | 2 | 3 | 4 | 5 | null = null
  let requirement_ratings: (1 | 2 | 3 | 4 | 5 | null)[] = Array(
    task.requirements.length,
  ).fill(null)

  async function save_ratings() {
    try {
      let requirement_ratings_obj: Record<string, 1 | 2 | 3 | 4 | 5 | null> = {}
      task.requirements.forEach((req, index) => {
        requirement_ratings_obj[req.id] = requirement_ratings[index]
      })
      let patch_body = {
        output: {
          rating: {
            value: overall_rating,
            type: "five_star",
            requirement_ratings: requirement_ratings_obj,
          },
        },
      }
      const client = createClient<paths>({
        baseUrl: "http://localhost:8757",
      })
      const {
        data, // only present if 2XX response
        error: fetch_error, // only present if 4XX or 5XX response
      } = await client.PATCH(
        "/api/projects/{project_id}/task/{task_id}/run/{run_id}",
        {
          params: {
            path: {
              project_id: project_id,
              task_id: task.id || "",
              run_id: run?.id || "",
            },
          },
          // @ts-expect-error type checking and PATCH don't mix
          body: patch_body,
        },
      )
      if (fetch_error) {
        // TODO: check error message extraction
        throw new Error("Failed to run task: " + fetch_error)
      }
      updated_run = data
    } catch (err) {
      // TODO: better error handling
      console.error("Failed to save ratings", err)
    }
  }

  function attempt_repair() {
    console.log("Attempting repair")
  }

  // Watch for changes to ratings and save them if they change
  let prior_overall_rating: 1 | 2 | 3 | 4 | 5 | null = overall_rating
  let prior_requirement_ratings: (1 | 2 | 3 | 4 | 5 | null)[] =
    requirement_ratings
  $: {
    if (
      overall_rating !== prior_overall_rating ||
      !areArraysEqual(requirement_ratings, prior_requirement_ratings)
    ) {
      save_ratings()
    }
    prior_overall_rating = overall_rating
    prior_requirement_ratings = [...requirement_ratings]
  }

  function areArraysEqual(arr1: unknown[], arr2: unknown[]): boolean {
    if (arr1.length !== arr2.length) return false
    return arr1.every((value, index) => value === arr2[index])
  }
</script>

<div>
  <div class="flex flex-col xl:flex-row gap-8">
    <div class="grow">
      <div class="text-xl font-bold mb-1">Outputs</div>
      {#if task.output_json_schema}
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
      {/if}
      <pre
        class="mt-3 bg-base-200 p-4 rounded-lg whitespace-pre-wrap break-words">{formatted_output}</pre>
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
        {#if task.requirements}
          {#each task.requirements as requirement, index}
            <div class="flex items-center">
              {requirement.name}:
            </div>
            <div class="flex items-center">
              <Rating bind:rating={requirement_ratings[index]} size={6} />
            </div>
          {/each}
        {/if}
      </div>
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

  <h1>Raw Data</h1>
  <pre>{JSON.stringify(run, null, 2)}</pre>
</div>

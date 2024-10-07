<script lang="ts">
  import { goto } from "$app/navigation"
  import { current_project } from "$lib/stores"
  import FormContainer from "$lib/utils/form_container.svelte"
  import FormElement from "$lib/utils/form_element.svelte"

  export let created = false
  // Prevents flash of complete UI if we're going to redirect
  export let redirect_on_created: string | null = null
  export let project_name = ""
  export let project_description = ""
  let custom_error_message: string | null = null
  let submitting = false

  $: warn_before_unload = [project_name, project_description].some(
    (value) => !!value,
  )

  const create_project = async () => {
    try {
      custom_error_message = null
      const response = await fetch("http://localhost:8757/api/project", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: project_name,
          description: project_description,
        }),
      })
      const data = await response.json()
      if (response.status !== 200) {
        throw new Error(
          data["message"] || "Unknown error (status: " + response.status + ")",
        )
      }
      if (data["path"]) {
        current_project.set(data["path"])
      } else {
        throw new Error("Project created, but failed to return location.")
      }
      custom_error_message = null
      if (redirect_on_created) {
        goto(redirect_on_created)
      }
      created = true
    } catch (error) {
      if (
        error instanceof Error &&
        error.message === "The string did not match the expected pattern."
      ) {
        custom_error_message = "Unexpected response from server"
      } else {
        custom_error_message =
          error instanceof Error ? error.message : "Unknown error"
      }
    } finally {
      submitting = false
    }
  }
</script>

<div class="flex flex-col gap-2 w-full max-w-400 sm:w-[400px] mx-auto">
  {#if !created}
    <FormContainer
      submit_label="Create Project"
      on:submit={create_project}
      bind:warn_before_unload
      bind:submitting
      bind:custom_error_message
    >
      <FormElement
        label="Project Name"
        id="project_name"
        inputType="input"
        bind:value={project_name}
      />
      <FormElement
        label="Project Description"
        id="project_description"
        inputType="textarea"
        optional={true}
        bind:value={project_description}
      />
    </FormContainer>
  {:else if !redirect_on_created}
    <h2 class="text-xl font-medium text-center">Project Created!</h2>
    <p class="text-sm text-center">
      Your new project "{project_name}" has been created.
    </p>
  {/if}
</div>

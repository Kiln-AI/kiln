<script lang="ts">
  import { goto } from "$app/navigation"
  import { load_projects } from "$lib/stores"
  import FormContainer from "$lib/utils/form_container.svelte"
  import FormElement from "$lib/utils/form_element.svelte"
  import { KilnError, createKilnError } from "$lib/utils/error_handlers"
  import { client } from "$lib/api_client"

  export let created = false
  // Prevents flash of complete UI if we're going to redirect
  export let redirect_on_created: string | null = null
  export let project_name = ""
  export let project_description = ""
  let error: KilnError | null = null
  let submitting = false

  $: warn_before_unload = [project_name, project_description].some(
    (value) => !!value,
  )

  function redirect_to_project(project_id: string) {
    goto(redirect_on_created + `?project_id=${encodeURIComponent(project_id)}`)
  }

  const create_project = async () => {
    try {
      const { data, error: post_error } = await client.POST("/api/project", {
        body: {
          v: 1,
          name: project_name,
          description: project_description,
        },
      })
      if (post_error) {
        throw post_error
      }

      // now reload the projects, which should fetch the new project as current_project
      await load_projects()
      error = null
      if (redirect_on_created && data?.id) {
        redirect_to_project(data.id)
        return
      }
      created = true
    } catch (e) {
      error = createKilnError(e)
    } finally {
      submitting = false
    }
  }

  let importing = false
  let import_project_path = ""

  const import_project = async () => {
    try {
      submitting = true
      const { data, error: post_error } = await client.POST(
        "/api/import_project",
        {
          params: {
            query: {
              project_path: import_project_path,
            },
          },
        },
      )
      if (post_error) {
        throw post_error
      }

      await load_projects()
      if (redirect_on_created && data?.id) {
        redirect_to_project(data.id)
        return
      }
      created = true
    } catch (e) {
      error = createKilnError(e)
    } finally {
      submitting = false
    }
  }
</script>

<div class="flex flex-col gap-2 w-full">
  {#if !created}
    {#if !importing}
      <FormContainer
        submit_label="Create Project"
        on:submit={create_project}
        bind:warn_before_unload
        bind:submitting
        bind:error
      >
        <FormElement
          label="Project Name"
          id="project_name"
          inputType="input"
          bind:value={project_name}
          max_length={120}
        />
        <FormElement
          label="Project Description"
          id="project_description"
          inputType="textarea"
          optional={true}
          bind:value={project_description}
        />
      </FormContainer>
      <p class="mt-4 text-center">
        Or
        <button class="link font-bold" on:click={() => (importing = true)}>
          import an existing project
        </button>
      </p>
    {:else}
      <FormContainer
        submit_label="Import Project"
        on:submit={import_project}
        bind:warn_before_unload
        bind:submitting
        bind:error
      >
        <FormElement
          label="Existing Project Path"
          description="The path to the project on your local machine. For example, /Users/username/Kiln Projects/my_project/project.json"
          id="import_project_path"
          inputType="input"
          bind:value={import_project_path}
        />
      </FormContainer>
      <p class="mt-4 text-center">
        Or
        <button class="link font-bold" on:click={() => (importing = false)}>
          create a new project
        </button>
      </p>
    {/if}
  {:else if !redirect_on_created}
    {#if importing}
      <h2 class="text-xl font-medium text-center">Project Imported!</h2>
      <p class="text-sm text-center">
        Your project "{import_project_path}" has been imported.
      </p>
    {:else}
      <h2 class="text-xl font-medium text-center">Project Created!</h2>
      <p class="text-sm text-center">
        Your new project "{project_name}" has been created.
      </p>
    {/if}
  {/if}
</div>

<script lang="ts">
  import { onMount } from "svelte"
  import { browser } from "$app/environment"
  import { createEventDispatcher } from "svelte"
  import { KilnError } from "./error_handlers"

  const id = "form_container_" + Math.random().toString(36)

  export let submit_label: string = "Submit"
  export let warn_before_unload: boolean = false
  export let error: KilnError | null = null
  export let submitting = false

  async function focus_field(field: string) {
    // Async as the forms validation is also trying to set focus and we want to win
    await new Promise((resolve) => setTimeout(resolve, 10))
    const input = document.getElementById(field)
    if (input) {
      input.focus()
    }
  }

  async function trigger_validation() {
    const form = document.getElementById(id)
    if (form) {
      const formElements = form.querySelectorAll("input, textarea, select")
      await formElements.forEach(async (element) => {
        if (element instanceof HTMLElement) {
          // The input events are monitored by the form validation
          const inputEvent = new Event("input", {
            bubbles: true,
            cancelable: true,
          })
          await element.dispatchEvent(inputEvent)
        }
      })
    }
  }

  function first_error() {
    if (!browser) return null
    const form = document.getElementById(id)
    if (form) {
      const errorElement = form.querySelector(".input-error, .textarea-error")
      if (errorElement instanceof HTMLElement) {
        return errorElement
      }
    }
    return null
  }

  let has_validation_errors = false

  function focus_first_error() {
    const firstError = first_error()
    if (firstError) {
      focus_field(firstError.id)
    }
    has_validation_errors = firstError !== null
  }

  const dispatch = createEventDispatcher()

  async function validate_and_submit() {
    await trigger_validation()
    const firstError = first_error()
    if (firstError) {
      has_validation_errors = true
      focus_field(firstError.id)
    } else {
      has_validation_errors = false
      // No errors, submit. The wrapper should handle the event
      submitting = true
      dispatch("submit")
    }
  }

  onMount(() => {
    // focus first form element
    const form = document.getElementById(id)
    if (form) {
      const firstInput = form.querySelector("input, textarea, select")
      if (firstInput && firstInput instanceof HTMLElement) {
        firstInput.focus()
      }
    }

    // Prevent losing data on refresh/navigation, without confirmation
    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload)
    }
  })
  function handleBeforeUnload(event: BeforeUnloadEvent) {
    // the wrapper should bind something to warn_before_unload
    if (warn_before_unload) {
      event.preventDefault()
    }
  }
</script>

<form class="flex flex-col gap-6 w-full" {id}>
  <slot />

  <div class="flex flex-col gap-2 mt-4">
    {#if has_validation_errors}
      <div class="text-sm text-center text-error">
        <button class="link" on:click={() => focus_first_error()}
          >Please correct the errors above</button
        >
      </div>
    {/if}
    {#if error}
      {#each error.getErrorMessages() as error_line}
        <div class="text-sm text-center text-error">
          {error_line}
        </div>
      {/each}
    {/if}
    <button
      type="submit"
      class="btn btn-primary"
      on:click={validate_and_submit}
      disabled={submitting}
    >
      {#if !submitting}
        {submit_label}
      {:else}
        <span class="loading loading-spinner loading-md"></span>
      {/if}
    </button>
  </div>
</form>

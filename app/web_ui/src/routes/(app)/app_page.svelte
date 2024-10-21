<script lang="ts">
  import { goto } from "$app/navigation"

  export let title: string = ""
  export let subtitle: string = ""
  export let sub_subtitle: string = ""

  export let action_button: string | null = null
  export let action_button_href: string | null = null
  export let action_button_action: (() => void) | null = null

  function run_action_button() {
    if (action_button_action) {
      action_button_action()
    } else if (action_button_href) {
      goto(action_button_href)
    }
  }
</script>

<div class="flex flex-row">
  <div class="flex flex-col grow">
    <h1 class="text-2xl font-bold">{title}</h1>
    {#if subtitle}
      <p class="text-lg mt-2">{subtitle}</p>
    {/if}
    {#if sub_subtitle}
      <p class="text-sm text-gray-500 mt-1">{sub_subtitle}</p>
    {/if}
  </div>
  {#if action_button}
    <div>
      <button on:click={run_action_button} class="btn px-6">
        {action_button}
      </button>
    </div>
  {/if}
</div>

<div class="mt-8 mb-12">
  <slot />
</div>

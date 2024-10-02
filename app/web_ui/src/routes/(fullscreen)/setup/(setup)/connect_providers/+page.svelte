<script lang="ts">
  import ConnectProviders from "./connect_providers.svelte"
  import { getContext } from "svelte"
  import { type Writable } from "svelte/store"

  const step_number = getContext("setup_step_number") as Writable<number>
  step_number.set(1)

  const next_enabled = getContext("setup_next_enabled") as Writable<boolean>
  const next_visible = getContext("setup_next_visible") as Writable<boolean>
  let has_connected_providers = false
  let intermediate_step = false
  $: {
    next_enabled.set(has_connected_providers)
    next_visible.set(!intermediate_step)
  }
</script>

<ConnectProviders bind:has_connected_providers bind:intermediate_step />

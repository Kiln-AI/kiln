<script lang="ts">
  import AppPage from "../app_page.svelte"
  import { current_task } from "$lib/stores"

  $: subtitle = $current_task?.name ?? ""
</script>

<svelte:head>
  <title>Kiln Studio</title>
  <meta name="description" content="The open source ML product platform" />
</svelte:head>

<AppPage title="Run Task" bind:subtitle />

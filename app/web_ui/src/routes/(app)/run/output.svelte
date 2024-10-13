<script lang="ts">
  import type { RunOutput } from "$lib/stores"
  export let output: RunOutput | null
  export let json_schema: string | null = null
</script>

<div>
  {#if output == null}
    <div>No output</div>
  {:else if json_schema && output.structured_output}
    <pre>{JSON.stringify(output.structured_output, null, 2)}</pre>
  {:else if !json_schema && output.plaintext_output}
    <pre>{output.plaintext_output}</pre>
  {:else}
    Unexpected output type
  {/if}
</div>

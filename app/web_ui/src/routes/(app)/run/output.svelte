<script lang="ts">
  export let raw_output: string
  export let structured: boolean = false
  $: formatted_output = raw_output
    ? structured
      ? JSON.stringify(JSON.parse(raw_output), null, 2)
      : raw_output
    : "No valid output. Content was: " + raw_output
</script>

<pre
  class="bg-base-200 p-4 rounded-lg whitespace-pre-wrap break-words">{formatted_output}</pre>

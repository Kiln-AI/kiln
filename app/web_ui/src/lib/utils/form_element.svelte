<script lang="ts">
  export let inputType: "input" | "textarea" | "select" = "input"
  export let id: string
  export let label: string
  export let value: unknown
  export let description: string = ""
  export let optional: boolean = false
  export let error_message: string | null = null // start null because they haven't had a chance to edit it yet
  export let light_label: boolean = false // styling
  export let select_options: [unknown, string][] = []
  export let select_options_grouped: [string, [unknown, string][]][] = []

  // Export to let parent redefine this. This is a basic "Optional" check
  export let validator: (value: unknown) => string | null = () => {
    if (optional) {
      return null
    }
    if (!value) {
      return '"' + label + '" is required'
    }
    return null
  }

  function run_validator() {
    const error = validator(value)
    error_message = error
  }
</script>

<div>
  <label
    for={id}
    class="text-sm font-medium text-left flex flex-col gap-1 pb-[4px]"
  >
    <div class="flex flex-row">
      <span class="grow {light_label ? 'text-xs text-gray-500' : ''}"
        >{label}</span
      >
      <span class="pl-1 text-xs text-gray-500 flex-none"
        >{optional ? "Optional" : ""}</span
      >
    </div>
    {#if description}
      <div class="text-xs text-gray-500">
        {description}
      </div>
    {/if}
  </label>
  {#if inputType === "textarea"}
    <textarea
      placeholder={error_message || label}
      {id}
      class="textarea text-base textarea-bordered w-full h-18 wrap-pre text-left align-top
       {error_message ? 'textarea-error' : ''}"
      bind:value
      on:input={run_validator}
      autocomplete="off"
    />
  {:else if inputType === "input"}
    <input
      type="text"
      placeholder={error_message || label}
      {id}
      class="input text-base input-bordered w-full font-base {error_message
        ? 'input-error'
        : ''}"
      bind:value
      on:input={run_validator}
      autocomplete="off"
    />
  {:else if inputType === "select"}
    <select {id} class="select select-bordered" bind:value>
      {#if select_options_grouped.length > 0}
        {#each select_options_grouped as group}
          <optgroup label={group[0]}>
            {#each group[1] as option}
              <option value={option[0]} selected={option[0] === value}
                >{option[1]}</option
              >
            {/each}
          </optgroup>
        {/each}
      {:else}
        {#each select_options as option}
          <option value={option[0]} selected={option[0] === value}
            >{option[1]}</option
          >
        {/each}
      {/if}
    </select>
  {/if}
</div>

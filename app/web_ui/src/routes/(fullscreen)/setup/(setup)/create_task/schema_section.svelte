<script lang="ts">
  import JsonSchemaFormElement from "$lib/utils/json_schema_editor/json_schema_form_element.svelte"
  import type { SchemaModel } from "$lib/utils/json_schema_editor/json_schema_templates"
  import { empty_schema_model } from "$lib/utils/json_schema_editor/json_schema_templates"

  export let schema_model: SchemaModel = empty_schema_model
  export let plaintext: boolean = true
  let id = Math.random().toString(36)
</script>

<div>
  <div class="form-control">
    <label class="label cursor-pointer flex flex-row gap-3">
      <input
        type="radio"
        name="radio-input-schema"
        class="radio"
        value={true}
        bind:group={plaintext}
      />
      <span class="label-text text-left grow">Plaintext</span>
    </label>
  </div>
  <div class="form-control">
    <label class="label cursor-pointer flex flex-row gap-3">
      <input
        type="radio"
        name="radio-input-schema-{id}"
        class="radio"
        value={false}
        bind:group={plaintext}
      />
      <span class="label-text text-left grow">Structured Schema (JSON)</span>
    </label>
  </div>

  {#if !plaintext}
    <JsonSchemaFormElement {schema_model} />
  {/if}
</div>

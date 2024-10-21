<script lang="ts">
  import JsonSchemaFormElement from "$lib/utils/json_schema_editor/json_schema_form_element.svelte"
  import {
    type SchemaModel,
    model_from_schema,
    schema_from_model,
  } from "$lib/utils/json_schema_editor/json_schema_templates"
  import { example_schema_model } from "$lib/utils/json_schema_editor/json_schema_templates"

  let id = Math.random().toString(36)

  export let schema_string: string | null = null

  // Our "viewModel" - this file only exposes the schema string, but keeps a live VM up to date both ways.
  // Initial load is string -> Model. We updatee it if the string is set from extrernal.
  // Later it's Model -> String from the accessor below. Not live because sub-item reactivity is not easy
  let schema_model: SchemaModel = schema_model_from_string(schema_string)
  $: schema_model = schema_model_from_string(schema_string)
  let plaintext: boolean = !schema_string
  $: plaintext = !schema_string

  // Update our live VM from the schema string
  function schema_model_from_string(
    new_schema_string: string | null,
  ): SchemaModel {
    if (new_schema_string) {
      return model_from_schema(JSON.parse(new_schema_string))
    } else {
      return example_schema_model()
    }
  }

  export function get_schema_string(): string | null {
    if (plaintext) {
      return null
    } else {
      return JSON.stringify(schema_from_model(schema_model))
    }
  }
</script>

<div>
  <div class="form-control">
    <label class="label cursor-pointer flex flex-row gap-3">
      <input
        type="radio"
        name="radio-input-schema-{id}"
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

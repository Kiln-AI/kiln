<script lang="ts">
  import {
    empty_schema_model,
    schema_from_model,
  } from "./json_schema_templates"
  import type { SchemaModel } from "./json_schema_templates"
  import FormElement from "../form_element.svelte"

  let validation_errors: string[] = []

  export let schema_model: SchemaModel = empty_schema_model

  $: schema_preview = schema_from_model(schema_model)
  $: model_json = JSON.stringify(schema_model, null, 2)
  $: schema_json = JSON.stringify(schema_preview, null, 2)
  $: console.log("model_json", model_json)
  $: console.log("schema_json", schema_json)
</script>

<code class="font-mono whitespace-pre text-xs">
  model: {model_json}
</code>
<code class="font-mono whitespace-pre text-xs">
  schema: {schema_json}
</code>

{#if validation_errors.length > 0}
  <div class="validation-errors">
    {#each validation_errors as error}
      <div class="text-error">{error}</div>
    {/each}
  </div>
{:else}
  <div class="flex flex-col gap-6">
    {#each schema_model.properties as property, index}
      {#if property}
        <!-- ignore we don't use this var-->
      {/if}
      <div class="flex flex-col gap-2">
        <div class="font-medium text-sm">
          Property #{index + 1}
        </div>
        <div class="flex flex-row gap-3">
          <div class="grow">
            <FormElement
              id={"property_{name}_title"}
              label="Property Name"
              inputType="input"
              bind:value={schema_model.properties[index].title}
              light_label={true}
            />
          </div>
          <FormElement
            id={"property_{name}_type"}
            label="Type"
            inputType="select"
            bind:value={schema_model.properties[index].type}
            select_options={[
              ["string", "String"],
              ["number", "Number"],
              ["integer", "Integer"],
              ["boolean", "Boolean"],
            ]}
            light_label={true}
          />
          <FormElement
            id={"property_{name}_required"}
            label="Required"
            inputType="select"
            bind:value={schema_model.properties[index].required}
            select_options={[
              [true, "True"],
              [false, "False"],
            ]}
            light_label={true}
          />
        </div>
        <FormElement
          id={"property_{name}_description"}
          label="Description"
          inputType="input"
          bind:value={schema_model.properties[index].description}
          light_label={true}
        />
      </div>
    {/each}
  </div>
{/if}

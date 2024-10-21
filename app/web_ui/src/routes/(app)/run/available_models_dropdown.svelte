<script lang="ts">
  import {
    available_models,
    load_available_models,
    ui_state,
  } from "$lib/stores"
  import type { AvailableModels } from "$lib/types"
  import { onMount } from "svelte"
  import FormElement from "$lib/utils/form_element.svelte"

  export let model: string = $ui_state.selected_model
  $: $ui_state.selected_model = model
  $: model_options = format_model_options($available_models || {})

  onMount(async () => {
    await load_available_models()
  })

  function format_model_options(
    providers: AvailableModels[],
  ): [string, [unknown, string][]][] {
    let options = []
    for (const provider of providers) {
      let model_list = []
      for (const model of provider.models) {
        let id = provider.provider_id + "/" + model.id
        model_list.push([id, model.name])
      }
      options.push([provider.provider_name, model_list])
    }
    // @ts-expect-error this is the correct format, but TS isn't finding it
    return options
  }
</script>

<FormElement
  label="Model"
  bind:value={model}
  id="model"
  inputType="select"
  select_options_grouped={model_options}
/>

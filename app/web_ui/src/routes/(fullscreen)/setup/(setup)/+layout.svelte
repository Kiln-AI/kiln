<script lang="ts">
  import { writable } from "svelte/store"
  import { setContext } from "svelte"
  const step_number = writable(1)
  setContext("setup_step_number", step_number)
  const next_enabled = writable(false)
  setContext("setup_next_enabled", next_enabled)

  const steps = [
    {
      title: "Welcome",
      link: "/setup",
      description: "",
    },
    {
      title: "Connect AI Providers",
      link: "/setup/create_project",
      description:
        "Kiln is free, but your need to connect API keys to use AI services.",
    },
    {
      title: "Create Project",
      link: "/",
      description: "Create a project. You can always create more later!",
    },
  ]

  $: next_link = steps[$step_number].link
  $: step_title = steps[$step_number].title
  $: step_description = steps[$step_number].description
</script>

<div class="min-h-screen p-4 flex flex-col">
  <div class="grow"></div>
  <div class="flex-none flex flex-row items-center justify-center">
    <img src="/logo.svg" alt="logo" class="size-8 mb-3" />
  </div>
  <h1 class="text-2xl lg:text-4xl ml-4 flex-none font-bold text-center">
    {step_title}
  </h1>
  <h3 class="text-base font-medium text-center mt-3 max-w-[600px] mx-auto">
    {step_description}
  </h3>

  <div class="flex-none min-h-[50vh] py-8">
    <slot />
  </div>

  <div class="flex-none flex flex-col place-content-center md:flex-row gap-4">
    <div class="md:grow">
      <ul class="steps steps-horizontal w-full max-w-[500px] hidden">
        <!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
        {#each steps as step, index}
          <li
            class="step relative {index <= $step_number ? 'step-primary' : ''}"
            data-content={index === $step_number ? "●" : ""}
          ></li>
        {/each}
      </ul>
    </div>
    <a
      href={$next_enabled ? next_link : "#"}
      class="flex-none {$next_enabled ? '' : 'cursor-default'}"
    >
      <button
        class="btn btn-primary w-full min-w-[130px]"
        disabled={!$next_enabled}
      >
        Next
      </button>
    </a>
  </div>
  <div class="grow-[1.5]"></div>
</div>

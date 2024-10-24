<script lang="ts">
  import AppPage from "../app_page.svelte"
  import { ui_state } from "$lib/stores"

  let sections = [
    {
      name: "Providers",
      description: "Connect to AI providers like OpenAI, Google, or Ollama.",
      href: "/settings/providers",
      button_text: "Providers",
    },
    {
      name: "Projects",
      description: "Add, remove or edit projects.",
      href: "/settings/manage_projects",
      button_text: "All Projects",
    },
    {
      name: "Current Project",
      description: "Edit the currently selected project.",
      button_text: "Edit Project",
      href: "/settings/edit_project/" + $ui_state.current_project_id,
    },
    {
      name: "Current Task",
      description: "Edit the currently selected task.",
      button_text: "Edit Task",
      href: `/settings/edit_task/${$ui_state?.current_project_id}/${$ui_state?.current_task_id}`,
    },
    {
      name: "Replay Introduction",
      description: "Watch the introduction again.",
      href: "/settings/intro",
      button_text: "Introduction",
    },
  ]
</script>

<AppPage title="Settings">
  <div class="flex flex-col gap-8 max-w-[700px] mt-16">
    {#each sections as section}
      <div class="flex flex-col md:flex-row gap-4 md:items-center">
        <div class="grow">
          <h3 class="font-medium">{section.name}</h3>
          <p class="text-sm text-gray-500">{section.description}</p>
        </div>
        <a href={section.href} class="btn" style="min-width: 14rem">
          {section.button_text}
        </a>
      </div>
    {/each}
  </div>
</AppPage>

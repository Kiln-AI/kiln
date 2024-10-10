<script lang="ts">
  import AppPage from "../app_page.svelte"
  import EditProject from "../../(fullscreen)/setup/(setup)/create_project/edit_project.svelte"
</script>

<div class="max-w-[600px]">
  <AppPage
    title="New Project"
    subtitle="Projects are a collection of tasks and other resources. They are the ideal way to organize your work."
  >
    <EditProject redirect_on_created="/create_task" />
  </AppPage>
</div>

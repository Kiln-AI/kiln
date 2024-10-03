<script lang="ts">
  import NewProject from "./new_project.svelte"
</script>

<div class="grow"></div>
<div class="flex-none flex flex-row items-center justify-center">
  <img src="/logo.svg" alt="logo" class="size-8 mb-3" />
</div>
<h1 class="text-2xl lg:text-4xl flex-none font-bold text-center">
  Create a Project
</h1>
<h3 class="text-base font-medium text-center mt-3 max-w-[600px] mx-auto">
  You can always create more later!
</h3>

<div class="flex-none min-h-[50vh] py-8 px-4 h-full flex flex-col pt-24">
  <NewProject redirect_on_created="/" />
</div>

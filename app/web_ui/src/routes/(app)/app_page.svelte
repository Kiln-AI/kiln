<script lang="ts">
  export let title: string = ""
  export let subtitle: string = ""
  export let sub_subtitle: string = ""
</script>

<div class="flex flex-col">
  <h1 class="text-2xl font-bold">{title}</h1>
  {#if subtitle}
    <p class="text-lg mt-2">{subtitle}</p>
  {/if}
  {#if sub_subtitle}
    <p class="text-sm text-gray-500 mt-1">{sub_subtitle}</p>
  {/if}
</div>

<div class="mt-8">
  <slot />
</div>

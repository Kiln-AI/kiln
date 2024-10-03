<script lang="ts">
  import "../app.css"
  import { navigating } from "$app/stores"
  import { expoOut } from "svelte/easing"
  import { slide } from "svelte/transition"
  import { onMount } from "svelte"
  import { goto } from "$app/navigation"
  import { page } from "$app/stores"

  const check_needs_setup = async () => {
    if ($page.url.pathname.startsWith("/setup")) {
      // We're already on a setup page, no need to redirect
      return
    }

    try {
      let res = await fetch("http://localhost:8757/api/settings")
      let data = await res.json()
      let projects = data["projects"]

      if (!projects || projects.length === 0) {
        goto("/setup")
      }
    } catch (e) {
      console.error("check_needs_setup error", e)
    }
  }

  onMount(() => {
    // Check if we need setup (async okay)
    check_needs_setup()
  })
</script>

{#if $navigating}
  <!--
    Loading animation for next page since svelte doesn't show any indicator.
     - delay 100ms because most page loads are instant, and we don't want to flash
     - long 12s duration because we don't actually know how long it will take
     - exponential easing so fast loads (>100ms and <1s) still see enough progress,
       while slow networks see it moving for a full 12 seconds
  -->
  <div
    class="fixed w-full top-0 right-0 left-0 h-1 z-50 bg-primary"
    in:slide={{ delay: 100, duration: 12000, axis: "x", easing: expoOut }}
  ></div>
{/if}
<slot />

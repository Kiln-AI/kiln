<script>
  import "../app.css"
  import { page } from "$app/stores"
</script>

<div class="hero min-h-[100vh]">
  <div class="hero-content text-center">
    <div class="max-w-lg">
      <h1 class="text-5xl font-bold">This is embarrassing...</h1>
      <p class="py-6 text-2xl">There was an error: {$page?.error?.message}</p>
      <div>
        <a href="/" class="btn btn-primary btn-wide">Return Home</a>
      </div>
    </div>
  </div>
</div>

<script lang="ts">
  export let rating: number | null = null
  let hover_rating: number | null = null
  let id = Math.random().toString(36)
  export let size: number = 8

  $: visual_rating = hover_rating ? hover_rating : rating

  function rating_clicked(new_rating: number) {
    // click current to remove rating
    if (new_rating === rating) {
      rating = null
      return
    }
    rating = new_rating
  }
</script>

<div class="rating" {id}>
  <!-- For the compiler so our sizes aren't compiled away -->
  <p class="hidden h-5 w-5 h-6 w-6 h-7 w-7 h-8 w-8"></p>
  <input
    type="radio"
    name="rating-{id}"
    class="rating-hidden"
    checked={visual_rating === null}
    value={null}
    bind:group={rating}
  />
  {#each [1, 2, 3, 4, 5] as r}
    <input
      type="radio"
      name="rating-{id}"
      class="mask mask-star-2 w-{size} h-{size}"
      checked={visual_rating === r}
      on:mouseover={() => (hover_rating = r)}
      on:focus={() => (hover_rating = r)}
      on:mouseleave={() => (hover_rating = null)}
      on:blur={() => (hover_rating = null)}
      on:click={() => rating_clicked(r)}
      value={r}
      bind:group={rating}
    />
  {/each}
</div>

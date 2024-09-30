<script>
  import "../../app.css"
</script>

<div class="drawer lg:drawer-open">
  <input id="main-drawer" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content flex flex-col lg:mx-4 min-h-screen">
    <div class="flex-none h-12">
      <div class="flex flex-row h-full items-center">
        <label for="main-drawer" class="drawer-button lg:hidden">
          <svg
            class="size-6 mx-3"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
          >
            <path
              fill="currentColor"
              fill-rule="evenodd"
              d="M19 4a1 1 0 01-1 1H2a1 1 0 010-2h16a1 1 0 011 1zm0 6a1 1 0 01-1 1H2a1 1 0 110-2h16a1 1 0 011 1zm-1 7a1 1 0 100-2H2a1 1 0 100 2h16z"
            />
          </svg>
        </label>
        <div class="flex-grow">Home</div>
      </div>
    </div>

    <div class="flex-grow rounded-t-lg bg-base-100 shadow-lg">
      <slot />
    </div>
  </div>
  <div class="drawer-side">
    <label for="my-drawer-2" aria-label="close sidebar" class="drawer-overlay"
    ></label>

    <div class="flex flex-row items-center mx-6 my-3 hidden lg:flex">
      <img src="/logo.svg" alt="logo" class="w-8 h-8" />
      <div class="text-lg font-bold ml-1">Kiln AI</div>
    </div>
    <ul class="menu bg-base-200 text-base-content min-h-full w-60 p-4">
      <li><a>Sidebar Item 1</a></li>
      <li><a>Sidebar Item 2</a></li>
    </ul>
  </div>
</div>

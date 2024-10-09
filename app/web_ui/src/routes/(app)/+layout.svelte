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
        <div class="flex-grow"></div>
      </div>
    </div>

    <div class="flex-grow rounded-t-lg bg-base-100 shadow-lg p-4">
      <slot />
    </div>
  </div>
  <div class="drawer-side">
    <label for="main-drawer" aria-label="close sidebar" class="drawer-overlay"
    ></label>

    <ul
      class="menu bg-base-200 text-base-content min-h-full w-72 lg:w-60 xl:w-72 p-4 pt-1 lg:pt-4"
    >
      <li class="hover:bg-transparent flex flex-row justify-end">
        <label
          for="main-drawer"
          class="lg:hidden ml-3 text-2xl cursor-pointer ml-4 pt-[5px]"
        >
          &#x2715;
        </label>
      </li>
      <li class="mb-4">
        <a href="https://kiln-ai.com" target="_blank">
          <div class="flex flex-row items-center mx-[-5px] p-0">
            <img src="/logo.svg" alt="logo" class="w-8 h-8" />
            <div class="text-lg font-bold ml-1">Kiln AI</div>
          </div>
        </a>
      </li>
      <li><a href="/?1">Sidebar Item 1</a></li>
      <li><a href="/?2">Sidebar Item 2</a></li>
    </ul>
  </div>
</div>

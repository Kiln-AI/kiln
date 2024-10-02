<script lang="ts">
  import { fade } from "svelte/transition"
  import { onMount } from "svelte"

  const providers = [
    {
      name: "OpenRouter.ai",
      description:
        "The easiest way to use Kiln. Proxies requests to OpenAI, Anthropic, Google, and more. Works with almost any model.",
      image: "/images/openrouter.svg",
      featured: true,
    },
    {
      name: "OpenAI",
      description: "The OG home to GPT-4 and more.",
      image: "/images/openai.svg",
      featured: false,
    },
    {
      name: "Ollama",
      description: "Run models locally. No API key required.",
      image: "/images/ollama.svg",
      featured: false,
    },
    {
      name: "Groq",
      description:
        "The fastest model host. Providing Llama, Gemma and Mistral models.",
      image: "/images/groq.svg",
      featured: false,
    },
    {
      name: "Amazon Bedrock",
      description: "So your company has an AWS contract?",
      image: "/images/aws.svg",
      featured: false,
    },
  ]

  type ProviderStatus = {
    connected: boolean
    error: string | null
    custom_description: string | null
    connecting: boolean
  }
  let status: { [key: string]: ProviderStatus } = {
    Ollama: {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
    OpenAI: {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
    "OpenRouter.ai": {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
    Groq: {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
    "Amazon Bedrock": {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
  }

  export let has_connected_providers = false

  const connect_provider = (provider: (typeof providers)[number]) => {
    if (status[provider.name].connected) {
      return
    }
    if (provider.name === "Ollama") {
      connect_ollama()
    }
  }

  const connect_ollama = async (user_initated: boolean = true) => {
    status.Ollama.connecting = user_initated
    let data: { message: string | null; models: [] | null }
    let res: Response
    try {
      res = await fetch("http://localhost:8757/provider/ollama/connect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      })
      data = await res.json()
    } catch (e) {
      status.Ollama.error = "Failed to connect. Ensure Ollama app is running."
      return
    } finally {
      status.Ollama.connecting = false
    }
    if (!res || res.status !== 200 || !data) {
      status.Ollama.error = data.message || "Failed to connect to Ollama"
      return
    }
    if (!data.models || data.models.length === 0) {
      status.Ollama.error = "Ollama running, but no models available"
      return
    }
    status.Ollama.connected = true
    status.Ollama.custom_description =
      "Ollama connected. The following supported models are available: " +
      data.models.join(", ") +
      "."
    has_connected_providers = true
  }

  onMount(() => {
    connect_ollama(false).then(() => {
      // Clear the error as the user didn't initiate this run
      status["Ollama"].error = null
    })
  })
</script>

<div class="flex flex-col gap-6 max-w-lg mx-auto">
  {#each providers as provider}
    <div class="flex flex-row gap-4 items-center">
      <img
        src={provider.image}
        alt={provider.name}
        class="flex-none p-1 {provider.featured ? 'size-12' : 'size-10 mx-1'}"
      />
      <div class="flex flex-col grow pr-4">
        <h3
          class={provider.featured
            ? "text-large font-bold"
            : "text-base font-medium"}
        >
          {provider.name}
          {#if provider.featured}
            <div class="badge ml-2 badge-secondary text-xs font-medium">
              Recommended
            </div>
          {/if}
        </h3>
        {#if status[provider.name] && status[provider.name].error}
          <p class="text-sm text-error" transition:fade>
            {status[provider.name].error}
          </p>
        {:else}
          <p class="text-sm text-gray-500">
            {status[provider.name].custom_description || provider.description}
          </p>
        {/if}
      </div>
      <button
        class="btn md:min-w-[100px]"
        on:click={() => connect_provider(provider)}
      >
        {#if status[provider.name] && status[provider.name].connected}
          <img src="/images/circle-check.svg" class="size-6" alt="Connected" />
        {:else if status[provider.name] && status[provider.name].connecting}
          <div class="loading loading-spinner loading-md"></div>
        {:else}
          Connect
        {/if}
      </button>
    </div>
  {/each}
</div>

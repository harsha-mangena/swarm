<template>
  <div class="p-8 space-y-8 bg-bg-primary">
    <div>
      <h1 class="text-2xl font-semibold mb-2 text-text-primary">Settings</h1>
      <p class="text-text-secondary">Configure API keys and system settings</p>
    </div>

    <!-- API Keys Section -->
    <div class="bg-bg-secondary border border-border rounded-lg p-6">
      <h2 class="text-lg font-semibold mb-4 text-text-primary">API Keys</h2>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium mb-2 text-text-primary">Anthropic API Key</label>
          <input
            v-model="apiKeys.anthropic"
            type="password"
            placeholder="sk-ant-..."
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-2 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-2 text-text-primary">Google API Key</label>
          <input
            v-model="apiKeys.google"
            type="password"
            placeholder="AIza..."
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-2 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-2 text-text-primary">OpenAI API Key</label>
          <input
            v-model="apiKeys.openai"
            type="password"
            placeholder="sk-..."
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-2 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-2 text-text-primary">OpenRouter API Key</label>
          <input
            v-model="apiKeys.openrouter"
            type="password"
            placeholder="sk-or-..."
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-2 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-2 text-text-primary">Tavily API Key</label>
          <input
            v-model="apiKeys.tavily"
            type="password"
            placeholder="tvly-..."
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-2 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-2 text-text-primary">Brave API Key</label>
          <input
            v-model="apiKeys.brave"
            type="password"
            placeholder="BSA..."
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-2 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
          />
        </div>
        <button
          @click="saveApiKeys"
          class="bg-accent text-bg-primary px-6 py-2 rounded-lg font-medium hover:bg-accent-hover transition-colors"
        >
          Save API Keys
        </button>
      </div>
    </div>

    <!-- Link to LLMs Page -->
    <div class="bg-bg-secondary border border-border rounded-lg p-6">
      <h2 class="text-lg font-semibold mb-4 text-text-primary">LLM Providers & Models</h2>
      <p class="text-text-secondary mb-4">
        View available providers and their models on the LLMs page.
      </p>
      <router-link
        to="/llms"
        class="inline-flex items-center gap-2 bg-accent text-bg-primary px-4 py-2 rounded-lg text-sm font-medium hover:bg-accent-hover transition-colors"
      >
        View LLMs
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
        </svg>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const apiKeys = ref({
  anthropic: '',
  google: '',
  openai: '',
  openrouter: '',
  tavily: '',
  brave: '',
})

const loadApiKeys = () => {
  // Load from localStorage
  const stored = localStorage.getItem('apiKeys')
  if (stored) {
    apiKeys.value = JSON.parse(stored)
  }
}

const saveApiKeys = () => {
  localStorage.setItem('apiKeys', JSON.stringify(apiKeys.value))
  alert('API keys saved locally. Note: These are stored in browser localStorage only.')
}

onMounted(() => {
  loadApiKeys()
})
</script>


<template>
  <div class="p-8 space-y-8 bg-bg-primary">
    <div>
      <h1 class="text-2xl font-semibold mb-2 text-text-primary">LLM Providers & Models</h1>
      <p class="text-text-secondary">View available providers and their models</p>
    </div>

    <!-- Providers & Models Section -->
    <div class="bg-bg-secondary border border-border rounded-lg p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-semibold text-text-primary">Available Providers</h2>
        <button
          @click="refreshProviders"
          :disabled="loading"
          class="border border-border px-4 py-2 rounded-lg text-sm hover:bg-bg-tertiary transition-colors text-text-primary disabled:opacity-50"
        >
          <span v-if="!loading">Refresh</span>
          <span v-else class="inline-flex items-center gap-2">
            <span class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
            Loading...
          </span>
        </button>
      </div>

      <div v-if="loading && Object.keys(providers).length === 0" class="text-center py-12">
        <span class="inline-flex items-center gap-2 text-text-secondary">
          <span class="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
          Loading providers...
        </span>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="(provider, name) in providers"
          :key="name"
          class="border border-border rounded-lg p-4 bg-bg-tertiary"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <h3 class="font-semibold text-text-primary capitalize text-lg">{{ name }}</h3>
              <span
                class="px-2 py-1 rounded text-xs font-medium"
                :class="provider.available ? 'bg-accent text-bg-primary' : 'bg-bg-secondary text-text-tertiary'"
              >
                {{ provider.available ? 'Available' : 'Unavailable' }}
              </span>
              <span class="text-xs text-text-tertiary">
                {{ provider.type || 'cloud' }}
              </span>
            </div>
          </div>

          <div v-if="provider.models && provider.models.length > 0" class="mt-4">
            <h4 class="text-sm font-medium text-text-secondary mb-2">Available Models:</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              <div
                v-for="model in provider.models"
                :key="model"
                class="bg-bg-secondary border border-border rounded px-3 py-2 text-sm text-text-primary"
              >
                {{ model }}
              </div>
            </div>
          </div>
          <div v-else class="mt-4 text-sm text-text-tertiary">
            No models available
          </div>

          <div v-if="provider.error" class="mt-3 text-xs text-text-tertiary bg-bg-secondary border border-border rounded px-3 py-2">
            <span class="font-medium">Error:</span> {{ provider.error }}
          </div>
          <div v-if="provider.reason" class="mt-2 text-xs text-text-tertiary">
            <span class="font-medium">Reason:</span> {{ provider.reason }}
          </div>
        </div>

        <div v-if="Object.keys(providers).length === 0" class="text-center py-12 text-text-tertiary">
          No providers configured. Configure API keys in Settings.
        </div>
      </div>
    </div>

    <!-- Provider Info -->
    <div class="bg-bg-secondary border border-border rounded-lg p-6">
      <h2 class="text-lg font-semibold mb-4 text-text-primary">Provider Information</h2>
      <div class="space-y-3 text-sm text-text-secondary">
        <div>
          <span class="font-medium text-text-primary">Ollama:</span> Local LLM server. Install from <a href="https://ollama.ai" target="_blank" class="text-accent hover:underline">ollama.ai</a>
        </div>
        <div>
          <span class="font-medium text-text-primary">Anthropic (Claude):</span> Requires API key from <a href="https://console.anthropic.com" target="_blank" class="text-accent hover:underline">console.anthropic.com</a>
        </div>
        <div>
          <span class="font-medium text-text-primary">Google (Gemini):</span> Requires API key from <a href="https://aistudio.google.com" target="_blank" class="text-accent hover:underline">aistudio.google.com</a>
        </div>
        <div>
          <span class="font-medium text-text-primary">OpenAI:</span> Requires API key from <a href="https://platform.openai.com" target="_blank" class="text-accent hover:underline">platform.openai.com</a>
        </div>
        <div>
          <span class="font-medium text-text-primary">OpenRouter:</span> Unified API for multiple providers. Get key from <a href="https://openrouter.ai" target="_blank" class="text-accent hover:underline">openrouter.ai</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../services/api'

const providers = ref({})
const loading = ref(false)

const loadProviders = async () => {
  loading.value = true
  try {
    const status = await api.getProviderStatus()
    providers.value = status.providers || {}
  } catch (error) {
    console.error('Failed to load providers:', error)
    providers.value = {}
  } finally {
    loading.value = false
  }
}

const refreshProviders = () => {
  loadProviders()
}

onMounted(() => {
  loadProviders()
})
</script>


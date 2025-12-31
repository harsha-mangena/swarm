<template>
  <div class="p-8 space-y-8 bg-bg-primary">
    <div>
      <h1 class="text-2xl font-semibold mb-2 text-text-primary">Settings</h1>
      <p class="text-text-secondary">Configure API keys, model preferences, and system settings</p>
    </div>

    <!-- Model Preferences Section -->
    <div class="bg-bg-secondary border border-border rounded-lg p-6">
      <h2 class="text-lg font-semibold mb-4 text-text-primary">Model Preferences</h2>
      <p class="text-text-secondary text-sm mb-4">
        Enter the model name to use for each provider. The model name will be used directly with the API.
      </p>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium mb-2 text-text-primary">Google (Gemini)</label>
          <input
            v-model="modelSettings.google_model"
            type="text"
            placeholder="e.g., gemini/gemini-2.0-flash-exp"
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-2 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
          />
          <p class="text-text-tertiary text-xs mt-1">Format: gemini/model-name</p>
        </div>
        <div>
          <label class="block text-sm font-medium mb-2 text-text-primary">Anthropic (Claude)</label>
          <input
            v-model="modelSettings.anthropic_model"
            type="text"
            placeholder="e.g., claude-3-5-sonnet-20241022"
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-2 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
          />
          <p class="text-text-tertiary text-xs mt-1">Format: model-name (no prefix needed)</p>
        </div>
        <div>
          <label class="block text-sm font-medium mb-2 text-text-primary">OpenAI</label>
          <input
            v-model="modelSettings.openai_model"
            type="text"
            placeholder="e.g., gpt-4o"
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-2 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
          />
          <p class="text-text-tertiary text-xs mt-1">Format: model-name (no prefix needed)</p>
        </div>
        <div>
          <label class="block text-sm font-medium mb-2 text-text-primary">OpenRouter</label>
          <input
            v-model="modelSettings.openrouter_model"
            type="text"
            placeholder="e.g., openrouter/anthropic/claude-3-sonnet"
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-2 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
          />
          <p class="text-text-tertiary text-xs mt-1">Format: openrouter/provider/model-name</p>
        </div>
        <div class="flex items-center gap-4">
          <button
            @click="saveModelSettings"
            :disabled="savingModels"
            class="bg-accent text-bg-primary px-6 py-2 rounded-lg font-medium hover:bg-accent-hover transition-colors disabled:opacity-50"
          >
            {{ savingModels ? 'Saving...' : 'Save Model Preferences' }}
          </button>
          <span v-if="modelSaveSuccess" class="text-green-500 text-sm">✓ Saved successfully</span>
        </div>
      </div>
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

const modelSettings = ref({
  google_model: 'gemini/gemini-1.5-flash',
  anthropic_model: 'claude-3-5-sonnet-20241022',
  openai_model: 'gpt-4o',
  openrouter_model: 'openrouter/anthropic/claude-3-sonnet',
})

const savingModels = ref(false)
const modelSaveSuccess = ref(false)

const loadApiKeys = () => {
  const stored = localStorage.getItem('apiKeys')
  if (stored) {
    apiKeys.value = JSON.parse(stored)
  }
}

const saveApiKeys = () => {
  localStorage.setItem('apiKeys', JSON.stringify(apiKeys.value))
  alert('API keys saved locally. Note: These are stored in browser localStorage only.')
}

const loadModelSettings = async () => {
  try {
    const response = await fetch('/api/settings')
    if (response.ok) {
      const data = await response.json()
      modelSettings.value = data
    }
  } catch (error) {
    console.error('Failed to load model settings:', error)
  }
}

const saveModelSettings = async () => {
  savingModels.value = true
  modelSaveSuccess.value = false
  
  try {
    const response = await fetch('/api/settings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(modelSettings.value),
    })
    
    if (response.ok) {
      modelSaveSuccess.value = true
      setTimeout(() => {
        modelSaveSuccess.value = false
      }, 3000)
    } else {
      alert('Failed to save model settings')
    }
  } catch (error) {
    console.error('Failed to save model settings:', error)
    alert('Failed to save model settings: ' + error.message)
  } finally {
    savingModels.value = false
  }
}

onMounted(async () => {
  loadApiKeys()
  await loadModelSettings()
})
</script>


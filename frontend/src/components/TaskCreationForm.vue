<template>
  <div class="bg-bg-secondary rounded-xl border border-border p-6">
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <label class="block text-sm font-medium mb-2">Task Description</label>
        <textarea 
          v-model="form.description"
          rows="3"
          placeholder="Describe what you want to accomplish..."
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-3 
                 text-text-primary placeholder-text-tertiary
                 focus:outline-none focus:border-accent
                 resize-none"
          required
        ></textarea>
      </div>
      
      <div class="flex items-center gap-4">
        <!-- Provider Selection -->
        <div class="flex-1">
          <label class="block text-sm font-medium mb-2">Provider</label>
          <select
            v-model="form.provider"
            class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-2.5 text-text-primary
                   hover:border-accent focus:outline-none focus:border-accent"
          >
            <option value="auto">Auto (Recommended)</option>
            <option value="ollama">Ollama</option>
            <option value="claude">Claude</option>
            <option value="gemini">Gemini</option>
            <option value="openai">OpenAI</option>
          </select>
        </div>
        
        <!-- Submit -->
        <div class="pt-7">
          <button 
            type="submit"
            :disabled="loading"
            class="bg-accent text-bg-primary px-6 py-2.5 rounded-lg
                   font-medium transition-colors flex items-center gap-2 disabled:opacity-50 hover:bg-accent-hover"
          >
            <svg v-if="!loading" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            <span v-else class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            Create Task
          </button>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '../services/api'

const emit = defineEmits(['task-created'])

const form = ref({
  description: '',
  provider: 'auto',
  auto_execute: true,
})

const loading = ref(false)

const handleSubmit = async () => {
  loading.value = true
  try {
    const task = await api.createTask(form.value)
    emit('task-created', task)
    form.value.description = ''
  } catch (error) {
    console.error('Failed to create task:', error)
    alert('Failed to create task. Please try again.')
  } finally {
    loading.value = false
  }
}
</script>


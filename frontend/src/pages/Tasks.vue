<template>
  <div class="h-[calc(100vh-3.5rem)] flex bg-bg-primary overflow-hidden">
    
    <!-- Sidebar: Prev Tasks -->
    <aside class="w-64 border-r border-border bg-bg-secondary flex flex-col">
      <div class="p-4 border-b border-border">
        <h2 class="font-medium text-text-primary">Prev tasks</h2>
      </div>
      <div class="flex-1 overflow-y-auto p-2 space-y-1">
        <div v-if="recentTasks.length === 0" class="text-xs text-text-tertiary text-center py-4">
          No tasks yet
        </div>
        <div
          v-for="task in recentTasks"
          :key="task.id"
          @click="viewTask(task.id)"
          class="group p-3 rounded-lg hover:bg-bg-tertiary cursor-pointer transition-colors border border-transparent hover:border-border"
        >
          <div class="font-medium text-sm text-text-primary truncate mb-1">
            {{ task.description }}
          </div>
          <div class="flex items-center justify-between text-xs text-text-tertiary">
            <span>{{ formatDate(task.created_at) }}</span>
            <span :class="getStatusColor(task.status)">{{ task.status }}</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col items-center justify-center p-8 relative">
      <!-- Create Task Card -->
      <div class="w-full max-w-2xl bg-bg-secondary border border-border rounded-xl shadow-lg p-8 relative z-10">
        <h1 class="text-2xl font-light text-text-primary mb-6">Create task</h1>
        
        <div class="space-y-6">
          <!-- Text Input -->
          <textarea
            v-model="query"
            placeholder="Describe your task..."
            rows="3"
            class="w-full bg-transparent text-xl text-text-primary placeholder-text-tertiary focus:outline-none resize-none"
            :disabled="loading"
          ></textarea>

          <!-- File Upload Preview -->
          <div v-if="uploadedFiles.length > 0" class="flex flex-wrap gap-2">
            <div
              v-for="(file, idx) in uploadedFiles"
              :key="idx"
              class="bg-bg-tertiary border border-border rounded-full px-3 py-1 text-xs flex items-center gap-2 group"
            >
              <span class="text-text-secondary max-w-[150px] truncate">{{ file.name }}</span>
              <button @click="removeFile(idx)" class="text-text-tertiary hover:text-text-primary">×</button>
            </div>
          </div>

          <!-- Controls Row -->
          <div class="flex items-center justify-between pt-4 border-t border-border">
            <div class="flex items-center gap-3">
              <!-- Upload Button -->
              <div class="relative">
                <input
                  type="file"
                  multiple
                  @change="handleFileSelect"
                  class="hidden"
                  ref="fileInput"
                />
                <button
                  @click="fileInput?.click()"
                  class="flex items-center gap-2 px-4 py-2 rounded-full border border-border hover:bg-bg-tertiary text-sm text-text-secondary transition-colors"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                  Upload Knowledge
                </button>
              </div>

              <!-- Provider Selector -->
              <div class="relative">
                <select
                  v-model="selectedProvider"
                  class="appearance-none bg-transparent pl-4 pr-10 py-2 rounded-full border border-border hover:bg-bg-tertiary text-sm text-text-secondary transition-colors cursor-pointer focus:outline-none"
                >
                  <option value="auto">Provider: Auto</option>
                  <option value="anthropic">Provider: Anthropic</option>
                  <option value="google">Provider: Google</option>
                  <option value="openai">Provider: OpenAI</option>
                </select>
                <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-text-tertiary">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                </div>
              </div>
            </div>

            <!-- Create Button -->
            <button
              @click="executeTask"
              :disabled="loading || !query.trim()"
              class="px-6 py-2 rounded-full bg-text-primary text-bg-primary font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
            >
              <span v-if="loading">Creating...</span>
              <span v-else>Create</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Example Tasks (Visual Only per sketch) -->
      <div class="absolute bottom-20 right-20 opacity-50 pointer-events-none">
        <svg width="200" height="100" viewBox="0 0 200 100" fill="none" class="text-border">
          <path d="M10 10 Q 100 50 180 80" stroke="currentColor" stroke-width="2" marker-end="url(#arrow)"/>
          <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
              <path d="M0,0 L0,6 L9,3 z" fill="currentColor" />
            </marker>
          </defs>
        </svg>
        <div class="absolute top-24 left-40 text-sm text-text-tertiary whitespace-nowrap">
          Example tasks
        </div>
      </div>

    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

const router = useRouter()
const fileInput = ref()
const uploadedFiles = ref([])
const query = ref('')
const selectedProvider = ref('auto')
const loading = ref(false)
const recentTasks = ref([])

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  files.forEach(file => {
    uploadedFiles.value.push(file)
  })
}

const removeFile = (index) => {
  uploadedFiles.value.splice(index, 1)
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return ''
  return date.toLocaleDateString()
}

const getStatusColor = (status) => {
  return status === 'completed' ? 'text-success' : 'text-text-tertiary'
}

const executeTask = async () => {
  if (!query.value.trim() || loading.value) return

  loading.value = true
  const currentQuery = query.value
  const currentFiles = [...uploadedFiles.value]
  
  query.value = ''
  uploadedFiles.value = []

  try {
    let fileInfo = []
    if (currentFiles.length > 0) {
      const uploadResult = await api.uploadFiles(currentFiles)
      fileInfo = uploadResult.files || []
    }

    let taskDescription = currentQuery
    if (fileInfo.length > 0) {
      taskDescription += `\n\nKnowledge Base Files:\n${fileInfo.map(f => `- ${f.filename}`).join('\n')}`
    }

    const task = await api.createTask({
      description: taskDescription,
      provider: selectedProvider.value,
      auto_execute: true,
      context: { files: fileInfo }
    })
    
    // Navigate to task detail immediately
    router.push(`/tasks/${task.id}`)
  } catch (error) {
    console.error('Task execution failed:', error)
    alert(`Error: ${error.message || 'Failed to execute task'}`)
    loading.value = false
  }
}

const viewTask = (taskId) => {
  router.push(`/tasks/${taskId}`)
}

const loadRecentTasks = async () => {
  try {
    const tasks = await api.getTasks({ limit: 20 })
    recentTasks.value = tasks || []
  } catch (error) {
    console.error('Failed to load recent tasks:', error)
  }
}

onMounted(() => {
  loadRecentTasks()
  setInterval(loadRecentTasks, 5000)
})
</script>

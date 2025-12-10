<template>
  <div class="p-8 space-y-6 bg-bg-primary">
    <h1 class="text-2xl font-semibold text-text-primary">Agents</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="agent in agents" 
        :key="agent.id"
        @click="() => $router.push(`/agents/${agent.id}`)"
        class="bg-bg-secondary rounded-xl border border-border p-6 cursor-pointer hover:border-accent transition-colors"
      >
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-medium text-text-primary">{{ agent.name }}</h3>
          <span 
            class="w-2 h-2 rounded-full"
            :class="statusClass(agent.status)"
          ></span>
        </div>
        <div class="space-y-2 text-sm text-text-secondary">
          <div>Type: {{ agent.agent_type }}</div>
          <div>Provider: {{ agent.provider }}</div>
          <div>Load: {{ (agent.current_load * 100).toFixed(0) }}%</div>
        </div>
      </div>
      
      <div v-if="agents.length === 0" class="col-span-full p-6 text-center text-text-tertiary">
        No agents available
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

const router = useRouter()

const agents = ref([])

const statusClass = (status) => {
  if (status === 'idle') return 'bg-accent'
  if (status === 'processing') return 'bg-accent'
  if (status === 'error') return 'bg-accent'
  return 'bg-text-tertiary'
}

const loadAgents = async () => {
  try {
    agents.value = await api.getAgents()
  } catch (error) {
    console.error('Failed to load agents:', error)
  }
}

onMounted(() => {
  loadAgents()
  // Refresh every 5 seconds
  setInterval(loadAgents, 5000)
})
</script>


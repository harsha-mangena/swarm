<template>
  <div class="p-8 space-y-6 bg-bg-primary">
    <!-- Page Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-text-primary">Dashboard</h1>
        <p class="text-text-secondary text-sm mt-1">Overview of tasks and agents</p>
      </div>
    </div>
    
    <!-- Stats Cards -->
    <StatsCards />
    
    <!-- Tasks and Agents Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Tasks -->
      <div class="bg-bg-secondary rounded-xl border border-border">
        <div class="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 class="font-medium text-text-primary">Recent Tasks</h2>
          <router-link to="/tasks" class="text-text-primary text-sm hover:underline">View all</router-link>
        </div>
        
        <div class="divide-y divide-border">
          <div
            v-for="task in recentTasks" 
            :key="task.id"
            @click="() => $router.push(`/tasks/${task.id}`)"
            class="p-4 cursor-pointer hover:bg-bg-tertiary transition-colors"
          >
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-medium text-text-primary truncate flex-1">{{ task.description }}</h3>
              <span
                class="ml-3 px-2 py-1 rounded text-xs font-medium"
                :class="getStatusClass(task.status)"
              >
                {{ task.status }}
              </span>
            </div>
            <div class="flex items-center gap-4 text-xs text-text-tertiary">
              <span>{{ formatDate(task.created_at) }}</span>
              <span v-if="task.agents_count > 0">{{ task.agents_count }} agent(s)</span>
            </div>
          </div>
          <div v-if="recentTasks.length === 0" class="p-6 text-center text-text-tertiary">
            No tasks yet
          </div>
        </div>
      </div>

      <!-- Active Agents -->
      <div class="bg-bg-secondary rounded-xl border border-border">
        <div class="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 class="font-medium text-text-primary">Active Agents</h2>
          <router-link to="/agents" class="text-text-primary text-sm hover:underline">View all</router-link>
        </div>
        
        <div class="divide-y divide-border">
          <div
            v-for="agent in activeAgents" 
            :key="agent.id"
            @click="() => $router.push(`/agents/${agent.id}`)"
            class="p-4 cursor-pointer hover:bg-bg-tertiary transition-colors"
          >
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-medium text-text-primary">{{ agent.name }}</h3>
              <span 
                class="w-2 h-2 rounded-full"
                :class="getStatusClass(agent.status)"
              ></span>
            </div>
            <div class="flex items-center gap-4 text-xs text-text-tertiary">
              <span>{{ agent.agent_type }}</span>
              <span>{{ agent.provider }}</span>
              <span>Load: {{ (agent.current_load * 100).toFixed(0) }}%</span>
            </div>
          </div>
          <div v-if="activeAgents.length === 0" class="p-6 text-center text-text-tertiary">
            No active agents
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import StatsCards from '../components/StatsCards.vue'
import { api } from '../services/api'

const router = useRouter()
const recentTasks = ref([])
const activeAgents = ref([])

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}

const getStatusClass = (status) => {
  if (typeof status === 'string') {
    const classes = {
      'pending': 'bg-bg-tertiary text-text-tertiary',
      'in_progress': 'bg-accent text-bg-primary',
      'debating': 'bg-accent text-bg-primary',
      'completed': 'bg-accent text-bg-primary',
      'failed': 'bg-bg-tertiary text-text-tertiary',
      'cancelled': 'bg-bg-tertiary text-text-tertiary',
      'idle': 'bg-bg-tertiary',
      'processing': 'bg-accent',
      'error': 'bg-bg-tertiary',
    }
    return classes[status] || classes.pending
  }
  return 'bg-bg-tertiary'
}

const loadRecentTasks = async () => {
  try {
    const tasks = await api.getTasks({ limit: 5 })
    recentTasks.value = tasks || []
  } catch (error) {
    console.error('Failed to load tasks:', error)
  }
}

const loadActiveAgents = async () => {
  try {
    const agents = await api.getAgents()
    activeAgents.value = agents.filter(a => a.status === 'processing' || a.status === 'idle').slice(0, 5)
  } catch (error) {
    console.error('Failed to load agents:', error)
  }
}

onMounted(() => {
  loadRecentTasks()
  loadActiveAgents()
  // Refresh every 5 seconds
  setInterval(() => {
    loadRecentTasks()
    loadActiveAgents()
  }, 5000)
})
</script>

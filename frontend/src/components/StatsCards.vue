<template>
  <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
    <div class="bg-bg-secondary rounded-lg border border-border p-4">
      <div class="text-sm text-text-tertiary">Total Tasks</div>
      <div class="text-2xl font-semibold mt-1 text-text-primary">{{ stats.total_tasks || 0 }}</div>
    </div>
    <div class="bg-bg-secondary rounded-lg border border-border p-4">
      <div class="text-sm text-text-tertiary">Active Tasks</div>
      <div class="text-2xl font-semibold mt-1 text-text-primary">{{ stats.active_tasks || 0 }}</div>
    </div>
    <div class="bg-bg-secondary rounded-lg border border-border p-4">
      <div class="text-sm text-text-tertiary">Completed</div>
      <div class="text-2xl font-semibold mt-1 text-text-primary">{{ stats.completed_tasks || 0 }}</div>
    </div>
    <div class="bg-bg-secondary rounded-lg border border-border p-4">
      <div class="text-sm text-text-tertiary">Total Tokens</div>
      <div class="text-2xl font-semibold mt-1 text-text-primary">{{ formattedTokens }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../services/api'

const stats = ref({
  total_tasks: 0,
  active_tasks: 0,
  completed_tasks: 0,
  total_tokens: 0,
})

const formattedTokens = computed(() => {
  return (stats.value.total_tokens || 0).toLocaleString()
})

const loadStats = async () => {
  try {
    stats.value = await api.getStats()
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

onMounted(() => {
  loadStats()
  // Refresh every 10 seconds
  setInterval(loadStats, 10000)
})
</script>


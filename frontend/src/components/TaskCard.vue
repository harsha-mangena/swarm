<template>
  <div class="hover:bg-bg-tertiary/50 transition-colors">
    <div class="flex items-start justify-between gap-4">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <!-- Status Badge -->
          <span 
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
            :class="statusClass"
          >
            <span 
              v-if="isActive" 
              class="w-1.5 h-1.5 rounded-full bg-current animate-pulse"
            ></span>
            {{ statusText }}
          </span>
          
          <!-- Provider Badge -->
          <span class="text-xs text-text-tertiary">
            {{ task.provider }}
          </span>
        </div>
        
        <h3 class="font-medium mt-2 truncate">
          {{ truncatedDescription }}
        </h3>
        
        <div class="flex items-center gap-4 mt-2 text-sm text-text-tertiary">
          <span>{{ task.agents_count }} agents</span>
          <span>{{ formattedDate }}</span>
          <span v-if="task.tokens_used">{{ task.tokens_used.toLocaleString() }} tokens</span>
        </div>
      </div>
      
      <router-link 
        :to="`/tasks/${task.id}`"
        class="p-2 rounded-lg hover:bg-bg-elevated text-text-secondary hover:text-text-primary"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
        </svg>
      </router-link>
    </div>
    
    <!-- Progress Bar -->
    <div v-if="isActive && task.progress" class="mt-3">
      <div class="h-1 bg-bg-tertiary rounded-full overflow-hidden">
        <div 
          class="h-full bg-accent transition-all duration-300"
          :style="{ width: `${task.progress}%` }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  task: {
    type: Object,
    required: true,
  },
})

const statusText = computed(() => {
  return props.task.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
})

const isActive = computed(() => {
  return ['in_progress', 'debating'].includes(props.task.status)
})

const statusClass = computed(() => {
  const status = props.task.status
  if (status === 'completed') return 'bg-accent/10 text-text-primary border border-accent/20'
  if (status === 'in_progress') return 'bg-accent/10 text-text-primary border border-accent/20'
  if (status === 'debating') return 'bg-accent/10 text-text-primary border border-accent/20'
  if (status === 'failed') return 'bg-accent/10 text-text-primary border border-accent/20'
  return 'bg-bg-tertiary text-text-tertiary border border-border'
})

const truncatedDescription = computed(() => {
  const desc = props.task.description
  return desc.length > 80 ? desc.substring(0, 80) + '...' : desc
})

const formattedDate = computed(() => {
  const date = new Date(props.task.created_at)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
})
</script>


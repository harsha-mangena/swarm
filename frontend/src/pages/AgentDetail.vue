<template>
  <div class="p-8 space-y-6 bg-bg-primary">
    <div class="flex items-center justify-between">
      <div>
        <button
          @click="$router.back()"
          class="text-text-secondary hover:text-text-primary mb-2 flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
          Back
        </button>
        <h1 class="text-2xl font-semibold text-text-primary">{{ agent.name || agent.agent_type }}</h1>
        <p class="text-text-secondary text-sm mt-1">Agent Details</p>
      </div>
      <span
        class="px-3 py-1 rounded text-sm font-medium"
        :class="getStatusClass(agent.status)"
      >
        {{ agent.status }}
      </span>
    </div>

    <!-- Agent Info Card -->
    <div class="bg-bg-secondary border border-border rounded-lg p-6">
      <h2 class="text-lg font-semibold mb-4 text-text-primary">Agent Information</h2>
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span class="text-text-tertiary">Type:</span>
          <span class="ml-2 text-text-primary font-medium">{{ agent.agent_type }}</span>
        </div>
        <div>
          <span class="text-text-tertiary">Provider:</span>
          <span class="ml-2 text-text-primary font-medium">{{ agent.provider }}</span>
        </div>
        <div>
          <span class="text-text-tertiary">Current Load:</span>
          <span class="ml-2 text-text-primary font-medium">{{ (agent.current_load * 100).toFixed(0) }}%</span>
        </div>
        <div>
          <span class="text-text-tertiary">Capabilities:</span>
          <span class="ml-2 text-text-primary font-medium">{{ agent.capabilities?.join(', ') || 'N/A' }}</span>
        </div>
      </div>
    </div>

    <!-- Agent Thinking/Work/Output -->
    <div class="space-y-4">
      <!-- Thinking Section -->
      <div class="bg-bg-secondary border border-border rounded-lg p-6">
        <h2 class="text-lg font-semibold mb-4 text-text-primary">Thinking Process</h2>
        <div v-if="agentThoughts.length === 0" class="text-text-tertiary text-sm">
          No thinking records available
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="(thought, idx) in agentThoughts"
            :key="idx"
            class="bg-bg-tertiary border border-border rounded p-4"
          >
            <div class="text-xs text-text-tertiary mb-2">{{ formatDate(thought.created_at || thought.timestamp) }}</div>
            <p class="text-text-primary whitespace-pre-wrap text-sm">{{ thought.content }}</p>
          </div>
        </div>
      </div>

      <!-- Work Section -->
      <div class="bg-bg-secondary border border-border rounded-lg p-6">
        <h2 class="text-lg font-semibold mb-4 text-text-primary">Work History</h2>
        <div v-if="agentWork.length === 0" class="text-text-tertiary text-sm">
          No work records available
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="(work, idx) in agentWork"
            :key="idx"
            class="bg-bg-tertiary border border-border rounded p-4"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-text-primary">{{ work.metadata?.task_id || work.namespace?.split(':')[1] || 'Unknown Task' }}</span>
              <span class="text-xs text-text-tertiary">{{ formatDate(work.created_at || work.timestamp) }}</span>
            </div>
            <p class="text-text-secondary text-sm">{{ work.metadata?.description || work.content }}</p>
            <div v-if="work.metadata?.tools_used" class="mt-2 flex flex-wrap gap-2">
              <span
                v-for="tool in work.metadata.tools_used"
                :key="tool"
                class="px-2 py-1 bg-bg-primary border border-border rounded text-xs text-text-secondary"
              >
                {{ tool }}
              </span>
            </div>
            <div v-else-if="work.tools_used" class="mt-2 flex flex-wrap gap-2">
              <span
                v-for="tool in work.tools_used"
                :key="tool"
                class="px-2 py-1 bg-bg-primary border border-border rounded text-xs text-text-secondary"
              >
                {{ tool }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Output Section -->
      <div class="bg-bg-secondary border border-border rounded-lg p-6">
        <h2 class="text-lg font-semibold mb-4 text-text-primary">Output</h2>
        <div v-if="agentOutput.length === 0" class="text-text-tertiary text-sm">
          No output records available
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="(output, idx) in agentOutput"
            :key="idx"
            class="bg-bg-tertiary border border-border rounded p-4"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-text-primary">Task: {{ output.metadata?.task_id || output.namespace?.split(':')[1] || 'Unknown' }}</span>
              <span class="text-xs text-text-tertiary">{{ formatDate(output.created_at || output.timestamp) }}</span>
            </div>
            <div class="text-text-primary whitespace-pre-wrap text-sm mb-2">{{ output.content }}</div>
            <div v-if="output.metadata?.confidence" class="text-xs text-text-tertiary">
              Confidence: {{ (output.metadata.confidence * 100).toFixed(0) }}%
            </div>
            <div v-if="output.metadata?.evidence && output.metadata.evidence.length > 0" class="mt-2">
              <div class="text-xs text-text-tertiary mb-1">Evidence:</div>
              <ul class="list-disc list-inside text-xs text-text-secondary space-y-1">
                <li v-for="(evidence, eIdx) in output.metadata.evidence" :key="eIdx">{{ evidence }}</li>
              </ul>
            </div>
            <div v-else-if="output.evidence && output.evidence.length > 0" class="mt-2">
              <div class="text-xs text-text-tertiary mb-1">Evidence:</div>
              <ul class="list-disc list-inside text-xs text-text-secondary space-y-1">
                <li v-for="(evidence, eIdx) in output.evidence" :key="eIdx">{{ evidence }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'

const route = useRoute()
const agent = ref({})
const agentThoughts = ref([])
const agentWork = ref([])
const agentOutput = ref([])

const formatDate = (dateString) => {
  if (!dateString) return 'Unknown'
  const date = new Date(dateString)
  return date.toLocaleString()
}

const getStatusClass = (status) => {
  const classes = {
    'idle': 'bg-bg-tertiary text-text-tertiary',
    'processing': 'bg-accent text-bg-primary',
    'error': 'bg-bg-tertiary text-text-tertiary',
  }
  return classes[status] || classes.idle
}

const loadAgentDetails = async () => {
  const agentId = route.params.id
  try {
    // Get agent info
    const agents = await api.getAgents()
    const foundAgent = agents.find(a => a.id === agentId)
    if (foundAgent) {
      agent.value = foundAgent
    }

    // Load agent memory/thoughts
    try {
      const memory = await api.getAgentMemory(agentId)
      if (Array.isArray(memory)) {
        // Categorize memory entries
        agentThoughts.value = memory.filter(m => 
          m.metadata?.type === 'thinking' || 
          m.metadata?.category === 'thinking' ||
          (m.scope === 'agent' && !m.metadata?.type && !m.metadata?.category)
        )
        agentWork.value = memory.filter(m => 
          m.metadata?.type === 'work' || 
          m.metadata?.category === 'work' ||
          (m.scope === 'task' && m.metadata?.type !== 'output')
        )
        agentOutput.value = memory.filter(m => 
          m.metadata?.type === 'output' || 
          m.metadata?.category === 'output' ||
          (m.scope === 'task' && m.metadata?.type === 'output')
        )
      }
    } catch (error) {
      console.error('Failed to load agent memory:', error)
      // Fallback: empty arrays
      agentThoughts.value = []
      agentWork.value = []
      agentOutput.value = []
    }
  } catch (error) {
    console.error('Failed to load agent details:', error)
  }
}

onMounted(() => {
  loadAgentDetails()
  // Refresh every 3 seconds
  setInterval(loadAgentDetails, 3000)
})
</script>


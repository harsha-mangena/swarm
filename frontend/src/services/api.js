import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // Tasks
  async createTask(data) {
    const response = await client.post('/tasks', data)
    return response.data
  },

  async getTasks(params = {}) {
    const response = await client.get('/tasks', { params })
    return response.data
  },

  async getTask(id) {
    const response = await client.get(`/tasks/${id}`)
    return response.data
  },

  async getTaskMemory(id, params = {}) {
    const response = await client.get(`/tasks/${id}/memory`, { params })
    return response.data
  },

  async getDebateState(id) {
    const response = await client.get(`/tasks/${id}/debate`)
    return response.data
  },

  async deleteTask(id) {
    const response = await client.delete(`/tasks/${id}`)
    return response.data
  },

  async getTaskSubtasks(id) {
    const response = await client.get(`/tasks/${id}/subtasks`)
    return response.data
  },

  async getTaskValidation(id) {
    const response = await client.get(`/tasks/${id}/validation`)
    return response.data
  },

  // Agents
  async getAgents() {
    const response = await client.get('/agents')
    return response.data
  },

  async getAgentStatus() {
    const response = await client.get('/agents/status')
    return response.data
  },

  // Providers
  async getProviderStatus() {
    const response = await client.get('/providers/status')
    return response.data
  },

  // Stats
  async getStats() {
    const response = await client.get('/stats')
    return response.data
  },

  // Status
  async getStatus() {
    const response = await client.get('/status')
    return response.data
  },

  // Files
  async uploadFiles(files) {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    const response = await client.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Agent Memory
  async getAgentMemory(agentId) {
    const response = await client.get(`/agents/${agentId}/memory`)
    return response.data
  },

  // Generic POST request (used by chat)
  async post(url, data) {
    const response = await client.post(url, data)
    return response
  },
}


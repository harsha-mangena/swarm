<template>
  <header class="border-b border-border sticky top-0 bg-bg-primary/80 backdrop-blur-sm z-50 h-14">
    <div class="max-w-full px-6 h-full flex items-center justify-between">
      <div class="flex items-center gap-8">
        <router-link to="/" class="text-lg font-semibold text-text-primary">SwarmOS</router-link>
        <nav class="flex items-center gap-6">
          <router-link
            to="/tasks"
            class="text-sm transition-colors py-1 px-2 rounded-md hover:bg-bg-tertiary"
            :class="isActive('/tasks') ? 'text-text-primary font-medium bg-bg-tertiary' : 'text-text-secondary'"
          >
            Tasks
          </router-link>
          <router-link
            to="/docs"
            class="text-sm transition-colors py-1 px-2 rounded-md hover:bg-bg-tertiary"
            :class="isActive('/docs') ? 'text-text-primary font-medium bg-bg-tertiary' : 'text-text-secondary'"
          >
            Docs
          </router-link>
          <router-link
            to="/settings"
            class="text-sm transition-colors py-1 px-2 rounded-md hover:bg-bg-tertiary"
            :class="isActive('/settings') ? 'text-text-primary font-medium bg-bg-tertiary' : 'text-text-secondary'"
          >
            Settings
          </router-link>
        </nav>
      </div>
      
      <div class="flex items-center gap-4">
        <ProviderBadge />
        <button 
          @click="toggleTheme"
          class="p-2 rounded-lg hover:bg-bg-tertiary text-text-primary transition-colors"
          :title="dark ? 'Switch to light mode' : 'Switch to dark mode'"
        >
          <svg v-if="dark" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0z"/>
          </svg>
          <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/>
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ProviderBadge from './ProviderBadge.vue'

const route = useRoute()
const dark = ref(true)

const isActive = (path) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

const toggleTheme = () => {
  dark.value = !dark.value
  document.documentElement.dataset.theme = dark.value ? 'dark' : 'light'
}

onMounted(() => {
  dark.value = document.documentElement.dataset.theme === 'dark'
})
</script>

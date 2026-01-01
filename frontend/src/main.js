import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

import Home from './pages/Home.vue'
import Tasks from './pages/Tasks.vue'
import TaskDetail from './pages/TaskDetail.vue'
import Agents from './pages/Agents.vue'
import AgentDetail from './pages/AgentDetail.vue'
import LLMs from './pages/LLMs.vue'
import Docs from './pages/Docs.vue'
import Settings from './pages/Settings.vue'
import Login from './pages/Login.vue'
import { getSession, isSupabaseConfigured } from './services/supabase'

const routes = [
  { path: '/', component: Home },
  { path: '/login', component: Login },
  { path: '/tasks', component: Tasks, meta: { requiresAuth: true } },
  { path: '/tasks/:id', component: TaskDetail, meta: { requiresAuth: true } },
  { path: '/agents', component: Agents },
  { path: '/agents/:id', component: AgentDetail },
  { path: '/llms', component: LLMs },
  { path: '/docs', component: Docs },
  { path: '/settings', component: Settings },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth guard - redirect to login if not authenticated
router.beforeEach(async (to, from, next) => {
  // Skip auth check if Supabase is not configured (dev mode)
  if (!isSupabaseConfigured()) {
    next()
    return
  }

  if (to.meta.requiresAuth) {
    const session = await getSession()
    if (!session) {
      next('/login')
      return
    }
  }

  // Redirect to tasks if already logged in and going to login
  if (to.path === '/login') {
    const session = await getSession()
    if (session) {
      next('/tasks')
      return
    }
  }

  next()
})

const app = createApp(App)
app.use(router)
app.mount('#app')


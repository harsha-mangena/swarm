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

const routes = [
  { path: '/', component: Home },
  { path: '/tasks', component: Tasks },
  { path: '/tasks/:id', component: TaskDetail },
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

const app = createApp(App)
app.use(router)
app.mount('#app')

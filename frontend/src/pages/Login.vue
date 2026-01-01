<template>
  <div class="min-h-screen bg-bg-primary flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Logo/Title -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-text-primary mb-2">SwarmOS</h1>
        <p class="text-text-secondary">Multi-Agent Task Orchestration</p>
      </div>

      <!-- Auth Card -->
      <div class="bg-bg-secondary border border-border rounded-2xl p-8 shadow-xl">
        <h2 class="text-xl font-semibold text-text-primary mb-6">
          {{ isSignUp ? 'Create Account' : 'Welcome Back' }}
        </h2>

        <!-- Error Message -->
        <div v-if="error" class="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
          <p class="text-red-400 text-sm">{{ error }}</p>
        </div>

        <!-- Success Message -->
        <div v-if="successMessage" class="bg-green-500/10 border border-green-500/30 rounded-lg p-4 mb-6">
          <p class="text-green-400 text-sm">{{ successMessage }}</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-text-primary mb-2">Email</label>
            <input
              v-model="email"
              type="email"
              required
              placeholder="you@example.com"
              class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-3 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-text-primary mb-2">Password</label>
            <input
              v-model="password"
              type="password"
              required
              :placeholder="isSignUp ? 'Create a password (min 6 chars)' : 'Enter your password'"
              minlength="6"
              class="w-full bg-bg-tertiary border border-border rounded-lg px-4 py-3 text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-accent text-bg-primary py-3 rounded-lg font-medium hover:bg-accent-hover transition-colors disabled:opacity-50"
          >
            {{ loading ? 'Please wait...' : (isSignUp ? 'Create Account' : 'Sign In') }}
          </button>
        </form>

        <!-- Toggle -->
        <div class="mt-6 text-center">
          <button
            @click="toggleMode"
            class="text-accent hover:underline text-sm"
          >
            {{ isSignUp ? 'Already have an account? Sign in' : "Don't have an account? Sign up" }}
          </button>
        </div>
      </div>

      <!-- Skip Auth (Dev Mode) -->
      <div v-if="!isSupabaseConfigured" class="mt-6 text-center">
        <p class="text-text-tertiary text-sm mb-2">Supabase not configured</p>
        <button
          @click="skipAuth"
          class="text-accent hover:underline text-sm"
        >
          Continue without authentication →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { signIn, signUp, isSupabaseConfigured } from '../services/supabase'

const router = useRouter()

const isSignUp = ref(false)
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const successMessage = ref('')

const toggleMode = () => {
  isSignUp.value = !isSignUp.value
  error.value = ''
  successMessage.value = ''
}

const handleSubmit = async () => {
  loading.value = true
  error.value = ''
  successMessage.value = ''

  try {
    if (isSignUp.value) {
      await signUp(email.value, password.value)
      successMessage.value = 'Account created! Please check your email to verify your account.'
      isSignUp.value = false
    } else {
      await signIn(email.value, password.value)
      router.push('/tasks')
    }
  } catch (e) {
    error.value = e.message || 'An error occurred'
  } finally {
    loading.value = false
  }
}

const skipAuth = () => {
  router.push('/tasks')
}
</script>

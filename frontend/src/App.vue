<template>
  <div class="min-h-screen bg-bg-primary">
    <Header />
    <router-view />
  </div>
</template>

<script setup>
import Header from './components/Header.vue'
</script>

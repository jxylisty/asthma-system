<template>
  <div class="layout-container">
    <ParticleBackground />
    <Sidebar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import ParticleBackground from './ParticleBackground.vue'
</script>

<style scoped>
.layout-container {
  display: flex;
  min-height: 100vh;
  position: relative;
}

.main-content {
  flex: 1;
  margin-left: 230px;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}
</style>

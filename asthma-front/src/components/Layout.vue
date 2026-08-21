<template>
  <div class="layout-container">
    <ParticleBackground />
    <Sidebar v-model:isCollapse="isCollapse" />
    <main class="main-content" :style="{ marginLeft: isCollapse ? '68px' : '230px' }">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from './Sidebar.vue'
import ParticleBackground from './ParticleBackground.vue'

const isCollapse = ref(false)
</script>

<style scoped>
.layout-container {
  display: flex;
  min-height: 100vh;
  position: relative;
}

.main-content {
  flex: 1;
  height: 100vh;
  overflow-y: auto;
  position: relative;
  z-index: 1;
  transition: margin-left 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>

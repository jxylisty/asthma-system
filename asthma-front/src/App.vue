<template>
  <template v-if="isLoginPage">
    <router-view />
  </template>
  <template v-else>
    <Layout />
    <ClickEffect />
  </template>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Layout from './components/Layout.vue'
import ClickEffect from './components/ClickEffect.vue'

const route = useRoute()
const isLoginPage = computed(() => route.path === '/login')
</script>

<style>
:root {
  --bg-gradient: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-size-base: 14px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  height: 100%;
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  width: 100%;
  min-height: 100vh;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(64, 158, 255, 0.4);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(64, 158, 255, 0.6);
}

::selection {
  background: rgba(64, 158, 255, 0.3);
  color: inherit;
}
</style>
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import { initSettings } from './composables/useSettings'
import { initAiSettings } from './composables/useAiSettings'

initSettings()
initAiSettings()

const app = createApp(App)
app.use(ElementPlus)
app.use(router)
app.mount('#app')

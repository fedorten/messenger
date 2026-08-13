import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'
import { initTheme } from './services/theme'

initTheme()

const app = createApp(App)
app.use(router)
app.mount('#app')

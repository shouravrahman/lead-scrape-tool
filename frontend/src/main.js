import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import App from '@/App.vue'
import router from '@/router'
import '@/styles/global.scss'
import '@/styles/primevue-theme.css'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'
import Aura from '@primeuix/themes/aura';

const app = createApp(App)

// PrimeVue Configuration
app.use(PrimeVue, {
  theme: {
    preset: Aura
  }
})

app.use(createPinia())
app.use(router)
app.mount('#app')

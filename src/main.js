import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'

import './styles/theme.css'
import './styles/app.css'

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')

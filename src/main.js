import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'

import './styles/theme.css'
import './styles/app.css'

// Element Plus slider bug: tapping a mark label reaches the runway's *passive* touchstart
// listener, which calls preventDefault() -> console error. Stop the touch there; the
// browser's follow-up mousedown still hits the label's own handler and moves the slider.
document.addEventListener('touchstart', (e) => {
  if (e.target instanceof Element && e.target.closest('.el-slider__marks')) e.stopPropagation()
}, { capture: true, passive: true })

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')

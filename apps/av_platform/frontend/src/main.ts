// AV Platform shell (ADR-006): one Vue app on /av for the role screens; Desk is the back office.
import { createApp } from 'vue'
import { portalTargetKey } from 'frappe-ui'
import './style.css'
import App from './App.vue'
import { router } from './router'

const root = document.getElementById('app') as HTMLElement
const app = createApp(App)
app.use(router)
// Dialogs, menus and toasts stay inside .av-desk, where the scoped frappe-ui styles apply.
app.provide(portalTargetKey, root)
app.mount(root)

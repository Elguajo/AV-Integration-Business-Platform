// Mounts the role screens inside Frappe Desk pages (ADR-004). Desk owns the shell: navigation,
// sidebar, page title and URL. These screens only render server data and call Frappe APIs.
import { createApp, h, reactive, type Component } from 'vue'
import { FrappeUIProvider, portalTargetKey } from 'frappe-ui'
import './style.css'
import { ru } from './i18n/ru'
import { ruPm } from './i18n/pm'
import { ruOverview } from './i18n/overview'

export type View = 'sales' | 'board' | 'my-tasks' | 'overview' | 'projects' | 'project'

interface JQueryLike {
  get(index: number): HTMLElement
}

interface DeskPage {
  main: JQueryLike
}

interface Frappe {
  csrf_token: string
  boot: { av_desk?: { css: string[] } | null }
  ui: {
    make_app_page(options: { parent: HTMLElement; title: string; single_column: boolean }): DeskPage
  }
  get_route(): string[]
  set_route(...parts: string[]): unknown
  router: { on(event: 'change', handler: () => void): void }
}

declare global {
  interface Window {
    frappe: Frappe
    av_desk?: { mount_page: typeof mountPage }
  }
}

type PageModule = { default: Component }

const VIEWS: Record<View, { title: string; load: () => Promise<PageModule> }> = {
  sales: { title: ru.page.title, load: () => import('./pages/SalesWorkspace.vue') },
  board: { title: ruPm.page.title, load: () => import('./pages/ProjectBoard.vue') },
  'my-tasks': { title: ruPm.my.title, load: () => import('./pages/MyTasks.vue') },
  overview: { title: ruOverview.title, load: () => import('./pages/Overview.vue') },
  projects: { title: ruOverview.register.title, load: () => import('./pages/Projects.vue') },
  project: { title: ruOverview.card.title, load: () => import('./pages/ProjectCard.vue') },
}

function loadStyles(hrefs: string[]) {
  for (const href of hrefs) {
    if (document.querySelector(`link[data-av-desk="${href}"]`)) continue
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = href
    link.dataset.avDesk = href
    document.head.appendChild(link)
  }
}

// Boards scroll inside their columns, so the screen takes the height left under the Desk header.
function fitHeight(root: HTMLElement) {
  const fit = () => {
    if (!root.offsetParent) return
    const top = root.getBoundingClientRect().top + window.scrollY
    root.style.height = `${Math.max(420, window.innerHeight - top - 16)}px`
  }
  window.addEventListener('resize', fit)
  return fit
}

async function mountPage(wrapper: HTMLElement, pageName: string, view: View) {
  const { frappe } = window
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: VIEWS[view].title,
    single_column: true,
  })
  loadStyles(frappe.boot.av_desk?.css ?? [])
  // frappe-ui requests read the CSRF token from window, as on its own pages.
  window.csrf_token = frappe.csrf_token

  const root = document.createElement('div')
  root.className = 'av-desk'
  page.main.get(0).appendChild(root)
  const fit = fitHeight(root)

  const route = reactive({ args: frappe.get_route().slice(1) })
  frappe.router.on('change', () => {
    const current = frappe.get_route()
    if (current[0] !== pageName) return
    route.args = current.slice(1)
    requestAnimationFrame(fit)
  })

  const component = (await VIEWS[view].load()).default
  const props = () => {
    if (view === 'sales') {
      return {
        quotation: route.args[0],
        onNavigate: (quotation?: string) =>
          quotation ? frappe.set_route(pageName, quotation) : frappe.set_route(pageName),
      }
    }
    if (view === 'project') return { project: route.args[0] }
    return {}
  }

  const app = createApp({
    render: () => h(FrappeUIProvider, null, { default: () => h(component, props()) }),
  })
  // Dialogs, menus and toasts stay inside the scoped container instead of <body>.
  app.provide(portalTargetKey, root)
  app.mount(root)
  requestAnimationFrame(fit)
}

window.av_desk = { mount_page: mountPage }

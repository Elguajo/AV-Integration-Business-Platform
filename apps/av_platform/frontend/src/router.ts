import { createRouter, createWebHistory } from 'vue-router'
import { boot, landingPath, type ViewKey } from './boot'

declare module 'vue-router' {
  interface RouteMeta {
    view?: ViewKey
    // A record page (project card): the app menu folds to icons so the record's own column of
    // sections is the one wide menu on screen (research/12 §6.2а).
    record?: boolean
  }
}

export const router = createRouter({
  history: createWebHistory('/av'),
  routes: [
    { path: '/', redirect: () => landingPath() },
    { path: '/home', component: () => import('./pages/Overview.vue'), meta: { view: 'home' } },
    { path: '/my-tasks', component: () => import('./pages/MyTasks.vue'), meta: { view: 'my-tasks' } },
    { path: '/projects', component: () => import('./pages/Projects.vue'), meta: { view: 'projects' } },
    {
      path: '/projects/:project',
      component: () => import('./pages/ProjectCard.vue'),
      props: true,
      meta: { view: 'projects', record: true },
    },
    { path: '/board', component: () => import('./pages/ProjectBoard.vue'), meta: { view: 'board' } },
    {
      path: '/sales/:quotation?',
      component: () => import('./pages/SalesWorkspace.vue'),
      props: true,
      meta: { view: 'sales' },
    },
    { path: '/:pathMatch(.*)*', component: () => import('./pages/NotFound.vue') },
  ],
})

// The menu shows only the screens of the user's roles; a link to another one goes to the start
// screen. The data itself is protected by the server, not by this check.
router.beforeEach((to) => {
  if (to.meta.view && !boot.views.includes(to.meta.view)) return landingPath()
})

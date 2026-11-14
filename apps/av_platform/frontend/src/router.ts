import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory('/av'),
  routes: [
    { path: '/', redirect: '/sales' },
    {
      path: '/sales/:quotation?',
      name: 'Sales',
      component: () => import('./pages/SalesWorkspace.vue'),
      props: true,
    },
    {
      path: '/my-tasks',
      name: 'MyTasks',
      component: () => import('./pages/MyTasks.vue'),
    },
    {
      path: '/board',
      name: 'Board',
      component: () => import('./pages/ProjectBoard.vue'),
    },
    { path: '/:pathMatch(.*)*', redirect: '/sales' },
  ],
})

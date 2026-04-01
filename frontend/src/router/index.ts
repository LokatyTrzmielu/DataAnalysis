import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },
    {
      path: '/runs',
      name: 'runs',
      component: () => import('@/views/RunsView.vue'),
    },
    {
      path: '/runs/:id',
      name: 'run',
      component: () => import('@/views/RunView.vue'),
    },
    {
      path: '/carriers',
      name: 'carriers',
      component: () => import('@/views/CarriersView.vue'),
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

// Auth guard: redirect unauthenticated users to login
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login' }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
})

export default router

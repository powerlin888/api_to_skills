import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      children: [
        { path: '', name: 'Home', component: () => import('@/views/HomeView.vue') },
        { path: 'pdf-upload', name: 'PdfUpload', component: () => import('@/views/PdfUploadView.vue') },
        { path: 'agent-config', name: 'AgentConfig', component: () => import('@/views/AgentConfigView.vue') },
        { path: 'chat/:agentId', name: 'Chat', component: () => import('@/views/ChatView.vue') },
        { path: 'model-config', name: 'ModelConfig', component: () => import('@/views/ModelConfigView.vue') },
        { path: 'community', name: 'Community', component: () => import('@/views/CommunityView.vue') },
      ],
    },
  ],
})

const PUBLIC_ROUTES = new Set(['Home', 'Login', 'Community'])

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (!auth.isAuthenticated && !PUBLIC_ROUTES.has(to.name as string)) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && auth.isAuthenticated) {
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router

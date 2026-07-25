import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior() {
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
    },
    {
      path: '/stages',
      name: 'stages',
      component: () => import('../views/StagesView.vue'),
    },
    {
      path: '/documents',
      name: 'documents',
      component: () => import('../views/DocumentsView.vue'),
    },
    {
      path: '/official-channels',
      name: 'official-channels',
      component: () => import('../views/OfficialChannelsView.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: () => import('../views/PrivacyView.vue'),
    },
    {
      path: '/disclaimer',
      name: 'disclaimer',
      component: () => import('../views/DisclaimerView.vue'),
    },
    {
      path: '/legal-sources',
      name: 'legal-sources',
      component: () => import('../views/LegalSourcesView.vue'),
    },
    {
      path: '/coming-soon',
      name: 'coming-soon',
      component: () => import('../views/ComingSoonView.vue'),
    },
    {
      // 未匹配到的路径统一进入占位页，避免出现 404
      path: '/:pathMatch(.*)*',
      redirect: '/coming-soon',
    },
  ],
})

export default router

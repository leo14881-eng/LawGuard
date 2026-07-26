import { createRouter, createWebHistory } from 'vue-router'
import { applyRouteSeo } from '../utils/seo'

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
      path: '/stages/:id',
      name: 'stage-detail',
      component: () => import('../views/StageDetailView.vue'),
    },
    {
      path: '/rights-guide',
      name: 'rights-guide',
      component: () => import('../views/RightsGuideView.vue'),
    },
    {
      path: '/rights-guide/:id',
      name: 'rights-guide-detail',
      component: () => import('../views/RightsGuideDetailView.vue'),
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
      path: '/emergency-guide',
      name: 'emergency-guide',
      component: () => import('../views/EmergencyGuideView.vue'),
    },
    {
      // 未匹配到任何已知路径时展示 404 页面。
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/NotFoundView.vue'),
    },
  ],
})

// 每次路由跳转后同步更新 document.title / description / canonical / Open Graph /
// Twitter Card，覆盖首页与返回首页的场景（见 utils/seo.ts）。
router.afterEach((to) => {
  applyRouteSeo(typeof to.name === 'string' ? to.name : undefined, to.path)
})

export default router

import { createRouter, createWebHashHistory } from 'vue-router'
import AdminLayout from '../components/AdminLayout.vue'

const routes = [
  {
    path: '/',
    component: AdminLayout,
    children: [
      { path: '', redirect: '/screen' },
      { path: 'screen', name: 'screen', component: () => import('../views/ScreenView.vue'), meta: { title: '现场大屏' } },
      { path: 'resumes', name: 'resumes', component: () => import('../views/ResumesView.vue'), meta: { title: '简历管理' } },
      { path: 'positions', name: 'positions', component: () => import('../views/PositionsView.vue'), meta: { title: '岗位管理' } },
      { path: 'schools', name: 'schools', component: () => import('../views/SchoolsView.vue'), meta: { title: '学校管理' } },
      { path: 'dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { title: '数据看板' } }
    ]
  }
]

export default createRouter({
  history: createWebHashHistory(),
  routes
})

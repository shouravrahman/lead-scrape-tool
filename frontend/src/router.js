import { createRouter, createWebHistory } from 'vue-router'
import SearchView from '@/views/SearchView.vue'
import LeadsView from '@/views/LeadsView.vue'
import CampaignsView from '@/views/CampaignsView.vue'
import AnalyticsView from '@/views/AnalyticsView.vue'
import LogsView from '@/views/LogsView.vue'

const routes = [
  {
    path: '/',
    name: 'Search',
    component: SearchView,
  },
  {
    path: '/leads',
    name: 'Leads',
    component: LeadsView,
  },
  {
    path: '/campaigns',
    name: 'Campaigns',
    component: CampaignsView,
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: AnalyticsView,
  },
  {
    path: '/logs',
    name: 'Logs',
    component: LogsView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

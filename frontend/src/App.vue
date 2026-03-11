<template>
  <div id="app" class="app-wrapper">
    <!-- Sidebar -->
    <aside class="app-sidebar">
      <div class="logo">
        <!-- <i class="pi pi-chart-bar logo-icon"></i> -->
        <h1>LEAD INTEL</h1>
      </div>
      <nav class="sidebar-menu">
        <router-link v-for="nav in navItems" :key="nav.to" :to="nav.to" class="sidebar-link" active-class="active">
          <i :class="nav.icon" class="icon"></i>
          <span class="label">{{ nav.label }}</span>
        </router-link>
      </nav>
    </aside>

    <!-- Main Content Area -->
    <div class="main-layout">
      <!-- Top Navbar -->
      <header class="app-navbar">
        <div class="campaign-selector">
          <label>Campaign:</label>
          <Dropdown v-model="activeCampaignId" :options="campaigns" option-label="name" option-value="id" placeholder="All Campaigns" show-clear />
          <Button label="+ New" class="p-button-sm" @click="$router.push('/campaigns')" />
        </div>

        <div class="quota-display">
          <div v-for="q in quotaStatus" :key="q.provider" class="quota-item">
            <span class="q-label">{{ q.provider }}</span>
            <ProgressBar :value="(q.used / q.limit) * 100" />
            <span class="q-text">{{ q.used }}/{{ q.limit }}</span>
          </div>
        </div>
      </header>

      <!-- Main Content -->
      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import ProgressBar from 'primevue/progressbar'
import { useCampaignStore, useAnalyticsStore } from '@/stores'
import { quotaAPI, chatAPI } from '@/api'

const router = useRouter()
const campaignStore = useCampaignStore()
const analyticsStore = useAnalyticsStore()

const navItems = [
  { to: '/', icon: 'pi pi-search', label: 'Search' },
  { to: '/leads', icon: 'pi pi-list', label: 'Leads' },
  { to: '/campaigns', icon: 'pi pi-folder', label: 'Campaigns' },
  { to: '/analytics', icon: 'pi pi-chart-line', label: 'Analytics' },
  { to: '/logs', icon: 'pi pi-file', label: 'Logs' },
]

const campaigns = ref([])
const activeCampaignId = ref(null)
const overview = ref(null)
const quotaStatus = ref([])
const showChat = ref(false)
const chatHistory = ref([])
const chatInput = ref('')
const showOnboarding = ref(true)

onMounted(async () => {
  await campaignStore.fetchCampaigns()
  campaigns.value = campaignStore.campaigns

  await analyticsStore.fetchOverview()
  overview.value = analyticsStore.overview

  try {
    const response = await quotaAPI.getStatus()
    quotaStatus.value = response.data.providers || []
  } catch (error) {
    console.error('Failed to fetch quota:', error)
  }

  const saved = localStorage.getItem('activeCampaignId')
  if (saved) activeCampaignId.value = parseInt(saved)
})
</script>

<style scoped>
:root {
  --primary-color: #c0c0c0; /* Platinum */
  --primary-color-dark: #a8a8a8; /* Dark Platinum */
  --primary-color-light: #d4d4d4; /* Light Platinum */
}

.app-wrapper {
  display: flex;
  height: 100vh;
  background-color: #1e1e1e;
  color: #ffffff;
}

/* SIDEBAR */
.app-sidebar {
  width: 250px;
  background-color: #2c2c2c;
  display: flex;
  flex-direction: column;
  padding: 1rem;
}

.logo {
  text-align: center;
  margin-bottom: 2rem;
  margin-right: 0; /* Removed right margin */
}

.logo-icon {
  font-size: 2rem;
  color: #ffffff;
}

.sidebar-menu {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sidebar-link {
  color: #FFFFFF;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
  display: flex;
  align-items: center;
  gap: 0.5rem; /* Added margin between icon and text */
}

.sidebar-link .icon {
  margin-right: 0.5rem; /* Added margin to the right of the icon */
}

.sidebar-link:hover {
  background-color: rgba(192, 192, 192, 0.1);
}

.sidebar-link.active {
  background-color: #444;
}

/* MAIN LAYOUT */
.main-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* TOP NAVBAR */
.app-navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background-color: #333;
  border-bottom: 1px solid #444;
  margin-bottom: 1rem;
}

.campaign-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.campaign-selector label {
  font-weight: 600;
  color: var(--primary-color);
  white-space: nowrap;
  font-size: 0.95rem;
}

.quota-display {
  display: flex;
  gap: 2rem;
  flex: 1;
  justify-content: flex-end;
  align-items: center;
  flex-wrap: wrap;
}

.quota-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 150px;
}

.quota-item .q-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  min-width: 45px;
}

.quota-item .q-text {
  font-size: 0.8rem;
  color: var(--primary-color);
  font-weight: 600;
  min-width: 45px;
  text-align: right;
}

/* MAIN CONTENT */
.app-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

/* FOOTER */
.app-footer {
  background: rgba(20, 21, 28, 0.9);
  border-top: 1px solid rgba(192, 192, 192, 0.1);
  padding: 0.75rem 2rem;
  display: flex;
  justify-content: center;
  gap: 3rem;
  flex-wrap: wrap;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.stat .label {
  font-size: 0.75rem;
  color: #888;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat .value {
  font-size: 1.25rem;
  color: var(--primary-color);
  font-weight: 700;
}

/* CHAT BUTTON */
.chat-btn {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  box-shadow: 0 4px 20px rgba(192, 192, 192, 0.3);
  z-index: 200;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.message {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  line-height: 1.4;
  max-width: 90%;
}

.message.user {
  background: rgba(192, 192, 192, 0.2);
  color: #fff;
  align-self: flex-end;
  border-bottom-right-radius: 4px;
}

.message.assistant {
  background: rgba(192, 192, 192, 0.1);
  color: #ccc;
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}

.chat-input-area {
  display: flex;
  gap: 0.5rem;
  border-top: 1px solid rgba(192, 192, 192, 0.2);
  padding-top: 0.75rem;
}

.chat-input-area input {
  flex: 1;
}
.page-header{
 
  margin-bottom: 1.5rem;
}

@media (max-width: 768px) {
  .app-header {
    padding: 0.75rem 1rem;
    gap: 1rem;
  }

  .top-bar {
    padding: 0.75rem 1rem;
    gap: 1rem;
  }

  .app-content {
    padding: 1rem;
  }

  .app-footer {
    padding: 0.5rem 1rem;
    gap: 1.5rem;
  }

  .chat-btn {
    width: 50px;
    height: 50px;
    bottom: 1rem;
    right: 1rem;
  }
}
</style>

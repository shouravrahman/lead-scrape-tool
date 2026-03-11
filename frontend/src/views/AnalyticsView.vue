<template>
  <div class="analytics-view">
    <h2>📈 How You Are Growing</h2>

    <Skeleton v-if="!overview" height="200px" />

    <div v-else class="analytics-container">
      <!-- Key Metrics Cards -->
      <div class="metrics-grid">
        <Card class="metric-card">
          <template #header>
            <div class="metric-number">{{ overview.total_leads }}</div>
          </template>
          <p class="metric-label">Total People</p>
        </Card>

        <Card class="metric-card">
          <template #header>
            <div class="metric-number">{{ overview.active_jobs }}</div>
          </template>
          <p class="metric-label">Active Jobs</p>
        </Card>

        <Card class="metric-card">
          <template #header>
            <div class="metric-number">{{ overview.leads_by_vetting?.good || 0 }}</div>
          </template>
          <p class="metric-label">Good Fit</p>
        </Card>

        <Card class="metric-card">
          <template #header>
            <div class="metric-number">{{ overview.total_campaigns }}</div>
          </template>
          <p class="metric-label">Campaigns</p>
        </Card>
      </div>

      <!-- Lead Quality Distribution Chart -->
      <Card class="chart-card">
        <template #header>
          <h3>Lead Quality Distribution</h3>
        </template>
        <Chart type="pie" :data="leadQualityData" :options="chartOptions" />
      </Card>

      <!-- Status Distribution Chart -->
      <Card class="chart-card">
        <template #header>
          <h3>Status Breakdown</h3>
        </template>
        <Chart type="bar" :data="statusBreakdownData" :options="chartOptions" />
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAnalyticsStore, useCampaignStore } from '@/stores'
import Card from 'primevue/card'
import ProgressBar from 'primevue/progressbar'
import Skeleton from 'primevue/skeleton'
import Chart from 'primevue/chart'

const analyticsStore = useAnalyticsStore()
const campaignStore = useCampaignStore()

const overview = ref(null)
const leadQualityData = ref(null)
const statusBreakdownData = ref(null)
const chartOptions = ref({
  plugins: {
    legend: {
      labels: {
        color: '#FFFFFF',
      },
    },
  },
  scales: {
    x: {
      ticks: {
        color: '#FFFFFF',
      },
    },
    y: {
      ticks: {
        color: '#FFFFFF',
      },
    },
  },
})

onMounted(async () => {
  await analyticsStore.fetchOverview(campaignStore.activeCampaignId)
  overview.value = analyticsStore.overview

  // Prepare data for Lead Quality Distribution chart
  leadQualityData.value = {
    labels: Object.keys(overview.value.leads_by_vetting || {}),
    datasets: [
      {
        data: Object.values(overview.value.leads_by_vetting || {}),
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
      },
    ],
  }

  // Prepare data for Status Breakdown chart
  statusBreakdownData.value = {
    labels: Object.keys(overview.value.leads_by_status || {}),
    datasets: [
      {
        label: 'Status Count',
        data: Object.values(overview.value.leads_by_status || {}),
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
      },
    ],
  }
})
</script>

<style scoped>
.analytics-view {
  padding: 2rem;
  color: #FFFFFF;
}

.analytics-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.metric-card {
  text-align: center;
  padding: 1rem;
  background-color: #1E1E1E;
  border-radius: 8px;
}

.metric-number {
  font-size: 2rem;
  font-weight: bold;
}

.metric-label {
  font-size: 1rem;
  color: #AAAAAA;
}

.chart-card {
  padding: 1rem;
  background-color: #1E1E1E;
  border-radius: 8px;
}

.status-breakdown {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-name {
  font-weight: bold;
  color: #FFFFFF;
}

.status-count {
  color: #AAAAAA;
}
</style>


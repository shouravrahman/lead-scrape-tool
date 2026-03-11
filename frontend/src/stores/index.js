import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { campaignAPI, searchAPI, leadsAPI, analyticsAPI } from '@/api'

export const useCampaignStore = defineStore('campaign', () => {
  const campaigns = ref([])
  const activeCampaignId = ref(null)
  const loading = ref(false)

  const activeCampaign = computed(() => {
    return campaigns.value.find(c => c.id === activeCampaignId.value)
  })

  async function fetchCampaigns() {
    loading.value = true
    try {
      const response = await campaignAPI.list()
      campaigns.value = response.data
    } catch (error) {
      console.error('Failed to fetch campaigns:', error)
    } finally {
      loading.value = false
    }
  }

  async function createCampaign(data) {
    try {
      const response = await campaignAPI.create(data)
      campaigns.value.push(response.data)
      return response.data
    } catch (error) {
      console.error('Failed to create campaign:', error)
      throw error
    }
  }

  async function deleteCampaign(id) {
    try {
      await campaignAPI.delete(id)
      campaigns.value = campaigns.value.filter(c => c.id !== id)
      if (activeCampaignId.value === id) {
        activeCampaignId.value = null
      }
    } catch (error) {
      console.error('Failed to delete campaign:', error)
      throw error
    }
  }

  function setActiveCampaign(id) {
    activeCampaignId.value = id
    localStorage.setItem('activeCampaignId', id)
  }

  return {
    campaigns,
    activeCampaignId,
    activeCampaign,
    loading,
    fetchCampaigns,
    createCampaign,
    deleteCampaign,
    setActiveCampaign,
  }
})

export const useJobStore = defineStore('job', () => {
  const jobs = ref([])
  const activeJobs = computed(() => jobs.value.filter(j => ['processing_intent', 'scraping'].includes(j.status)))
  const loading = ref(false)

  async function fetchJobs(campaignId = null) {
    loading.value = true
    try {
      const response = await searchAPI.listJobs({ campaign_id: campaignId })
      jobs.value = response.data
    } catch (error) {
      console.error('Failed to fetch jobs:', error)
    } finally {
      loading.value = false
    }
  }

  async function startSearch(data) {
    try {
      const response = await searchAPI.startSearch(data)
      return response.data
    } catch (error) {
      console.error('Failed to start search:', error)
      throw error
    }
  }

  async function stopJob(jobId) {
    try {
      await searchAPI.stopJob(jobId)
      const job = jobs.value.find(j => j.id === jobId)
      if (job) job.status = 'stopped'
    } catch (error) {
      console.error('Failed to stop job:', error)
      throw error
    }
  }

  async function pollJobStatus(jobId, interval = 3000) {
    return new Promise(resolve => {
      const poll = setInterval(async () => {
        try {
          const response = await searchAPI.getJobStatus(jobId)
          const jobIndex = jobs.value.findIndex(j => j.id === jobId)
          if (jobIndex >= 0) {
            jobs.value[jobIndex] = response.data
          }

          if (['completed', 'failed', 'stopped'].includes(response.data.status)) {
            clearInterval(poll)
            resolve(response.data)
          }
        } catch (error) {
          console.error('Failed to poll job status:', error)
        }
      }, interval)
    })
  }

  return {
    jobs,
    activeJobs,
    loading,
    fetchJobs,
    startSearch,
    stopJob,
    pollJobStatus,
  }
})

export const useLeadStore = defineStore('lead', () => {
  const leads = ref([])
  const totalLeads = ref(0)
  const loading = ref(false)

  async function fetchLeads(filters = {}) {
    loading.value = true
    try {
      const response = await leadsAPI.list(filters)
      leads.value = response.data
      totalLeads.value = response.data.length
    } catch (error) {
      console.error('Failed to fetch leads:', error)
    } finally {
      loading.value = false
    }
  }

  async function updateLeadVetting(leadId, data) {
    try {
      const response = await leadsAPI.updateVetting(leadId, data)
      const index = leads.value.findIndex(l => l.id === leadId)
      if (index >= 0) {
        leads.value[index] = response.data
      }
      return response.data
    } catch (error) {
      console.error('Failed to update lead vetting:', error)
      throw error
    }
  }

  async function exportToSheets(filters = {}) {
    try {
      const response = await leadsAPI.exportToSheets(filters)
      return response.data
    } catch (error) {
      console.error('Failed to export leads:', error)
      throw error
    }
  }

  return {
    leads,
    totalLeads,
    loading,
    fetchLeads,
    updateLeadVetting,
    exportToSheets,
  }
})

export const useAnalyticsStore = defineStore('analytics', () => {
  const overview = ref(null)
  const distribution = ref(null)
  const loading = ref(false)

  async function fetchOverview(campaignId = null) {
    loading.value = true
    try {
      const response = await analyticsAPI.getOverview(campaignId)
      overview.value = response.data
    } catch (error) {
      console.error('Failed to fetch overview:', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchDistribution(campaignId = null) {
    try {
      const response = await analyticsAPI.getDistribution(campaignId)
      distribution.value = response.data
    } catch (error) {
      console.error('Failed to fetch distribution:', error)
    }
  }

  return {
    overview,
    distribution,
    loading,
    fetchOverview,
    fetchDistribution,
  }
})

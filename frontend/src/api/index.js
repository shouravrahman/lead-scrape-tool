import api from './client'

// ============================================================================
// CAMPAIGNS API
// ============================================================================

export const campaignAPI = {
  list() {
    return api.get('/campaigns')
  },
  get(id) {
    return api.get(`/campaigns/${id}`)
  },
  create(data) {
    return api.post('/campaigns', data)
  },
  delete(id) {
    return api.delete(`/campaigns/${id}`)
  },
}

// ============================================================================
// SEARCH & JOBS API
// ============================================================================

export const searchAPI = {
  startSearch(data) {
    return api.post('/search', data)
  },
  getJobStatus(jobId) {
    return api.get(`/jobs/${jobId}`)
  },
  listJobs(filters = {}) {
    return api.get('/jobs', { params: filters })
  },
  stopJob(jobId) {
    return api.post(`/jobs/${jobId}/stop`)
  },
}

// ============================================================================
// LEADS API
// ============================================================================

export const leadsAPI = {
  list(filters = {}) {
    return api.get('/leads', { params: filters })
  },
  get(id) {
    return api.get(`/leads/${id}`)
  },
  updateVetting(id, data) {
    return api.patch(`/leads/${id}/vetting`, data)
  },
  exportToSheets(filters = {}) {
    return api.post('/leads/export', {}, { params: filters })
  },
}

// ============================================================================
// ANALYTICS API
// ============================================================================

export const analyticsAPI = {
  getOverview(campaignId = null) {
    return api.get('/analytics', { params: { campaign_id: campaignId } })
  },
  getDistribution(campaignId = null) {
    return api.get('/analytics/distribution', { params: { campaign_id: campaignId } })
  },
}

// ============================================================================
// LOGS API
// ============================================================================

export const logsAPI = {
  list(logType = 'agent', limit = 100) {
    return api.get('/logs', { params: { log_type: logType, limit } })
  },
}

// ============================================================================
// QUOTA API
// ============================================================================

export const quotaAPI = {
  getStatus() {
    return api.get('/quota-status')
  },
}

// ============================================================================
// CHAT API
// ============================================================================

export const chatAPI = {
  send(message, history = null) {
    return api.post('/chat', { message, history })
  },
}

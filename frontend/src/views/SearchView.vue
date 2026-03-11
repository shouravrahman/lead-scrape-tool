<template>
  <div class="search-view">
    <!-- Search Form Card -->
    <Card class="search-card">
      <template #header>
        <div class="card-header">
          <h2>🔍 Find New People</h2>
          <p>Describe your ideal target audience</p>
        </div>
      </template>

      <form @submit.prevent="submitSearch" class="search-form">
        <div class="form-group">
          <label for="intent">Target Profile</label>
          <Textarea
            v-model="searchQuery.user_intent"
            placeholder="e.g., 'Pet shop owners in New York with 5+ employees, active on LinkedIn'"
            :auto-resize="true"
            rows="5"
            input-id="intent"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="search-name">Search Name</label>
            <InputText
              v-model="searchName"
              placeholder="e.g., Pet Shop Owners Q1"
              input-id="search-name"
            />
          </div>
          <div class="form-group">
            <label for="max-leads">How many?</label>
            <InputNumber
              v-model="searchQuery.max_leads"
              :min="1"
              :max="1000"
              input-id="max-leads"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="sheet-id">Google Sheet ID (Optional)</label>
          <InputText
            v-model="searchQuery.sheet_id"
            placeholder="Leave blank if you don't have one"
            input-id="sheet-id"
          />
        </div>

        <Button
          type="submit"
          label="🚀 Start Finding People"
          :loading="loading"
          class="w-full"
          severity="success"
        />
      </form>

      <Message
        v-if="successMessage"
        severity="success"
        :text="successMessage"
        class="mt-3"
      />
      <Message
        v-if="errorMessage"
        severity="error"
        :text="errorMessage"
        class="mt-3"
      />
    </Card>

    <!-- Active Jobs Section -->
    <div v-if="activeJobs.length > 0" class="jobs-section">
      <h3>🔄 Active Jobs</h3>
      <div class="jobs-grid">
        <Card v-for="job in activeJobs" :key="job.id" class="job-card">
          <template #header>
            <div class="job-header">
              <h4>Job #{{ job.id }}: {{ job.name }}</h4>
              <Button
                icon="pi pi-times"
                class="p-button-rounded p-button-text p-button-danger"
                @click="stopJob(job.id)"
              />
            </div>
          </template>
          <div class="job-info">
            <p class="leads-count">{{ job.leads_found }}/{{ job.max_leads }} leads found</p>
            <ProgressBar
              :value="(job.leads_found / job.max_leads) * 100"
              show-value
            />
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useJobStore, useCampaignStore } from '@/stores'
import { searchAPI } from '@/api'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import ProgressBar from 'primevue/progressbar'
import Message from 'primevue/message'

const jobStore = useJobStore()
const campaignStore = useCampaignStore()

const searchQuery = ref({
  user_intent: '',
  campaign_id: null,
  max_leads: 50,
  sheet_id: '',
})
const searchName = ref('')
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const activeJobs = computed(() => jobStore.activeJobs)

onMounted(async () => {
  searchQuery.value.campaign_id = campaignStore.activeCampaignId
  await jobStore.fetchJobs(campaignStore.activeCampaignId)
})

async function submitSearch() {
  if (!searchQuery.value.user_intent || searchQuery.value.user_intent.length < 10) {
    errorMessage.value = 'Please provide a detailed target profile'
    return
  }

  if (!searchQuery.value.campaign_id) {
    errorMessage.value = 'Please select a campaign first'
    return
  }

  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const response = await jobStore.startSearch(searchQuery.value)
    successMessage.value = `✅ Search Job #${response.job_id} started!`
    searchQuery.value.user_intent = ''
    searchName.value = ''
    await jobStore.fetchJobs(searchQuery.value.campaign_id)
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Failed to start search'
  } finally {
    loading.value = false
  }
}

async function stopJob(jobId) {
  try {
    await jobStore.stopJob(jobId)
    await jobStore.fetchJobs(searchQuery.value.campaign_id)
  } catch (error) {
    errorMessage.value = 'Failed to stop job'
  }
}
</script>

<style scoped lang="scss">
.search-view {
  max-width: 900px;
  margin: 0 auto;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  :deep(.p-inputtext),
  :deep(.p-inputtextarea),
  :deep(.p-inputnumber .p-inputnumber-input) {
    width: 100%;
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.jobs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
</style>

<template>
  <div class="campaigns-view">
    <div class="page-header">
      <div class="header-content">
        <h2>📂 Manage Campaigns</h2>
        <Button
          icon="pi pi-plus"
          label="New Campaign"
          @click="showCreateDialog = true"
          severity="success"
          class="new-campaign-btn"
        />
      </div>
    </div>

    <!-- Campaigns Grid -->
    <div v-if="campaigns.length === 0" class="empty-state">
      <p>No campaigns yet. Create one to get started!</p>
    </div>

    <div v-else class="campaigns-grid">
      <Card v-for="campaign in campaigns" :key="campaign.id" class="campaign-card">
        <template #header>
          <div class="campaign-header">
            <h4>{{ campaign.name }}</h4>
            <Button
              icon="pi pi-trash"
              class="p-button-rounded p-button-text p-button-danger"
              @click="deleteCampaign(campaign.id)"
            />
          </div>
        </template>
        <p class="campaign-desc">{{ campaign.description }}</p>
        <small class="campaign-meta">Created at {{ formatDate(campaign.created_at) }}</small>
      </Card>
    </div>

    <!-- Create Campaign Dialog -->
    <Dialog
      v-model:visible="showCreateDialog"
      header="Create New Campaign"
      :modal="true"
      :style="{ width: '500px' }"
    >
      <div class="form-group">
        <label for="campaign-name">Campaign Name</label>
        <InputText
          v-model="newCampaign.name"
          placeholder="e.g., New York Pet Shops"
          input-id="campaign-name"
          class="w-full"
        />
      </div>

      <div class="form-group mt-3">
        <label for="campaign-desc">Description</label>
        <Textarea
          v-model="newCampaign.description"
          placeholder="What is this campaign for?"
          rows="4"
          input-id="campaign-desc"
          class="w-full"
        />
      </div>

      <template #footer>
        <Button
          label="Cancel"
          @click="showCreateDialog = false"
          class="p-button-text"
        />
        <Button
          label="Create"
          @click="createCampaign"
          severity="success"
          :loading="creating"
        />
      </template>
    </Dialog>

    <Message
      v-if="message"
      :severity="message.type"
      :text="message.text"
      class="mt-3"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCampaignStore } from '@/stores'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Message from 'primevue/message'

const campaignStore = useCampaignStore()

const campaigns = ref([])
const showCreateDialog = ref(false)
const creating = ref(false)
const newCampaign = ref({ name: '', description: '' })
const message = ref(null)

onMounted(async () => {
  await campaignStore.fetchCampaigns()
  campaigns.value = campaignStore.campaigns
})

async function createCampaign() {
  if (!newCampaign.value.name.trim()) {
    message.value = { type: 'error', text: 'Campaign name required' }
    return
  }

  creating.value = true
  try {
    await campaignStore.createCampaign(newCampaign.value)
    campaigns.value = campaignStore.campaigns
    newCampaign.value = { name: '', description: '' }
    showCreateDialog.value = false
    message.value = { type: 'success', text: '✅ Campaign created!' }
  } catch (error) {
    message.value = { type: 'error', text: 'Failed to create campaign' }
  } finally {
    creating.value = false
  }
}

async function deleteCampaign(id) {
  if (!confirm('Delete this campaign?')) return

  try {
    await campaignStore.deleteCampaign(id)
    campaigns.value = campaignStore.campaigns
    message.value = { type: 'success', text: '✅ Campaign deleted!' }
  } catch (error) {
    message.value = { type: 'error', text: 'Failed to delete campaign' }
  }
}

function formatDate(date) {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString()
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.new-campaign-btn {
  margin-left: auto;
}

/* ...existing styles... */
</style>


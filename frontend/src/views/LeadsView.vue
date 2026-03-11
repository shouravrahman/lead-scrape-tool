<template>
  <div class="leads-view">
    <h2>🎯 Your Leads List</h2>

    <!-- Filters Toolbar -->
    <Toolbar class="mb-4">
      <template #start>
        <InputText
          v-model="filters.search_key"
          placeholder="Search by name or skill..."
          class="mr-2"
        />
        <Dropdown
          v-model="filters.vetting_status"
          :options="vettingOptions"
          option-label="label"
          option-value="value"
          placeholder="Status"
          class="mr-2"
        />
        <Button
          icon="pi pi-search"
          label="Filter"
          @click="applyFilters"
          class="mr-2"
        />
      </template>
      <template #end>
        <Button
          icon="pi pi-download"
          label="Export All"
          @click="exportToSheets"
          :disabled="leads.length === 0"
          severity="secondary"
        />
      </template>
    </Toolbar>

    <!-- Leads DataTable -->
    <DataTable
      :value="leads"
      :rows="10"
      :paginator="true"
      responsive-layout="scroll"
      striped-rows
      :loading="loading"
    >
      <Column field="name" header="Name" />
      <Column field="company" header="Company" />
      <Column field="email" header="Email" />
      <Column field="role" header="Role" />
      <Column field="score" header="Match Score">
        <template #body="{ data }">
          <span class="score-badge">{{ (data.score || 0).toFixed(1) }}</span>
        </template>
      </Column>
      <Column field="vetting_status" header="Status">
        <template #body="{ data }">
          <Tag
            :value="data.vetting_status || 'unvetted'"
            :severity="getVettingSeverity(data.vetting_status)"
          />
        </template>
      </Column>
      <Column header="Actions" :exportable="false">
        <template #body="{ data }">
          <Button
            icon="pi pi-check"
            class="p-button-success p-button-rounded p-button-text p-button-sm"
            @click="updateVetting(data.id, 'good')"
          />
          <Button
            icon="pi pi-times"
            class="p-button-danger p-button-rounded p-button-text p-button-sm"
            @click="updateVetting(data.id, 'junk')"
          />
          <Button
            icon="pi pi-download"
            class="p-button-info p-button-rounded p-button-text p-button-sm"
            @click="exportLead(data)"
          />
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useLeadStore, useCampaignStore } from '@/stores'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import Toolbar from 'primevue/toolbar'
import Tag from 'primevue/tag'

const leadStore = useLeadStore()
const campaignStore = useCampaignStore()

const leads = ref([])
const loading = ref(false)
const filters = ref({
  search_key: '',
  vetting_status: '',
  min_score: null,
  sort_by: 'newest',
})

const vettingOptions = [
  { label: 'All', value: '' },
  { label: '✅ Good Fit', value: 'good' },
  { label: '❌ Junk', value: 'junk' },
  { label: '🟡 Unvetted', value: 'unvetted' },
]

onMounted(async () => {
  await applyFilters()
})

async function applyFilters() {
  loading.value = true
  try {
    const filterParams = {
      ...filters.value,
      campaign_id: campaignStore.activeCampaignId,
    }
    await leadStore.fetchLeads(filterParams)
    leads.value = leadStore.leads
  } finally {
    loading.value = false
  }
}

async function updateVetting(leadId, status) {
  try {
    await leadStore.updateLeadVetting(leadId, { vetting_status: status })
    const idx = leads.value.findIndex(l => l.id === leadId)
    if (idx >= 0) leads.value[idx].vetting_status = status
  } catch (error) {
    console.error('Failed to update:', error)
  }
}

async function exportToSheets() {
  try {
    await leadStore.exportToSheets({ campaign_id: campaignStore.activeCampaignId })
    alert('✅ Exported to Google Sheets!')
  } catch (error) {
    alert('Failed to export')
  }
}

async function exportLead(lead) {
  try {
    await leadStore.exportToSheets({ campaign_id: lead.campaign_id })
    alert('✅ Lead exported!')
  } catch (error) {
    alert('Failed to export')
  }
}

function getVettingSeverity(status) {
  const severities = {
    good: 'success',
    junk: 'danger',
    unvetted: 'warning',
  }
  return severities[status] || 'info'
}
</script>




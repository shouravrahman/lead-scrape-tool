<template>
  <div class="logs-view">
    <h2>📜 System Logs</h2>

    <!-- Controls -->
    <Toolbar class="mb-4">
      <template #start>
        <Dropdown
          v-model="logType"
          :options="logTypeOptions"
          option-label="label"
          option-value="value"
          placeholder="Log Type"
          class="mr-2"
        />
        <Dropdown
          v-model="logLimit"
          :options="logLimitOptions"
          option-label="label"
          option-value="value"
          placeholder="Limit"
          class="mr-2"
        />
      </template>
      <template #end>
        <Button
          icon="pi pi-refresh"
          @click="fetchLogs"
          :loading="loading"
        />
      </template>
    </Toolbar>

    <!-- Logs DataTable -->
    <DataTable
      :value="logs"
      :loading="loading"
      responsive-layout="scroll"
      striped-rows
    >
      <Column field="level" header="Level" :style="{ width: '100px' }">
        <template #body="{ data }">
          <Tag
            :value="data.level || 'INFO'"
            :severity="getSeverity(data.level)"
          />
        </template>
      </Column>
      <Column field="message" header="Message" />
      <Column field="agent_name" header="Agent" :style="{ width: '150px' }" />
      <Column field="timestamp" header="Time" :style="{ width: '150px' }">
        <template #body="{ data }">
          {{ formatTime(data.timestamp) }}
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { logsAPI } from '@/api'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import Toolbar from 'primevue/toolbar'
import Tag from 'primevue/tag'

const logType = ref('agent')
const logLimit = ref(100)
const logs = ref([])
const loading = ref(false)

const logTypeOptions = [
  { label: '🤖 Agent Activity', value: 'agent' },
  { label: '📋 Audit Trail', value: 'audit' },
]

const logLimitOptions = [
  { label: 'Last 50', value: 50 },
  { label: 'Last 100', value: 100 },
  { label: 'Last 200', value: 200 },
  { label: 'Last 500', value: 500 },
]

onMounted(async () => {
  await fetchLogs()
})

async function fetchLogs() {
  loading.value = true
  try {
    const response = await logsAPI.list(logType.value, logLimit.value)
    logs.value = response.data || []
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  } finally {
    loading.value = false
  }
}

function formatTime(timestamp) {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp)
  return date.toLocaleString()
}

function getSeverity(level) {
  const severities = {
    'error': 'danger',
    'warning': 'warning',
    'info': 'info',
    'success': 'success',
  }
  return severities[level?.toLowerCase()] || 'info'
}
</script>


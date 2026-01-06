<template>
  <div class="page-container">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-secondary-900">Logs d'audit</h1>
      <p class="text-gray-500 mt-1">Historique des actions administratives</p>
    </div>

    <!-- Filters -->
    <Card class="mb-6 shadow-sm">
      <template #content>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <!-- Search -->
          <div class="lg:col-span-1">
            <label class="block text-sm font-medium text-gray-700 mb-1">Rechercher</label>
            <InputText
              v-model="filters.search"
              placeholder="Nom ressource..."
              class="w-full"
              @input="onFilterChange"
            />
          </div>

          <!-- Action Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Action</label>
            <Select
              v-model="filters.action"
              :options="actionOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Toutes"
              class="w-full"
              showClear
              @change="onFilterChange"
            />
          </div>

          <!-- Resource Type Filter -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <Select
              v-model="filters.resource_type"
              :options="resourceTypeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Tous"
              class="w-full"
              showClear
              @change="onFilterChange"
            />
          </div>

          <!-- Date From -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Du</label>
            <DatePicker
              v-model="filters.date_from"
              dateFormat="dd/mm/yy"
              placeholder="Date debut"
              class="w-full"
              showIcon
              @date-select="onFilterChange"
            />
          </div>

          <!-- Date To -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Au</label>
            <DatePicker
              v-model="filters.date_to"
              dateFormat="dd/mm/yy"
              placeholder="Date fin"
              class="w-full"
              showIcon
              @date-select="onFilterChange"
            />
          </div>
        </div>
      </template>
    </Card>

    <!-- Data Table -->
    <Card class="shadow-sm">
      <template #content>
        <DataTable
          :value="logs"
          :loading="isLoading"
          :rows="rowsPerPage"
          :totalRecords="total"
          :lazy="true"
          :paginator="true"
          :rowsPerPageOptions="[10, 20, 50]"
          dataKey="id"
          stripedRows
          paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
          :pt="{ root: { class: 'border-0' } }"
          @page="onPage"
        >
          <template #empty>
            <div class="text-center py-8 text-gray-500">
              <i class="pi pi-history text-4xl mb-3 block" />
              <p>Aucun log trouve</p>
            </div>
          </template>

          <!-- Date Column -->
          <Column field="created_at" header="Date" sortable style="min-width: 150px">
            <template #body="{ data }">
              <span class="text-sm">{{ formatDateTime(data.created_at) }}</span>
            </template>
          </Column>

          <!-- Admin Column -->
          <Column field="admin_email" header="Admin" style="min-width: 180px">
            <template #body="{ data }">
              <span class="text-sm font-medium">{{ data.admin_email || 'Systeme' }}</span>
            </template>
          </Column>

          <!-- Action Column -->
          <Column field="action" header="Action" style="min-width: 120px">
            <template #body="{ data }">
              <Tag :value="actionLabel(data.action)" :severity="actionSeverity(data.action)" />
            </template>
          </Column>

          <!-- Resource Type Column -->
          <Column field="resource_type" header="Type" style="min-width: 100px">
            <template #body="{ data }">
              <span class="text-sm capitalize">{{ resourceTypeLabel(data.resource_type) }}</span>
            </template>
          </Column>

          <!-- Resource Name Column -->
          <Column field="resource_name" header="Ressource" style="min-width: 200px">
            <template #body="{ data }">
              <div>
                <span class="text-sm font-medium">{{ data.resource_name || '-' }}</span>
                <span v-if="data.resource_id" class="text-xs text-gray-400 ml-1">
                  (ID: {{ data.resource_id }})
                </span>
              </div>
            </template>
          </Column>

          <!-- Details Column -->
          <Column header="Details" style="min-width: 200px">
            <template #body="{ data }">
              <div v-if="data.details" class="text-xs">
                <template v-if="data.details.changed">
                  <span
                    v-for="(value, key) in data.details.changed"
                    :key="key"
                    class="inline-block bg-blue-100 text-blue-700 px-2 py-0.5 rounded mr-1 mb-1"
                  >
                    {{ key }}: {{ formatValue(value) }}
                  </span>
                </template>
                <template v-else-if="data.details.is_active !== undefined">
                  <span :class="data.details.is_active ? 'text-green-600' : 'text-red-600'">
                    {{ data.details.is_active ? 'Active' : 'Desactive' }}
                  </span>
                </template>
                <template v-else-if="data.details.unlocked">
                  <span class="text-green-600">Deverrouille</span>
                </template>
                <template v-else-if="data.details.hard_delete">
                  <span class="text-red-600">Suppression definitive</span>
                </template>
                <template v-else>
                  <span class="text-gray-400">-</span>
                </template>
              </div>
              <span v-else class="text-gray-400">-</span>
            </template>
          </Column>

          <!-- IP Column -->
          <Column field="ip_address" header="IP" style="min-width: 120px">
            <template #body="{ data }">
              <span class="text-xs text-gray-500 font-mono">{{ data.ip_address || '-' }}</span>
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import DatePicker from 'primevue/datepicker'
import Tag from 'primevue/tag'
import { useAdminAuditLogs } from '~/composables/useAdminAuditLogs'
import { formatDateTime } from '~/utils/formatters'
import { adminLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard',
  middleware: ['admin'],
})

// Composable
const { logs, total, isLoading, fetchLogs } = useAdminAuditLogs()

// Filter state
const filters = ref({
  search: '',
  action: null as string | null,
  resource_type: null as string | null,
  date_from: null as Date | null,
  date_to: null as Date | null,
})

const rowsPerPage = ref(20)
const currentPage = ref(0)

// Filter options
const actionOptions = [
  { label: 'Creation', value: 'CREATE' },
  { label: 'Modification', value: 'UPDATE' },
  { label: 'Suppression', value: 'DELETE' },
  { label: 'Activation/Desactivation', value: 'TOGGLE_ACTIVE' },
  { label: 'Deverrouillage', value: 'UNLOCK' },
]

const resourceTypeOptions = [
  { label: 'Utilisateur', value: 'user' },
  { label: 'Marque', value: 'brand' },
  { label: 'Categorie', value: 'category' },
  { label: 'Couleur', value: 'color' },
  { label: 'Matiere', value: 'material' },
]

// Debounced filter change
let filterTimeout: ReturnType<typeof setTimeout> | null = null
const onFilterChange = () => {
  if (filterTimeout) clearTimeout(filterTimeout)
  filterTimeout = setTimeout(() => {
    currentPage.value = 0
    loadLogs()
  }, 300)
}

// Page change handler
const onPage = (event: { first: number; rows: number }) => {
  currentPage.value = event.first / event.rows
  rowsPerPage.value = event.rows
  loadLogs()
}

// Load logs with current filters
const loadLogs = async () => {
  try {
    await fetchLogs({
      skip: currentPage.value * rowsPerPage.value,
      limit: rowsPerPage.value,
      action: filters.value.action || undefined,
      resource_type: filters.value.resource_type || undefined,
      date_from: filters.value.date_from?.toISOString() || undefined,
      date_to: filters.value.date_to?.toISOString() || undefined,
      search: filters.value.search || undefined,
    })
  } catch (e) {
    adminLogger.error('Failed to load audit logs', { error: e })
  }
}

// Initial load
onMounted(() => {
  loadLogs()
})


const actionLabel = (action: string): string => {
  const labels: Record<string, string> = {
    CREATE: 'Creation',
    UPDATE: 'Modification',
    DELETE: 'Suppression',
    TOGGLE_ACTIVE: 'Toggle',
    UNLOCK: 'Deverrouillage',
  }
  return labels[action] || action
}

const actionSeverity = (action: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' => {
  const severities: Record<string, 'success' | 'info' | 'warn' | 'danger' | 'secondary'> = {
    CREATE: 'success',
    UPDATE: 'info',
    DELETE: 'danger',
    TOGGLE_ACTIVE: 'warn',
    UNLOCK: 'secondary',
  }
  return severities[action] || 'secondary'
}

const resourceTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    user: 'Utilisateur',
    brand: 'Marque',
    category: 'Categorie',
    color: 'Couleur',
    material: 'Matiere',
  }
  return labels[type] || type
}

const formatValue = (value: any): string => {
  if (typeof value === 'boolean') return value ? 'Oui' : 'Non'
  if (typeof value === 'string' && value.length > 30) return value.substring(0, 30) + '...'
  return String(value)
}
</script>

<style scoped>
.page-container {
  @apply p-6 lg:p-8;
}
</style>

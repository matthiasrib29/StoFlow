<template>
  <div class="p-4 lg:p-8">
    <PageHeader
      title="Tâches"
      subtitle="Suivez l'exécution de vos tâches en temps réel"
    >
      <template #actions>
        <Button
          label="Actualiser"
          icon="pi pi-refresh"
          class="border border-gray-300 bg-white hover:bg-gray-50 text-gray-700"
          :loading="isLoading"
          @click="fetchTasks"
        />
      </template>
    </PageHeader>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <Card class="shadow-sm border border-gray-100">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
              <i class="pi pi-clock text-blue-600 text-xl"></i>
            </div>
            <div>
              <p class="text-2xl font-bold text-secondary-900">{{ stats.by_status?.PENDING || 0 }}</p>
              <p class="text-sm text-gray-500">En attente</p>
            </div>
          </div>
        </template>
      </Card>

      <Card class="shadow-sm border border-gray-100">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-yellow-100 flex items-center justify-center">
              <i class="pi pi-spin pi-spinner text-yellow-600 text-xl"></i>
            </div>
            <div>
              <p class="text-2xl font-bold text-secondary-900">{{ stats.by_status?.STARTED || 0 }}</p>
              <p class="text-sm text-gray-500">En cours</p>
            </div>
          </div>
        </template>
      </Card>

      <Card class="shadow-sm border border-gray-100">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
              <i class="pi pi-check text-green-600 text-xl"></i>
            </div>
            <div>
              <p class="text-2xl font-bold text-secondary-900">{{ stats.by_status?.SUCCESS || 0 }}</p>
              <p class="text-sm text-gray-500">Réussies</p>
            </div>
          </div>
        </template>
      </Card>

      <Card class="shadow-sm border border-gray-100">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
              <i class="pi pi-times text-red-600 text-xl"></i>
            </div>
            <div>
              <p class="text-2xl font-bold text-secondary-900">{{ stats.by_status?.FAILURE || 0 }}</p>
              <p class="text-sm text-gray-500">Échouées</p>
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Filters -->
    <Card class="shadow-sm border border-gray-100 mb-6">
      <template #content>
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex-1 min-w-[200px]">
            <Select
              v-model="filters.status"
              :options="statusOptions"
              option-label="label"
              option-value="value"
              placeholder="Tous les statuts"
              class="w-full"
              show-clear
            />
          </div>
          <div class="flex-1 min-w-[200px]">
            <Select
              v-model="filters.marketplace"
              :options="marketplaceOptions"
              option-label="label"
              option-value="value"
              placeholder="Toutes les plateformes"
              class="w-full"
              show-clear
            />
          </div>
          <div class="flex-1 min-w-[200px]">
            <Select
              v-model="filters.action"
              :options="actionOptions"
              option-label="label"
              option-value="value"
              placeholder="Toutes les actions"
              class="w-full"
              show-clear
            />
          </div>
        </div>
      </template>
    </Card>

    <!-- Tasks Table -->
    <Card class="shadow-sm border border-gray-100">
      <template #content>
        <DataTable
          :value="tasks"
          :loading="isLoading"
          :paginator="true"
          :rows="20"
          :rows-per-page-options="[10, 20, 50]"
          :total-records="totalTasks"
          data-key="id"
          striped-rows
          responsive-layout="scroll"
          class="p-datatable-sm"
        >
          <Column field="id" header="ID" :sortable="true" style="width: 120px">
            <template #body="{ data }">
              <span class="font-mono text-xs text-gray-500">{{ data.id.substring(0, 8) }}...</span>
            </template>
          </Column>

          <Column field="marketplace" header="Plateforme" :sortable="true" style="width: 120px">
            <template #body="{ data }">
              <Tag
                v-if="data.marketplace"
                :severity="getMarketplaceSeverity(data.marketplace)"
                :value="data.marketplace"
              />
              <span v-else class="text-gray-400">-</span>
            </template>
          </Column>

          <Column field="action_code" header="Action" :sortable="true" style="width: 120px">
            <template #body="{ data }">
              <span v-if="data.action_code" class="capitalize">{{ data.action_code }}</span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </Column>

          <Column field="status" header="Statut" :sortable="true" style="width: 120px">
            <template #body="{ data }">
              <Tag :severity="getStatusSeverity(data.status)" :value="getStatusLabel(data.status)" />
            </template>
          </Column>

          <Column field="product_id" header="Produit" :sortable="true" style="width: 100px">
            <template #body="{ data }">
              <NuxtLink
                v-if="data.product_id"
                :to="`/dashboard/products/${data.product_id}`"
                class="text-primary-600 hover:underline"
              >
                #{{ data.product_id }}
              </NuxtLink>
              <span v-else class="text-gray-400">-</span>
            </template>
          </Column>

          <Column field="created_at" header="Créée" :sortable="true" style="width: 150px">
            <template #body="{ data }">
              <span class="text-sm">{{ formatDate(data.created_at) }}</span>
            </template>
          </Column>

          <Column field="runtime_seconds" header="Durée" style="width: 100px">
            <template #body="{ data }">
              <span v-if="data.runtime_seconds" class="text-sm">
                {{ formatDuration(data.runtime_seconds) }}
              </span>
              <span v-else-if="data.status === 'STARTED'" class="text-yellow-600">
                <i class="pi pi-spin pi-spinner mr-1"></i>
                En cours...
              </span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </Column>

          <Column field="retries" header="Essais" style="width: 80px">
            <template #body="{ data }">
              <span :class="data.retries > 0 ? 'text-orange-600' : 'text-gray-500'">
                {{ data.retries }}/{{ data.max_retries }}
              </span>
            </template>
          </Column>

          <Column header="Actions" style="width: 100px">
            <template #body="{ data }">
              <div class="flex gap-2">
                <Button
                  v-if="data.status === 'PENDING' || data.status === 'STARTED'"
                  icon="pi pi-times"
                  severity="danger"
                  text
                  rounded
                  size="small"
                  v-tooltip.top="'Annuler'"
                  @click="revokeTask(data.id)"
                />
                <Button
                  v-if="data.error"
                  icon="pi pi-info-circle"
                  severity="info"
                  text
                  rounded
                  size="small"
                  v-tooltip.top="'Voir l\'erreur'"
                  @click="showError(data)"
                />
              </div>
            </template>
          </Column>

          <template #empty>
            <div class="text-center py-8 text-gray-500">
              <i class="pi pi-inbox text-4xl mb-4 text-gray-300"></i>
              <p>Aucune tâche trouvée</p>
            </div>
          </template>
        </DataTable>
      </template>
    </Card>

    <!-- Error Dialog -->
    <Dialog
      v-model:visible="errorDialogVisible"
      header="Détails de l'erreur"
      :style="{ width: '500px' }"
      modal
    >
      <div v-if="selectedTask">
        <div class="mb-4">
          <p class="text-sm text-gray-500 mb-1">Tâche</p>
          <p class="font-mono text-sm">{{ selectedTask.id }}</p>
        </div>
        <div class="mb-4">
          <p class="text-sm text-gray-500 mb-1">Message d'erreur</p>
          <p class="text-red-600 bg-red-50 p-3 rounded-lg">{{ selectedTask.error }}</p>
        </div>
      </div>
      <template #footer>
        <Button label="Fermer" @click="errorDialogVisible = false" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

definePageMeta({
  layout: 'dashboard'
})

interface Task {
  id: string
  name: string
  status: string
  marketplace: string | null
  action_code: string | null
  product_id: number | null
  result: Record<string, any> | null
  error: string | null
  retries: number
  max_retries: number
  worker: string | null
  queue: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  runtime_seconds: number | null
}

interface TaskStats {
  period_days: number
  by_status: Record<string, number>
  by_marketplace: Record<string, number>
  avg_runtime_seconds: number | null
  total: number
}

// State
const tasks = ref<Task[]>([])
const totalTasks = ref(0)
const stats = ref<TaskStats>({
  period_days: 7,
  by_status: {},
  by_marketplace: {},
  avg_runtime_seconds: null,
  total: 0
})
const isLoading = ref(false)
const errorDialogVisible = ref(false)
const selectedTask = ref<Task | null>(null)

// Filters
const filters = ref({
  status: null as string | null,
  marketplace: null as string | null,
  action: null as string | null
})

const statusOptions = [
  { label: 'En attente', value: 'PENDING' },
  { label: 'En cours', value: 'STARTED' },
  { label: 'Réussie', value: 'SUCCESS' },
  { label: 'Échouée', value: 'FAILURE' },
  { label: 'Nouvelle tentative', value: 'RETRY' },
  { label: 'Annulée', value: 'REVOKED' }
]

const marketplaceOptions = [
  { label: 'Vinted', value: 'vinted' },
  { label: 'eBay', value: 'ebay' },
  { label: 'Etsy', value: 'etsy' }
]

const actionOptions = [
  { label: 'Publication', value: 'publish' },
  { label: 'Mise à jour', value: 'update' },
  { label: 'Suppression', value: 'delete' },
  { label: 'Synchronisation', value: 'sync' },
  { label: 'Commandes', value: 'sync_orders' }
]

// API calls
const { $api } = useNuxtApp()

async function fetchTasks() {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.status) params.append('status', filters.value.status)
    if (filters.value.marketplace) params.append('marketplace', filters.value.marketplace)
    if (filters.value.action) params.append('action_code', filters.value.action)
    params.append('limit', '50')

    const response = await $api(`/api/tasks?${params.toString()}`)
    tasks.value = response.tasks
    totalTasks.value = response.total
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
  } finally {
    isLoading.value = false
  }
}

async function fetchStats() {
  try {
    const response = await $api('/api/tasks/stats?days=7')
    stats.value = response
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

async function revokeTask(taskId: string) {
  try {
    await $api(`/api/tasks/${taskId}/revoke`, { method: 'POST' })
    await fetchTasks()
    await fetchStats()
  } catch (error) {
    console.error('Failed to revoke task:', error)
  }
}

// Helpers
function getStatusSeverity(status: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' {
  const map: Record<string, 'success' | 'info' | 'warn' | 'danger' | 'secondary'> = {
    PENDING: 'info',
    STARTED: 'warn',
    SUCCESS: 'success',
    FAILURE: 'danger',
    RETRY: 'warn',
    REVOKED: 'secondary'
  }
  return map[status] || 'secondary'
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    PENDING: 'En attente',
    STARTED: 'En cours',
    SUCCESS: 'Réussie',
    FAILURE: 'Échouée',
    RETRY: 'Nouvelle tentative',
    REVOKED: 'Annulée'
  }
  return map[status] || status
}

function getMarketplaceSeverity(marketplace: string): 'success' | 'info' | 'warn' {
  const map: Record<string, 'success' | 'info' | 'warn'> = {
    vinted: 'success',
    ebay: 'info',
    etsy: 'warn'
  }
  return map[marketplace] || 'info'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

function formatDuration(seconds: number): string {
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

function showError(task: Task) {
  selectedTask.value = task
  errorDialogVisible.value = true
}

// Auto-refresh
let refreshInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  fetchTasks()
  fetchStats()

  // Auto-refresh every 10 seconds
  refreshInterval = setInterval(() => {
    fetchTasks()
    fetchStats()
  }, 10000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

// Watch filters
watch(filters, () => {
  fetchTasks()
}, { deep: true })

// WebSocket updates
const { $socket } = useNuxtApp()

onMounted(() => {
  if ($socket) {
    $socket.on('task_completed', (data: any) => {
      fetchTasks()
      fetchStats()
    })
    $socket.on('task_failed', (data: any) => {
      fetchTasks()
      fetchStats()
    })
  }
})

onUnmounted(() => {
  if ($socket) {
    $socket.off('task_completed')
    $socket.off('task_failed')
  }
})
</script>

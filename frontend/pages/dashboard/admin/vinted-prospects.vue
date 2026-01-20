<template>
  <div class="page-container">
    <PageHeader
      title="Prospects Vinted"
      subtitle="Gestion des utilisateurs Vinted pour prospection"
    />

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <StatCard
        label="Total prospects"
        :value="stats?.total_prospects ?? 0"
        icon="pi pi-users"
        variant="primary"
        :loading="isLoadingStats"
      />
      <StatCard
        label="Nouveaux"
        :value="stats?.by_status?.new ?? 0"
        icon="pi pi-star"
        variant="info"
        :loading="isLoadingStats"
      />
      <StatCard
        label="Contactes"
        :value="stats?.by_status?.contacted ?? 0"
        icon="pi pi-send"
        variant="warning"
        :loading="isLoadingStats"
      />
      <StatCard
        label="Convertis"
        :value="stats?.by_status?.converted ?? 0"
        icon="pi pi-check-circle"
        variant="success"
        :loading="isLoadingStats"
      />
    </div>

    <!-- Actions Bar -->
    <Card class="shadow-sm mb-6">
      <template #content>
        <div class="flex flex-wrap items-center gap-4">
          <Button
            label="Lancer recherche"
            icon="pi pi-search"
            :loading="isFetching"
            @click="triggerFetch"
          />

          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">Pays:</label>
            <Select
              v-model="filters.country_code"
              :options="countryOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Tous"
              class="w-24"
              @change="fetchProspects"
            />
          </div>

          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">Statut:</label>
            <Select
              v-model="filters.status"
              :options="statusOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Tous"
              class="w-32"
              @change="fetchProspects"
            />
          </div>

          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">Min articles:</label>
            <InputNumber
              v-model="filters.min_items"
              :min="0"
              :max="10000"
              class="w-24"
              @update:modelValue="debouncedFetch"
            />
          </div>

          <div class="flex items-center gap-2 ml-auto">
            <InputText
              v-model="filters.search"
              placeholder="Rechercher login..."
              class="w-48"
              @input="debouncedFetch"
            />
          </div>
        </div>
      </template>
    </Card>

    <!-- Prospects Table -->
    <Card class="shadow-sm">
      <template #content>
        <DataTable
          :value="prospects"
          :loading="isLoading"
          :rows="50"
          :totalRecords="total"
          lazy
          paginator
          :first="skip"
          @page="onPage"
          dataKey="id"
          stripedRows
          class="p-datatable-sm"
        >
          <Column field="login" header="Login" sortable>
            <template #body="{ data }">
              <a
                :href="data.profile_url"
                target="_blank"
                class="text-primary-600 hover:underline font-medium"
              >
                {{ data.login }}
              </a>
            </template>
          </Column>

          <Column field="country_code" header="Pays" sortable style="width: 80px">
            <template #body="{ data }">
              <Tag :value="data.country_code || '?'" severity="secondary" />
            </template>
          </Column>

          <Column field="item_count" header="Articles" sortable style="width: 100px">
            <template #body="{ data }">
              <span class="font-semibold text-primary-600">{{ data.item_count }}</span>
            </template>
          </Column>

          <Column field="feedback_count" header="Avis" sortable style="width: 80px" />

          <Column field="feedback_reputation" header="Rep." sortable style="width: 80px">
            <template #body="{ data }">
              <span v-if="data.feedback_reputation" class="flex items-center gap-1">
                <i class="pi pi-star-fill text-yellow-400 text-xs" />
                {{ Number(data.feedback_reputation).toFixed(1) }}
              </span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </Column>

          <Column field="is_business" header="Pro" style="width: 60px">
            <template #body="{ data }">
              <i v-if="data.is_business" class="pi pi-check text-green-500" />
              <i v-else class="pi pi-times text-gray-300" />
            </template>
          </Column>

          <Column field="status" header="Statut" style="width: 120px">
            <template #body="{ data }">
              <Tag
                :value="statusLabels[data.status]"
                :severity="statusSeverity[data.status]"
              />
            </template>
          </Column>

          <Column field="discovered_at" header="Decouvert" style="width: 120px">
            <template #body="{ data }">
              <span class="text-sm text-gray-500">
                {{ formatDate(data.discovered_at) }}
              </span>
            </template>
          </Column>

          <Column header="Actions" style="width: 150px">
            <template #body="{ data }">
              <div class="flex gap-2">
                <Button
                  v-if="data.status === 'new'"
                  icon="pi pi-send"
                  size="small"
                  severity="info"
                  text
                  title="Marquer comme contacte"
                  @click="updateStatus(data.id, 'contacted')"
                />
                <Button
                  v-if="data.status === 'contacted'"
                  icon="pi pi-check"
                  size="small"
                  severity="success"
                  text
                  title="Marquer comme converti"
                  @click="updateStatus(data.id, 'converted')"
                />
                <Button
                  icon="pi pi-eye-slash"
                  size="small"
                  severity="secondary"
                  text
                  title="Ignorer"
                  @click="updateStatus(data.id, 'ignored')"
                />
                <Button
                  icon="pi pi-trash"
                  size="small"
                  severity="danger"
                  text
                  title="Supprimer"
                  @click="deleteProspect(data.id)"
                />
              </div>
            </template>
          </Column>

          <template #empty>
            <div class="text-center py-8 text-gray-500">
              <i class="pi pi-inbox text-4xl mb-4 block" />
              <p>Aucun prospect trouve</p>
              <p class="text-sm mt-2">Lancez une recherche pour decouvrir des vendeurs Vinted</p>
            </div>
          </template>
        </DataTable>
      </template>
    </Card>

    <!-- Fetch Job Dialog -->
    <Dialog
      v-model:visible="showFetchDialog"
      header="Lancer recherche de prospects"
      :style="{ width: '450px' }"
      modal
    >
      <div class="space-y-4">
        <div class="field">
          <label class="block text-sm font-medium mb-2">Pays cible</label>
          <Select
            v-model="fetchParams.country_code"
            :options="countryOptions.filter(c => c.value)"
            optionLabel="label"
            optionValue="value"
            class="w-full"
          />
        </div>

        <div class="field">
          <label class="block text-sm font-medium mb-2">Minimum d'articles</label>
          <InputNumber
            v-model="fetchParams.min_items"
            :min="50"
            :max="5000"
            class="w-full"
          />
          <small class="text-gray-500">Filtrer les vendeurs avec au moins X articles</small>
        </div>

        <div class="field">
          <label class="block text-sm font-medium mb-2">Pages par lettre</label>
          <InputNumber
            v-model="fetchParams.max_pages_per_search"
            :min="1"
            :max="100"
            class="w-full"
          />
          <small class="text-gray-500">Max pages de resultats par caractere (A-Z)</small>
        </div>
      </div>

      <template #footer>
        <Button label="Annuler" text @click="showFetchDialog = false" />
        <Button
          label="Lancer"
          icon="pi pi-search"
          :loading="isFetching"
          @click="confirmFetch"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { useToast } from 'primevue/usetoast'
import { useDebounceFn } from '@vueuse/core'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import StatCard from '~/components/admin/StatCard.vue'
import { useAuthStore } from '~/stores/auth'
import { adminLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard',
  middleware: ['admin'],
})

const toast = useToast()
const config = useRuntimeConfig()
const authStore = useAuthStore()

// State
const prospects = ref<any[]>([])
const total = ref(0)
const skip = ref(0)
const isLoading = ref(false)
const isLoadingStats = ref(false)
const isFetching = ref(false)
const showFetchDialog = ref(false)

const stats = ref<any>(null)

const filters = ref({
  status: null as string | null,
  country_code: null as string | null,
  min_items: null as number | null,
  search: '',
})

const fetchParams = ref({
  country_code: 'FR',
  min_items: 200,
  max_pages_per_search: 50,
})

// Options
const countryOptions = [
  { label: 'Tous', value: null },
  { label: 'France', value: 'FR' },
  { label: 'Allemagne', value: 'DE' },
  { label: 'Espagne', value: 'ES' },
  { label: 'Italie', value: 'IT' },
  { label: 'Belgique', value: 'BE' },
]

const statusOptions = [
  { label: 'Tous', value: null },
  { label: 'Nouveau', value: 'new' },
  { label: 'Contacte', value: 'contacted' },
  { label: 'Converti', value: 'converted' },
  { label: 'Ignore', value: 'ignored' },
]

const statusLabels: Record<string, string> = {
  new: 'Nouveau',
  contacted: 'Contacte',
  converted: 'Converti',
  ignored: 'Ignore',
}

const statusSeverity: Record<string, 'info' | 'warn' | 'success' | 'secondary'> = {
  new: 'info',
  contacted: 'warn',
  converted: 'success',
  ignored: 'secondary',
}

// API helpers
const apiUrl = computed(() => config.public.apiUrl || 'http://localhost:8000')

async function apiGet(path: string) {
  const response = await fetch(`${apiUrl.value}${path}`, {
    headers: { Authorization: `Bearer ${authStore.token}` },
  })
  if (!response.ok) throw new Error(`API error: ${response.status}`)
  return response.json()
}

async function apiPost(path: string, body?: any) {
  const response = await fetch(`${apiUrl.value}${path}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${authStore.token}`,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) throw new Error(`API error: ${response.status}`)
  return response.json()
}

async function apiPatch(path: string, body: any) {
  const response = await fetch(`${apiUrl.value}${path}`, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${authStore.token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(`API error: ${response.status}`)
  return response.json()
}

async function apiDelete(path: string) {
  const response = await fetch(`${apiUrl.value}${path}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${authStore.token}` },
  })
  if (!response.ok) throw new Error(`API error: ${response.status}`)
  return response.json()
}

// Fetch prospects
async function fetchProspects() {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', skip.value.toString())
    params.append('limit', '50')
    if (filters.value.status) params.append('status', filters.value.status)
    if (filters.value.country_code) params.append('country_code', filters.value.country_code)
    if (filters.value.min_items) params.append('min_items', filters.value.min_items.toString())
    if (filters.value.search) params.append('search', filters.value.search)

    const data = await apiGet(`/api/admin/vinted-prospects?${params}`)
    prospects.value = data.prospects
    total.value = data.total
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  } finally {
    isLoading.value = false
  }
}

// Fetch stats
async function fetchStats() {
  isLoadingStats.value = true
  try {
    stats.value = await apiGet('/api/admin/vinted-prospects/stats')
  } catch (e: any) {
    adminLogger.error('Failed to fetch stats:', e)
  } finally {
    isLoadingStats.value = false
  }
}

// Debounced fetch
const debouncedFetch = useDebounceFn(() => {
  skip.value = 0
  fetchProspects()
}, 500)

// Pagination
function onPage(event: any) {
  skip.value = event.first
  fetchProspects()
}

// Update status
async function updateStatus(prospectId: number, newStatus: string) {
  try {
    await apiPatch(`/api/admin/vinted-prospects/${prospectId}`, { status: newStatus })
    toast.add({ severity: 'success', summary: 'Succes', detail: 'Statut mis a jour', life: 2000 })
    fetchProspects()
    fetchStats()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  }
}

// Delete prospect
async function deleteProspect(prospectId: number) {
  if (!confirm('Supprimer ce prospect ?')) return

  try {
    await apiDelete(`/api/admin/vinted-prospects/${prospectId}`)
    toast.add({ severity: 'success', summary: 'Succes', detail: 'Prospect supprime', life: 2000 })
    fetchProspects()
    fetchStats()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  }
}

// Trigger fetch job
function triggerFetch() {
  showFetchDialog.value = true
}

async function confirmFetch() {
  isFetching.value = true
  try {
    const result = await apiPost('/api/admin/vinted-prospects/fetch', fetchParams.value)
    toast.add({
      severity: 'success',
      summary: 'Job cree',
      detail: `Job #${result.job_id} lance. ${result.message}`,
      life: 5000,
    })
    showFetchDialog.value = false
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  } finally {
    isFetching.value = false
  }
}

// Format date
function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  })
}

// Init
onMounted(() => {
  fetchProspects()
  fetchStats()
})
</script>

<style scoped>
.page-container {
  @apply p-6 lg:p-8;
}

.field {
  @apply mb-4;
}
</style>

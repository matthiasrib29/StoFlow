<template>
  <div class="page-container">
    <PageHeader
      title="Vendeurs Pro Vinted"
      subtitle="Scan et gestion des vendeurs professionnels Vinted"
    />

    <!-- Scan Control Card -->
    <Card class="shadow-sm mb-6 border border-gray-100">
      <template #content>
        <div class="flex flex-wrap items-center gap-4">
          <Button
            v-if="!scanProgress || ['completed', 'failed', 'cancelled'].includes(scanProgress.status)"
            label="Lancer Scan"
            icon="pi pi-play"
            @click="showScanDialog = true"
          />

          <template v-if="scanProgress && !['completed', 'failed', 'cancelled'].includes(scanProgress.status)">
            <Button
              v-if="scanProgress.status === 'running'"
              label="Pause"
              icon="pi pi-pause"
              severity="warn"
              @click="pauseScan"
            />
            <Button
              v-if="scanProgress.status === 'paused'"
              label="Reprendre"
              icon="pi pi-play"
              severity="success"
              @click="resumeScan"
            />
            <Button
              label="Annuler"
              icon="pi pi-times"
              severity="danger"
              outlined
              @click="cancelScan"
            />
          </template>

          <!-- Progress info -->
          <div v-if="scanProgress && !['completed', 'failed', 'cancelled'].includes(scanProgress.status)" class="flex-1 min-w-[300px]">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm text-gray-600">
                Lettre en cours : <strong>{{ scanProgress.current_letter || '...' }}</strong>
                — Page {{ scanProgress.current_page }}
              </span>
              <span class="text-sm text-gray-500">
                {{ scanProgress.letters_completed }}/{{ scanProgress.total_letters }} lettres
              </span>
            </div>
            <ProgressBar
              :value="scanProgressPercent"
              :showValue="true"
              style="height: 8px"
            />
            <div class="flex gap-4 mt-1 text-xs text-gray-500">
              <span>{{ scanProgress.total_saved }} sauvegardés</span>
              <span>{{ scanProgress.total_updated }} mis à jour</span>
              <span v-if="scanProgress.total_errors" class="text-red-500">{{ scanProgress.total_errors }} erreurs</span>
            </div>
          </div>

          <!-- Completed / Failed status -->
          <div v-if="scanProgress?.status === 'completed'" class="flex items-center gap-2 text-green-600">
            <i class="pi pi-check-circle" />
            <span class="text-sm font-medium">Scan terminé — {{ scanProgress.total_saved }} sauvegardés</span>
          </div>
          <div v-if="scanProgress?.status === 'failed'" class="flex items-center gap-2 text-red-600">
            <i class="pi pi-times-circle" />
            <span class="text-sm font-medium">Scan échoué</span>
          </div>
          <div v-if="scanProgress?.status === 'cancelled'" class="flex items-center gap-2 text-gray-500">
            <i class="pi pi-ban" />
            <span class="text-sm font-medium">Scan annulé</span>
          </div>
        </div>
      </template>
    </Card>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <StatCard
        label="Total vendeurs"
        :value="stats?.total_sellers ?? 0"
        icon="pi pi-users"
        variant="primary"
        :loading="isLoadingStats"
      />
      <StatCard
        label="Nouveaux"
        :value="stats?.by_status?.new ?? 0"
        icon="pi pi-star"
        variant="warning"
        :loading="isLoadingStats"
      />
      <StatCard
        label="Avec Email"
        :value="stats?.with_email ?? 0"
        icon="pi pi-envelope"
        variant="success"
        :loading="isLoadingStats"
      />
      <StatCard
        label="Avec Instagram"
        :value="stats?.with_instagram ?? 0"
        icon="pi pi-instagram"
        variant="default"
        :loading="isLoadingStats"
      />
    </div>

    <!-- Filters Card -->
    <Card class="shadow-sm mb-6">
      <template #content>
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">Statut:</label>
            <Select
              v-model="filters.status"
              :options="statusOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Tous"
              class="w-32"
              @change="resetAndFetch"
            />
          </div>

          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">Pays:</label>
            <Select
              v-model="filters.country_code"
              :options="countryOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Tous"
              class="w-28"
              @change="resetAndFetch"
            />
          </div>

          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">Marketplace:</label>
            <Select
              v-model="filters.marketplace"
              :options="marketplaceOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Toutes"
              class="w-36"
              @change="resetAndFetch"
            />
          </div>

          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">Min articles:</label>
            <InputNumber
              v-model="filters.min_items"
              :min="0"
              :max="50000"
              class="w-24"
              @update:modelValue="debouncedFetch"
            />
          </div>

          <div class="flex items-center gap-2">
            <Checkbox
              v-model="filters.has_email"
              :binary="true"
              inputId="hasEmail"
              @change="resetAndFetch"
            />
            <label for="hasEmail" class="text-sm text-gray-600 cursor-pointer">Email</label>
          </div>

          <div class="flex items-center gap-2">
            <Checkbox
              v-model="filters.has_instagram"
              :binary="true"
              inputId="hasInstagram"
              @change="resetAndFetch"
            />
            <label for="hasInstagram" class="text-sm text-gray-600 cursor-pointer">Instagram</label>
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

    <!-- Bulk Actions -->
    <div v-if="selectedSellers.length > 0" class="mb-4 flex items-center gap-3 p-3 bg-primary-50 rounded-lg">
      <span class="text-sm font-medium text-primary-700">{{ selectedSellers.length }} sélectionné(s)</span>
      <Select
        v-model="bulkStatus"
        :options="statusOptions.filter(o => o.value)"
        optionLabel="label"
        optionValue="value"
        placeholder="Changer statut"
        class="w-36"
      />
      <Button
        label="Appliquer"
        icon="pi pi-check"
        size="small"
        :disabled="!bulkStatus"
        @click="applyBulkUpdate"
      />
    </div>

    <!-- DataTable -->
    <Card class="shadow-sm">
      <template #content>
        <DataTable
          v-model:selection="selectedSellers"
          :value="sellers"
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
          <Column selectionMode="multiple" headerStyle="width: 3rem" />

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

          <Column field="business_name" header="Entreprise">
            <template #body="{ data }">
              <span class="text-sm">{{ data.business_name || '-' }}</span>
            </template>
          </Column>

          <Column field="item_count" header="Articles" sortable style="width: 90px">
            <template #body="{ data }">
              <span class="font-semibold text-primary-600">{{ data.item_count }}</span>
            </template>
          </Column>

          <Column field="feedback_reputation" header="Rep." sortable style="width: 80px">
            <template #body="{ data }">
              <span v-if="data.feedback_reputation" class="flex items-center gap-1">
                <i class="pi pi-star-fill text-yellow-400 text-xs" />
                {{ Number(data.feedback_reputation).toFixed(1) }}
              </span>
              <span v-else class="text-gray-400">-</span>
            </template>
          </Column>

          <Column field="legal_code" header="SIRET" style="width: 130px">
            <template #body="{ data }">
              <span class="text-xs font-mono">{{ data.legal_code || '-' }}</span>
            </template>
          </Column>

          <Column header="Email" style="width: 60px">
            <template #body="{ data }">
              <a
                v-if="data.contact_email"
                :href="`mailto:${data.contact_email}`"
                class="text-primary-600 hover:text-primary-800"
                :title="data.contact_email"
              >
                <i class="pi pi-envelope" />
              </a>
              <span v-else class="text-gray-300">-</span>
            </template>
          </Column>

          <Column header="Insta" style="width: 60px">
            <template #body="{ data }">
              <a
                v-if="data.contact_instagram"
                :href="`https://instagram.com/${data.contact_instagram}`"
                target="_blank"
                class="text-pink-500 hover:text-pink-700"
                :title="data.contact_instagram"
              >
                <i class="pi pi-instagram" />
              </a>
              <span v-else class="text-gray-300">-</span>
            </template>
          </Column>

          <Column header="TikTok" style="width: 60px">
            <template #body="{ data }">
              <a
                v-if="data.contact_tiktok"
                :href="`https://tiktok.com/@${data.contact_tiktok}`"
                target="_blank"
                class="text-gray-700 hover:text-gray-900"
                :title="data.contact_tiktok"
              >
                <i class="pi pi-video" />
              </a>
              <span v-else class="text-gray-300">-</span>
            </template>
          </Column>

          <Column header="Tel" style="width: 60px">
            <template #body="{ data }">
              <a
                v-if="data.contact_phone"
                :href="`tel:${data.contact_phone}`"
                class="text-green-600 hover:text-green-800"
                :title="data.contact_phone"
              >
                <i class="pi pi-phone" />
              </a>
              <span v-else class="text-gray-300">-</span>
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

          <Column field="discovered_at" header="Découvert" style="width: 100px">
            <template #body="{ data }">
              <span class="text-sm text-gray-500">
                {{ formatDate(data.discovered_at) }}
              </span>
            </template>
          </Column>

          <Column header="Actions" style="width: 120px">
            <template #body="{ data }">
              <div class="flex gap-1">
                <Button
                  v-if="data.status === 'new'"
                  icon="pi pi-send"
                  size="small"
                  severity="info"
                  text
                  title="Marquer contacté"
                  @click="updateStatus(data.id, 'contacted')"
                />
                <Button
                  v-if="data.status === 'contacted'"
                  icon="pi pi-check"
                  size="small"
                  severity="success"
                  text
                  title="Marquer converti"
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
                  @click="deleteSeller(data.id)"
                />
              </div>
            </template>
          </Column>

          <template #empty>
            <div class="text-center py-8 text-gray-500">
              <i class="pi pi-inbox text-4xl mb-4 block" />
              <p>Aucun vendeur pro trouvé</p>
              <p class="text-sm mt-2">Lancez un scan pour découvrir des vendeurs professionnels Vinted</p>
            </div>
          </template>
        </DataTable>
      </template>
    </Card>

    <!-- Scan Config Dialog -->
    <Dialog
      v-model:visible="showScanDialog"
      header="Configurer le scan"
      :style="{ width: '450px' }"
      modal
    >
      <div class="space-y-4">
        <div class="field">
          <label class="block text-sm font-medium mb-2">Scope de recherche</label>
          <InputText
            v-model="scanParams.search_scope_text"
            class="w-full"
            placeholder="a,b,c,...,z (par défaut A-Z)"
          />
          <small class="text-gray-500">Lettres séparées par des virgules. Laisser vide pour A-Z complet.</small>
        </div>

        <div class="field">
          <label class="block text-sm font-medium mb-2">Marketplace</label>
          <Select
            v-model="scanParams.marketplace"
            :options="marketplaceOptions.filter(o => o.value)"
            optionLabel="label"
            optionValue="value"
            class="w-full"
          />
        </div>

        <div class="field">
          <label class="block text-sm font-medium mb-2">Résultats par page</label>
          <InputNumber
            v-model="scanParams.per_page"
            :min="1"
            :max="100"
            class="w-full"
          />
          <small class="text-gray-500">Nombre de résultats par page Vinted (max 100)</small>
        </div>
      </div>

      <template #footer>
        <Button label="Annuler" text @click="showScanDialog = false" />
        <Button
          label="Lancer"
          icon="pi pi-play"
          :loading="isStartingScan"
          @click="startScan"
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
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import ProgressBar from 'primevue/progressbar'
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

// --- State ---
const sellers = ref<any[]>([])
const selectedSellers = ref<any[]>([])
const total = ref(0)
const skip = ref(0)
const isLoading = ref(false)
const isLoadingStats = ref(false)
const isStartingScan = ref(false)
const showScanDialog = ref(false)
const bulkStatus = ref<string | null>(null)

const stats = ref<any>(null)

const filters = ref({
  status: null as string | null,
  country_code: null as string | null,
  marketplace: null as string | null,
  min_items: null as number | null,
  has_email: false,
  has_instagram: false,
  search: '',
})

const scanParams = ref({
  search_scope_text: '',
  marketplace: 'vinted_fr',
  per_page: 90,
})

// Scan progress
const scanWorkflowId = ref<string | null>(null)
const scanProgress = ref<any>(null)
let pollInterval: ReturnType<typeof setInterval> | null = null

// --- Options ---
const countryOptions = [
  { label: 'Tous', value: null },
  { label: 'France', value: 'FR' },
  { label: 'Allemagne', value: 'DE' },
  { label: 'Espagne', value: 'ES' },
  { label: 'Italie', value: 'IT' },
  { label: 'Belgique', value: 'BE' },
]

const marketplaceOptions = [
  { label: 'Toutes', value: null },
  { label: 'Vinted FR', value: 'vinted_fr' },
  { label: 'Vinted DE', value: 'vinted_de' },
  { label: 'Vinted ES', value: 'vinted_es' },
  { label: 'Vinted IT', value: 'vinted_it' },
  { label: 'Vinted BE', value: 'vinted_be' },
]

const statusOptions = [
  { label: 'Tous', value: null },
  { label: 'Nouveau', value: 'new' },
  { label: 'Contacté', value: 'contacted' },
  { label: 'Converti', value: 'converted' },
  { label: 'Ignoré', value: 'ignored' },
]

const statusLabels: Record<string, string> = {
  new: 'Nouveau',
  contacted: 'Contacté',
  converted: 'Converti',
  ignored: 'Ignoré',
}

const statusSeverity: Record<string, 'info' | 'warn' | 'success' | 'secondary'> = {
  new: 'info',
  contacted: 'warn',
  converted: 'success',
  ignored: 'secondary',
}

// --- API helpers ---
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

// --- Data fetching ---
async function fetchSellers() {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', skip.value.toString())
    params.append('limit', '50')
    if (filters.value.status) params.append('status', filters.value.status)
    if (filters.value.country_code) params.append('country_code', filters.value.country_code)
    if (filters.value.marketplace) params.append('marketplace', filters.value.marketplace)
    if (filters.value.min_items) params.append('min_items', filters.value.min_items.toString())
    if (filters.value.search) params.append('search', filters.value.search)
    if (filters.value.has_email) params.append('has_email', 'true')
    if (filters.value.has_instagram) params.append('has_instagram', 'true')

    const data = await apiGet(`/api/admin/vinted-pro-sellers?${params}`)
    sellers.value = data.sellers
    total.value = data.total
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  } finally {
    isLoading.value = false
  }
}

async function fetchStats() {
  isLoadingStats.value = true
  try {
    stats.value = await apiGet('/api/admin/vinted-pro-sellers/stats')
  } catch (e: any) {
    adminLogger.error('Failed to fetch pro seller stats:', e)
  } finally {
    isLoadingStats.value = false
  }
}

// --- Filters ---
const debouncedFetch = useDebounceFn(() => {
  skip.value = 0
  fetchSellers()
}, 500)

function resetAndFetch() {
  skip.value = 0
  fetchSellers()
}

// --- Pagination ---
function onPage(event: any) {
  skip.value = event.first
  fetchSellers()
}

// --- Actions ---
async function updateStatus(sellerId: number, newStatus: string) {
  try {
    await apiPatch(`/api/admin/vinted-pro-sellers/${sellerId}`, { status: newStatus })
    toast.add({ severity: 'success', summary: 'Succès', detail: 'Statut mis à jour', life: 2000 })
    fetchSellers()
    fetchStats()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  }
}

async function deleteSeller(sellerId: number) {
  if (!confirm('Supprimer ce vendeur ?')) return
  try {
    await apiDelete(`/api/admin/vinted-pro-sellers/${sellerId}`)
    toast.add({ severity: 'success', summary: 'Succès', detail: 'Vendeur supprimé', life: 2000 })
    fetchSellers()
    fetchStats()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  }
}

async function applyBulkUpdate() {
  if (!bulkStatus.value || selectedSellers.value.length === 0) return
  try {
    const ids = selectedSellers.value.map((s: any) => s.id)
    await apiPost('/api/admin/vinted-pro-sellers/bulk-update', {
      seller_ids: ids,
      status: bulkStatus.value,
    })
    toast.add({
      severity: 'success',
      summary: 'Succès',
      detail: `${ids.length} vendeur(s) mis à jour`,
      life: 2000,
    })
    selectedSellers.value = []
    bulkStatus.value = null
    fetchSellers()
    fetchStats()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  }
}

// --- Scan workflow ---
const scanProgressPercent = computed(() => {
  if (!scanProgress.value || !scanProgress.value.total_letters) return 0
  return Math.round((scanProgress.value.letters_completed / scanProgress.value.total_letters) * 100)
})

async function startScan() {
  isStartingScan.value = true
  try {
    // Parse search scope from comma-separated text
    const scope = scanParams.value.search_scope_text
      ? scanParams.value.search_scope_text.split(',').map(s => s.trim()).filter(Boolean)
      : undefined // Let backend use default A-Z

    const body: any = {
      marketplace: scanParams.value.marketplace,
      per_page: scanParams.value.per_page,
    }
    if (scope) body.search_scope = scope

    const result = await apiPost('/api/admin/vinted-pro-sellers/scan/start', body)
    scanWorkflowId.value = result.workflow_id
    showScanDialog.value = false
    toast.add({
      severity: 'success',
      summary: 'Scan lancé',
      detail: `Workflow ${result.workflow_id}`,
      life: 3000,
    })
    startPolling(result.workflow_id)
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  } finally {
    isStartingScan.value = false
  }
}

function startPolling(workflowId: string) {
  stopPolling()
  scanWorkflowId.value = workflowId
  // Fetch immediately then poll
  pollScanProgress()
  pollInterval = setInterval(pollScanProgress, 3000)
}

async function pollScanProgress() {
  if (!scanWorkflowId.value) return
  try {
    scanProgress.value = await apiGet(`/api/admin/vinted-pro-sellers/scan/progress/${scanWorkflowId.value}`)
    if (['completed', 'failed', 'cancelled'].includes(scanProgress.value.status)) {
      stopPolling()
      fetchSellers()
      fetchStats()
    }
  } catch (e: any) {
    adminLogger.error('Failed to poll scan progress:', e)
  }
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

async function pauseScan() {
  try {
    await apiPost(`/api/admin/vinted-pro-sellers/scan/pause?workflow_id=${scanWorkflowId.value}`)
    toast.add({ severity: 'info', summary: 'Scan en pause', life: 2000 })
    pollScanProgress()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  }
}

async function resumeScan() {
  try {
    await apiPost(`/api/admin/vinted-pro-sellers/scan/resume?workflow_id=${scanWorkflowId.value}`)
    toast.add({ severity: 'info', summary: 'Scan repris', life: 2000 })
    startPolling(scanWorkflowId.value!)
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  }
}

async function cancelScan() {
  if (!confirm('Annuler le scan en cours ?')) return
  try {
    await apiPost(`/api/admin/vinted-pro-sellers/scan/cancel?workflow_id=${scanWorkflowId.value}`)
    toast.add({ severity: 'warn', summary: 'Scan annulé', life: 2000 })
    stopPolling()
    scanProgress.value = { ...scanProgress.value, status: 'cancelled' }
  } catch (e: any) {
    toast.add({ severity: 'error', summary: 'Erreur', detail: e.message, life: 3000 })
  }
}

// --- Utils ---
function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  })
}

// --- Lifecycle ---
onMounted(() => {
  fetchSellers()
  fetchStats()
})

onUnmounted(() => {
  stopPolling()
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

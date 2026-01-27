<template>
  <div class="page-container">
    <!-- Page Header -->
    <PageHeader
      title="Produits Vinted"
      subtitle="Gérez vos produits synchronisés depuis Vinted"
    >
      <template #actions>
        <!-- Sync Button -->
        <Button
          label="Synchroniser"
          icon="pi pi-sync"
          :loading="syncing"
          :disabled="!isConnected || syncing"
          class="btn-secondary"
          v-tooltip.top="!isConnected ? 'Connexion Vinted requise pour synchroniser' : ''"
          @click="syncProducts"
        />
      </template>
    </PageHeader>

    <!-- Bannière offline -->
    <InfoBox v-if="!isConnected" type="warning" icon="pi pi-exclamation-triangle" class="mb-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="font-semibold">Mode hors ligne</p>
          <p class="text-sm mt-1">
            Vous consultez vos produits importés. Reconnectez-vous pour synchroniser, publier ou modifier.
          </p>
        </div>
        <Button
          label="Connecter"
          icon="pi pi-link"
          size="small"
          class="btn-primary ml-4"
          @click="$router.push('/dashboard/platforms/vinted')"
        />
      </div>
    </InfoBox>

    <!-- Contenu principal -->
    <div>
          <!-- Toolbar -->
          <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
            <!-- Search -->
            <div class="flex items-center gap-3">
              <IconField>
                <InputIcon class="pi pi-search" />
                <InputText
                  v-model="searchQuery"
                  placeholder="Rechercher..."
                  class="w-64"
                />
              </IconField>

              <!-- Status Filter -->
              <Select
                v-model="statusFilter"
                :options="statusOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Tous les statuts"
                class="w-48"
              />
            </div>
          </div>

          <!-- Loading -->
          <div v-if="loading" class="text-center py-12">
            <ProgressSpinner style="width: 50px; height: 50px" />
            <p class="mt-4 text-gray-500">Chargement des produits...</p>
          </div>

          <!-- Error -->
          <div v-else-if="error" class="text-center py-12">
            <i class="pi pi-exclamation-triangle text-4xl text-red-400 mb-4"/>
            <p class="text-red-600">{{ error }}</p>
            <Button
              label="Réessayer"
              icon="pi pi-refresh"
              class="mt-4"
              @click="fetchProducts"
            />
          </div>

          <!-- Empty -->
          <div v-else-if="filteredProducts.length === 0" class="text-center py-12">
            <i class="pi pi-box text-4xl text-gray-300 mb-4"/>
            <p class="text-gray-500">
              {{ products.length === 0
                ? (isConnected ? 'Aucun produit synchronisé' : 'Aucun produit importé')
                : 'Aucun résultat pour cette recherche'
              }}
            </p>
            <Button
              v-if="products.length === 0 && isConnected"
              label="Synchroniser maintenant"
              icon="pi pi-sync"
              class="mt-4 btn-primary"
              @click="syncProducts"
            />
            <Button
              v-if="products.length === 0 && !isConnected"
              label="Connecter Vinted"
              icon="pi pi-link"
              class="mt-4 btn-primary"
              @click="$router.push('/dashboard/platforms/vinted')"
            />
          </div>

          <!-- Products Table -->
          <DataTable
            v-else
            :value="filteredProducts"
            :paginator="true"
            :rows="pageSize"
            :totalRecords="totalProducts"
            :rowsPerPageOptions="[10, 20, 50, 100]"
            :lazy="true"
            @page="onPageChange"
            dataKey="vinted_id"
            responsiveLayout="scroll"
            class="p-datatable-sm"
          >
            <!-- Image -->
            <Column header="Image" style="width: 80px">
              <template #body="{ data }">
                <img
                  v-if="data.image_url"
                  :src="data.image_url"
                  :alt="data.title"
                  class="w-16 h-16 object-cover rounded-lg"
                />
                <div v-else class="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
                  <i class="pi pi-image text-gray-400"/>
                </div>
              </template>
            </Column>

            <!-- Title -->
            <Column field="title" header="Titre" sortable style="min-width: 200px">
              <template #body="{ data }">
                <div>
                  <div class="flex items-center gap-2">
                    <a
                      v-if="data.url"
                      :href="data.url"
                      target="_blank"
                      class="font-medium text-secondary-900 hover:text-primary-600 hover:underline transition-colors"
                    >
                      {{ data.title }}
                    </a>
                    <span v-else class="font-medium text-secondary-900">{{ data.title }}</span>
                    <i
                      v-if="data.description"
                      class="pi pi-file-edit text-primary-500"
                      v-tooltip.top="'Description récupérée'"
                    />
                    <i
                      v-else
                      class="pi pi-file text-gray-300"
                      v-tooltip.top="'Pas de description'"
                    />
                  </div>
                  <div class="text-xs text-gray-500 mt-1">
                    ID: {{ data.vinted_id }}
                  </div>
                </div>
              </template>
            </Column>

            <!-- Price -->
            <Column field="price" header="Prix" sortable style="width: 100px">
              <template #body="{ data }">
                <span class="font-semibold text-secondary-900">
                  {{ data.price ? `${data.price.toFixed(2)} €` : '-' }}
                </span>
              </template>
            </Column>

            <!-- Status -->
            <Column field="status" header="Statut" sortable style="width: 120px">
              <template #body="{ data }">
                <Tag
                  :value="getStatusLabel(data.status)"
                  :severity="getStatusSeverity(data.status)"
                />
              </template>
            </Column>

            <!-- Views -->
            <Column field="view_count" header="Vues" sortable style="width: 80px">
              <template #body="{ data }">
                <span class="flex items-center gap-1">
                  <i class="pi pi-eye text-gray-400 text-xs"/>
                  {{ data.view_count || 0 }}
                </span>
              </template>
            </Column>

            <!-- Favourites -->
            <Column field="favourite_count" header="Favoris" sortable style="width: 80px">
              <template #body="{ data }">
                <span class="flex items-center gap-1">
                  <i class="pi pi-heart text-red-400 text-xs"/>
                  {{ data.favourite_count || 0 }}
                </span>
              </template>
            </Column>

            <!-- Published -->
            <Column field="published_at" header="Publié" sortable style="width: 100px">
              <template #body="{ data }">
                {{ data.published_at ? new Date(data.published_at).toLocaleDateString('fr-FR') : '-' }}
              </template>
            </Column>

            <!-- Link Status -->
            <Column header="Liaison" style="width: 150px">
              <template #body="{ data }">
                <div v-if="data.product_id" class="flex items-center gap-2">
                  <Tag severity="success" value="Lié" />
                  <Button
                    icon="pi pi-eye"
                    class="p-button-text p-button-sm"
                    v-tooltip.top="'Voir le produit'"
                    @click="goToProduct(data.product_id)"
                  />
                  <Button
                    icon="pi pi-times"
                    class="p-button-text p-button-sm p-button-danger"
                    :disabled="!isConnected"
                    v-tooltip.top="!isConnected ? 'Connexion requise' : 'Délier'"
                    @click="unlinkProduct(data)"
                  />
                </div>
                <div v-else>
                  <Button
                    label="Lier"
                    icon="pi pi-link"
                    class="p-button-outlined p-button-sm"
                    :disabled="!isConnected"
                    v-tooltip.top="!isConnected ? 'Connexion requise' : ''"
                    @click="openLinkModal(data)"
                  />
                </div>
              </template>
            </Column>

          </DataTable>
        </div>

    <!-- Link Product Modal -->
    <LinkProductModal
      v-model="showLinkModal"
      :vinted-product="selectedVintedProduct"
      @linked="handleLinked"
      @created="handleCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { useToast } from 'primevue/usetoast'
import LinkProductModal from '~/components/vinted/LinkProductModal.vue'
import InfoBox from '~/components/ui/InfoBox.vue'
import { usePlatformConnection } from '~/composables/usePlatformConnection'
import { getStatusLabel, getStatusSeverity } from '~/utils/formatters'
import { vintedLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

const toast = import.meta.client ? useToast() : null

interface VintedProduct {
  id: number
  vinted_id: number
  product_id: number | null  // Link to Stoflow Product
  title: string
  description: string | null
  price: number | null
  currency: string | null
  url: string | null
  status: string
  condition: string | null
  view_count: number
  favourite_count: number
  brand: string | null
  size: string | null
  color: string | null
  category: string | null
  image_url: string | null
  published_at: string | null
}

// Connection
const { isConnected, fetchStatus } = usePlatformConnection('vinted')

// State
const products = ref<VintedProduct[]>([])
const loading = ref(false)
const syncing = ref(false)
const syncPollInterval = ref<ReturnType<typeof setInterval> | null>(null)
const error = ref<string | null>(null)
const searchQuery = ref('')
const statusFilter = ref<string | null>(null)

// Pagination state
const currentPage = ref(1)
const pageSize = ref(20)
const totalProducts = ref(0)

// Link modal state
const showLinkModal = ref(false)
const selectedVintedProduct = ref<VintedProduct | null>(null)

// Options
const statusOptions = [
  { label: 'Tous les statuts', value: null },
  { label: 'Publié', value: 'published' },
  { label: 'Vendu', value: 'sold' },
  { label: 'En attente', value: 'pending' },
  { label: 'Brouillon', value: 'draft' },
]

// Computed - client-side search only (status filter is handled by backend)
const filteredProducts = computed(() => {
  if (!searchQuery.value) return products.value

  const query = searchQuery.value.toLowerCase()
  return products.value.filter(p =>
    p.title?.toLowerCase().includes(query) ||
    p.brand?.toLowerCase().includes(query) ||
    p.vinted_id?.toString().includes(query)
  )
})

// Methods
const api = useApi()

async function fetchProducts(page: number = 1, limit: number = 20) {
  loading.value = true
  error.value = null

  try {
    const offset = (page - 1) * limit
    const params = new URLSearchParams({
      offset: offset.toString(),
      limit: limit.toString(),
    })

    // Send status filter to backend
    if (statusFilter.value) {
      params.append('status_filter', statusFilter.value)
    }

    const response = await api.get<{
      products: VintedProduct[]
      total: number
      limit: number
      offset: number
    }>(`/vinted/products?${params.toString()}`)

    products.value = response?.products || []
    totalProducts.value = response?.total || 0
    currentPage.value = page
    pageSize.value = limit
  } catch (e: any) {
    vintedLogger.error('Failed to fetch Vinted products', { error: e.message })
    error.value = e.message || 'Erreur lors du chargement des produits'
  } finally {
    loading.value = false
  }
}

async function syncProducts() {
  if (syncing.value) return
  syncing.value = true

  try {
    await api.post('/vinted/products/sync')
    startSyncPolling()
  } catch (e: any) {
    // Sync already running - just poll for completion
    if (e.message?.includes('déjà en cours')) {
      startSyncPolling()
    } else {
      vintedLogger.error('Failed to sync Vinted products', { error: e.message })
      error.value = e.message || 'Erreur lors de la synchronisation'
      syncing.value = false
    }
  }
}

async function checkSyncStatus(): Promise<boolean> {
  try {
    const result = await api.get<any[]>('/vinted/temporal/sync/list?limit=1')
    const workflows = result || []
    // close_time is null when workflow is still running
    return workflows.some((w: any) => !w.close_time)
  } catch {
    return false
  }
}

function startSyncPolling() {
  if (syncPollInterval.value) return

  syncPollInterval.value = setInterval(async () => {
    const isRunning = await checkSyncStatus()
    if (!isRunning) {
      stopSyncPolling()
      syncing.value = false
      await fetchProducts(1, pageSize.value)
    }
  }, 5000)
}

function stopSyncPolling() {
  if (syncPollInterval.value) {
    clearInterval(syncPollInterval.value)
    syncPollInterval.value = null
  }
}

// Pagination handler
function onPageChange(event: { first: number; rows: number }) {
  const newPage = Math.floor(event.first / event.rows) + 1
  fetchProducts(newPage, event.rows)
}

// Link functions
function openLinkModal(product: VintedProduct) {
  selectedVintedProduct.value = product
  showLinkModal.value = true
}

function handleLinked(vintedId: number, productId: number) {
  // Update product in list
  const index = products.value.findIndex(p => p.vinted_id === vintedId)
  if (index !== -1) {
    products.value[index].product_id = productId
  }
}

function handleCreated(vintedId: number, productId: number) {
  // Update product in list
  const index = products.value.findIndex(p => p.vinted_id === vintedId)
  if (index !== -1) {
    products.value[index].product_id = productId
  }
}

async function unlinkProduct(product: VintedProduct) {
  try {
    await api.delete(`/api/vinted/products/${product.vinted_id}/link`)

    // Update product in list
    const index = products.value.findIndex(p => p.vinted_id === product.vinted_id)
    if (index !== -1) {
      products.value[index].product_id = null
    }

    toast?.add({
      severity: 'success',
      summary: 'Produit délié',
      detail: 'Le produit a été délié avec succès',
      life: 3000
    })
  } catch (e: any) {
    vintedLogger.error('Failed to unlink Vinted product', { vintedId: product.vinted_id, error: e.message })
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: e.message || 'Impossible de délier le produit',
      life: 5000
    })
  }
}

function goToProduct(productId: number) {
  navigateTo(`/dashboard/products/${productId}/edit`)
}

// Init
onMounted(async () => {
  await fetchStatus()
  await fetchProducts()

  // Check if a sync is already running
  const isRunning = await checkSyncStatus()
  if (isRunning) {
    syncing.value = true
    startSyncPolling()
  }
})

onUnmounted(() => {
  stopSyncPolling()
})

// Reload when status filter changes
watch(statusFilter, () => {
  currentPage.value = 1
  fetchProducts(1, pageSize.value)
})

// Rafraîchir les produits à la reconnexion
watch(isConnected, async (connected) => {
  if (connected) {
    await fetchProducts(1, pageSize.value)
  }
})
</script>

<template>
  <div class="page-container">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <NuxtLink to="/dashboard/platforms/ebay" class="text-gray-500 hover:text-gray-700">
            <i class="pi pi-arrow-left"/>
          </NuxtLink>
          <h1 class="text-2xl font-bold text-secondary-900">Produits eBay</h1>
        </div>
        <p class="text-gray-500">Gerez vos annonces importees depuis eBay</p>
      </div>
      <div class="flex gap-3">
        <Button
          label="Importer"
          icon="pi pi-download"
          class="btn-secondary"
          :loading="isImporting"
          @click="importProducts"
        />
        <Button
          label="Synchroniser"
          icon="pi pi-sync"
          class="btn-primary"
          :loading="isSyncing"
          @click="syncProducts"
        />
      </div>
    </div>

    <!-- Not connected -->
    <Card v-if="!ebayStore.isConnected" class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <div class="text-center py-12">
          <i class="pi pi-link text-4xl text-gray-300 mb-4"/>
          <h3 class="text-xl font-bold text-secondary-900 mb-2">Connectez votre compte eBay</h3>
          <p class="text-gray-500 mb-4">Accedez a vos produits apres connexion</p>
          <Button
            label="Connecter maintenant"
            icon="pi pi-link"
            class="btn-primary"
            @click="navigateTo('/dashboard/platforms/ebay')"
          />
        </div>
      </template>
    </Card>

    <!-- Connected -->
    <template v-else>
      <!-- Stats Summary -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-xl p-4 border border-gray-100">
          <p class="text-sm text-gray-500">Total</p>
          <p class="text-2xl font-bold text-secondary-900">{{ totalProducts }}</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-gray-100">
          <p class="text-sm text-gray-500">Actifs</p>
          <p class="text-2xl font-bold text-success-600">{{ activeCount }}</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-gray-100">
          <p class="text-sm text-gray-500">Brouillons</p>
          <p class="text-2xl font-bold text-warning-600">{{ draftCount }}</p>
        </div>
        <div class="bg-white rounded-xl p-4 border border-gray-100">
          <p class="text-sm text-gray-500">Hors stock</p>
          <p class="text-2xl font-bold text-error-600">{{ outOfStockCount }}</p>
        </div>
      </div>

      <!-- Toolbar -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
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
              label="Reessayer"
              icon="pi pi-refresh"
              class="mt-4"
              @click="fetchProducts"
            />
          </div>

          <!-- Empty -->
          <div v-else-if="filteredProducts.length === 0" class="text-center py-12">
            <i class="pi pi-box text-4xl text-gray-300 mb-4"/>
            <p class="text-gray-500">
              {{ products.length === 0 ? 'Aucun produit importe' : 'Aucun resultat pour cette recherche' }}
            </p>
            <Button
              v-if="products.length === 0"
              label="Importer depuis eBay"
              icon="pi pi-download"
              class="mt-4 btn-primary"
              @click="importProducts"
            />
          </div>

          <!-- Products Table -->
          <ClientOnly v-else>
            <DataTable
              :value="filteredProducts"
              :paginator="true"
              :rows="20"
              :rowsPerPageOptions="[10, 20, 50]"
              :loading="loading"
              stripedRows
              class="modern-table"
              responsiveLayout="scroll"
            >
              <!-- Image + Title -->
              <Column header="Produit" style="min-width: 300px">
                <template #body="{ data }">
                  <div class="flex items-center gap-3">
                    <img
                      v-if="data.image_url"
                      :src="data.image_url"
                      :alt="data.title"
                      class="w-12 h-12 rounded-lg object-cover"
                    >
                    <div v-else class="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center">
                      <i class="pi pi-image text-gray-400"/>
                    </div>
                    <div>
                      <p class="font-semibold text-secondary-900 line-clamp-1">{{ data.title }}</p>
                      <p class="text-xs text-gray-500">SKU: {{ data.ebay_sku || data.id }}</p>
                    </div>
                  </div>
                </template>
              </Column>

              <!-- Price -->
              <Column header="Prix" sortable field="price" style="min-width: 100px">
                <template #body="{ data }">
                  <span class="font-bold text-secondary-900">{{ formatCurrency(data.price) }}</span>
                </template>
              </Column>

              <!-- Quantity -->
              <Column header="Stock" sortable field="quantity" style="min-width: 80px">
                <template #body="{ data }">
                  <Tag
                    :severity="data.quantity > 0 ? 'success' : 'danger'"
                    :value="data.quantity || 0"
                  />
                </template>
              </Column>

              <!-- Condition -->
              <Column header="Etat" style="min-width: 120px">
                <template #body="{ data }">
                  <span class="text-sm">{{ getConditionLabel(data.condition) }}</span>
                </template>
              </Column>

              <!-- Status -->
              <Column header="Statut" style="min-width: 100px">
                <template #body="{ data }">
                  <Tag
                    :severity="getStatusSeverity(data.status)"
                    :value="getStatusLabel(data.status)"
                  />
                </template>
              </Column>

              <!-- Actions -->
              <Column header="Actions" style="min-width: 120px">
                <template #body="{ data }">
                  <div class="flex gap-2">
                    <Button
                      v-if="data.listing_url"
                      icon="pi pi-external-link"
                      class="p-button-sm p-button-text"
                      v-tooltip="'Voir sur eBay'"
                      @click="openOnEbay(data.listing_url)"
                    />
                    <Button
                      icon="pi pi-sync"
                      class="p-button-sm p-button-text"
                      v-tooltip="'Synchroniser'"
                      :loading="syncingId === data.id"
                      @click="syncProduct(data)"
                    />
                  </div>
                </template>
              </Column>
            </DataTable>
            <template #fallback>
              <div class="flex justify-center items-center p-8">
                <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
              </div>
            </template>
          </ClientOnly>
        </template>
      </Card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, getStatusLabel, getStatusSeverity } from '~/utils/formatters'
import { ebayLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

const ebayStore = useEbayStore()
const { showSuccess, showError, showInfo } = useAppToast()
const { get, post } = useApi()

// State
const loading = ref(false)
const error = ref<string | null>(null)
const products = ref<any[]>([])
const totalProducts = ref(0)
const searchQuery = ref('')
const statusFilter = ref<string | null>(null)
const isImporting = ref(false)
const isSyncing = ref(false)
const syncingId = ref<number | null>(null)

// Status options
const statusOptions = [
  { label: 'Tous', value: null },
  { label: 'Actif', value: 'active' },
  { label: 'Inactif', value: 'inactive' },
  { label: 'Brouillon', value: 'draft' },
  { label: 'Hors stock', value: 'out_of_stock' }
]

// Computed
const filteredProducts = computed(() => {
  let result = products.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p =>
      p.title?.toLowerCase().includes(query) ||
      p.ebay_sku?.toLowerCase().includes(query)
    )
  }

  if (statusFilter.value) {
    result = result.filter(p => p.status === statusFilter.value)
  }

  return result
})

const activeCount = computed(() => products.value.filter(p => p.status === 'active').length)
const draftCount = computed(() => products.value.filter(p => p.status === 'inactive' || p.status === 'draft').length)
const outOfStockCount = computed(() => products.value.filter(p => (p.quantity || 0) === 0).length)

// Methods
const fetchProducts = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await get<{
      items: any[]
      total: number
    }>('/api/ebay/products?page=1&page_size=100')

    products.value = response?.items || []
    totalProducts.value = response?.total || 0
  } catch (e: any) {
    error.value = e.message || 'Erreur lors du chargement'
    ebayLogger.error('Failed to fetch eBay products', { error: e.message })
  } finally {
    loading.value = false
  }
}

const importProducts = async () => {
  isImporting.value = true
  try {
    const response = await post<{ imported_count: number }>('/api/ebay/products/import')
    showSuccess('Import termine', `${response?.imported_count || 0} produit(s) importe(s)`, 3000)
    await fetchProducts()
  } catch (e: any) {
    showError('Erreur', e.message || 'Impossible d\'importer les produits', 5000)
  } finally {
    isImporting.value = false
  }
}

const syncProducts = async () => {
  isSyncing.value = true
  try {
    await post('/api/ebay/products/sync')
    showSuccess('Synchronisation', 'Produits synchronises', 3000)
    await fetchProducts()
  } catch (e: any) {
    showError('Erreur', e.message || 'Erreur de synchronisation', 5000)
  } finally {
    isSyncing.value = false
  }
}

const syncProduct = async (product: any) => {
  syncingId.value = product.id
  try {
    await post(`/api/ebay/products/${product.ebay_sku}/sync`)
    showSuccess('Synchronise', 'Produit mis a jour', 3000)
    await fetchProducts()
  } catch (e: any) {
    showError('Erreur', e.message || 'Erreur de synchronisation', 5000)
  } finally {
    syncingId.value = null
  }
}

const openOnEbay = (url: string) => {
  if (!import.meta.client) return
  window.open(url, '_blank')
}

const getConditionLabel = (condition: string): string => {
  const labels: Record<string, string> = {
    NEW: 'Neuf',
    LIKE_NEW: 'Comme neuf',
    NEW_OTHER: 'Neuf autre',
    USED_EXCELLENT: 'Occasion excellent',
    USED_VERY_GOOD: 'Occasion tres bon',
    USED_GOOD: 'Occasion bon',
    USED_ACCEPTABLE: 'Occasion acceptable',
    FOR_PARTS_OR_NOT_WORKING: 'Pour pieces'
  }
  return labels[condition] || condition || 'Non specifie'
}


// Init
onMounted(async () => {
  try {
    await ebayStore.checkConnectionStatus()
    if (ebayStore.isConnected) {
      await fetchProducts()
    }
  } catch (e) {
    ebayLogger.error('Failed to initialize eBay products page', { error: e })
  }
})
</script>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
}
</style>

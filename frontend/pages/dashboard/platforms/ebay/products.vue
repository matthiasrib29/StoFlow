<template>
  <PlatformProductsPage
    platform="ebay"
    :is-connected="ebayStore.isConnected ?? false"
    :loading="loading"
    :error="error"
    :is-empty="products.length === 0"
    @retry="fetchProducts"
  >
    <!-- Header Actions -->
    <template #header-actions>
      <Button
        label="Importer"
        icon="pi pi-download"
        class="btn-primary"
        :loading="isSyncing"
        :disabled="isSyncing"
        @click="handleImport"
      />
    </template>

    <!-- Stats Summary -->
    <template #stats>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
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
    </template>

    <!-- Toolbar -->
    <template #toolbar>
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <IconField>
            <InputIcon class="pi pi-search" />
            <InputText
              v-model="searchQuery"
              placeholder="Rechercher..."
              class="w-64"
            />
          </IconField>

          <Select
            v-model="statusFilter"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Tous les statuts"
            class="w-48"
            @change="onStatusChange"
          />

          <Select
            v-model="marketplaceFilter"
            :options="marketplaceOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Toutes les marketplaces"
            class="w-52"
            @change="onMarketplaceChange"
          />
        </div>
      </div>
    </template>

    <!-- Products Table -->
    <template #content>
      <ClientOnly>
        <DataTable
          :value="filteredProducts"
          :paginator="true"
          :lazy="true"
          :rows="pageSize"
          :totalRecords="totalProducts"
          :rowsPerPageOptions="[20, 50, 100]"
          :first="(currentPage - 1) * pageSize"
          stripedRows
          class="modern-table"
          responsiveLayout="scroll"
          @page="onPageChange"
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
                  <a
                    v-if="data.ebay_listing_url"
                    :href="data.ebay_listing_url"
                    target="_blank"
                    class="font-semibold text-secondary-900 line-clamp-1 hover:text-primary-600 hover:underline transition-colors"
                  >
                    {{ data.title }}
                  </a>
                  <p v-else class="font-semibold text-secondary-900 line-clamp-1">{{ data.title }}</p>
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

          <!-- Link Status -->
          <Column header="Liaison" style="min-width: 150px">
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
                  v-tooltip.top="'Délier'"
                  @click="unlinkProduct(data)"
                />
              </div>
              <div v-else>
                <Button
                  label="Lier"
                  icon="pi pi-link"
                  class="p-button-outlined p-button-sm"
                  @click="openLinkModal(data)"
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

    <!-- Empty Actions -->
    <template #empty-actions>
      <Button
        label="Importer depuis eBay"
        icon="pi pi-download"
        class="mt-4 btn-primary"
        :loading="isSyncing"
        @click="handleImport"
      />
    </template>
  </PlatformProductsPage>

  <!-- Link Product Modal -->
  <EbayLinkProductModal
    v-model="showLinkModal"
    :ebay-product="selectedEbayProduct"
    @linked="handleLinked"
    @created="handleCreated"
  />
</template>

<script setup lang="ts">
import { useToast } from 'primevue/usetoast'
import EbayLinkProductModal from '~/components/ebay/LinkProductModal.vue'
import { formatCurrency, getStatusLabel, getStatusSeverity } from '~/utils/formatters'
import { ebayLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

interface EbayProduct {
  id: number
  ebay_sku: string
  product_id: number | null
  title: string
  description: string | null
  price: number | null
  currency: string
  brand: string | null
  size: string | null
  color: string | null
  condition: string | null
  quantity: number
  marketplace_id: string
  ebay_listing_id: number | null
  status: string
  image_url: string | null
  image_urls: string[] | null
  ebay_listing_url: string | null
}

const ebayStore = useEbayStore()
const { showSuccess, showError } = useAppToast()
const { get, post, delete: del } = useApi()
const toast = import.meta.client ? useToast() : null

// Use eBay products composable for Temporal sync
const {
  isSyncing,
  syncProducts,
} = useEbayProducts()

// State
const loading = ref(false)
const error = ref<string | null>(null)
const products = ref<EbayProduct[]>([])
const totalProducts = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const statusFilter = ref<string | null>(null)
const marketplaceFilter = ref<string | null>(null)

// Link modal state
const showLinkModal = ref(false)
const selectedEbayProduct = ref<EbayProduct | null>(null)

// Status options
const statusOptions = [
  { label: 'Tous', value: null },
  { label: 'Actif', value: 'active' },
  { label: 'Inactif', value: 'inactive' },
  { label: 'Brouillon', value: 'draft' },
  { label: 'Hors stock', value: 'out_of_stock' }
]

// Marketplace options
const marketplaceOptions = [
  { label: 'Toutes les marketplaces', value: null },
  { label: 'eBay France', value: 'EBAY_FR' },
  { label: 'eBay Allemagne', value: 'EBAY_DE' },
  { label: 'eBay Royaume-Uni', value: 'EBAY_GB' },
  { label: 'eBay Italie', value: 'EBAY_IT' },
  { label: 'eBay Espagne', value: 'EBAY_ES' },
  { label: 'eBay Pays-Bas', value: 'EBAY_NL' },
  { label: 'eBay Pologne', value: 'EBAY_PL' },
  { label: 'eBay États-Unis', value: 'EBAY_US' }
]

// Computed - only search filter (status filter is server-side)
const filteredProducts = computed(() => {
  let result = products.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p =>
      p.title?.toLowerCase().includes(query) ||
      p.ebay_sku?.toLowerCase().includes(query)
    )
  }

  return result
})

// Stats from API (global, not affected by pagination)
const activeCount = ref(0)
const draftCount = ref(0)
const outOfStockCount = ref(0)

// Methods
const fetchProducts = async (page?: number, size?: number) => {
  const targetPage = page ?? currentPage.value
  const targetSize = size ?? pageSize.value

  ebayLogger.info('Fetching eBay products', {
    page: targetPage,
    pageSize: targetSize,
    marketplace: marketplaceFilter.value
  })

  loading.value = true
  error.value = null
  try {
    const params = new URLSearchParams({
      page: targetPage.toString(),
      page_size: targetSize.toString()
    })

    if (marketplaceFilter.value) {
      params.append('marketplace_id', marketplaceFilter.value)
    }

    if (statusFilter.value) {
      params.append('status', statusFilter.value)
    }

    const response = await get<{
      items: any[]
      total: number
      active_count: number
      inactive_count: number
      out_of_stock_count: number
    }>(`/ebay/products?${params.toString()}`)

    products.value = response?.items || []
    totalProducts.value = response?.total || 0
    activeCount.value = response?.active_count || 0
    draftCount.value = response?.inactive_count || 0
    outOfStockCount.value = response?.out_of_stock_count || 0

    ebayLogger.info('eBay products fetched successfully', {
      totalProducts: totalProducts.value,
      itemsCount: products.value.length,
      page: targetPage
    })
  } catch (e: any) {
    error.value = e.message || 'Erreur lors du chargement'
    ebayLogger.error('Failed to fetch eBay products', {
      error: e.message,
      stack: e.stack
    })
  } finally {
    loading.value = false
  }
}

const onPageChange = async (event: { page: number; rows: number; first: number }) => {
  const newPage = event.page + 1 // PrimeVue uses 0-based index
  const newSize = event.rows

  currentPage.value = newPage
  pageSize.value = newSize

  await fetchProducts(newPage, newSize)
}

const onMarketplaceChange = async () => {
  currentPage.value = 1
  await fetchProducts(1, pageSize.value)
}

const onStatusChange = async () => {
  currentPage.value = 1
  await fetchProducts(1, pageSize.value)
}

/**
 * Handle sync via Temporal workflow.
 * Fire-and-forget: workflow runs in background, user refreshes to see results.
 */
const handleImport = async () => {
  ebayLogger.info('Starting eBay products sync via Temporal')
  await syncProducts()
}

const getConditionLabel = (condition: string): string => {
  const labels: Record<string, string> = {
    NEW: 'Neuf',
    LIKE_NEW: 'Comme neuf',
    NEW_OTHER: 'Neuf autre',
    USED_EXCELLENT: 'Occasion excellent',
    USED_VERY_GOOD: 'Occasion très bon',
    USED_GOOD: 'Occasion bon',
    USED_ACCEPTABLE: 'Occasion acceptable',
    FOR_PARTS_OR_NOT_WORKING: 'Pour pièces'
  }
  return labels[condition] || condition || 'Non spécifié'
}

// Link functions
function openLinkModal(product: EbayProduct) {
  selectedEbayProduct.value = product
  showLinkModal.value = true
}

function handleLinked(ebayProductId: number, productId: number) {
  // Update product in list
  const index = products.value.findIndex(p => p.id === ebayProductId)
  if (index !== -1) {
    products.value[index].product_id = productId
  }
}

function handleCreated(ebayProductId: number, productId: number) {
  // Update product in list
  const index = products.value.findIndex(p => p.id === ebayProductId)
  if (index !== -1) {
    products.value[index].product_id = productId
  }
}

async function unlinkProduct(product: EbayProduct) {
  try {
    await del(`/ebay/products/${product.id}/link`)

    // Update product in list
    const index = products.value.findIndex(p => p.id === product.id)
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
    ebayLogger.error('Failed to unlink eBay product', { ebayProductId: product.id, error: e.message })
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
  ebayLogger.info('eBay Products page mounted', {
    route: '/dashboard/platforms/ebay/products'
  })

  try {
    await ebayStore.checkConnectionStatus()
    ebayLogger.debug('Connection status checked', {
      isConnected: ebayStore.isConnected
    })

    if (ebayStore.isConnected) {
      await fetchProducts()
    } else {
      ebayLogger.warn('User not connected to eBay', {
        redirectRequired: true
      })
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

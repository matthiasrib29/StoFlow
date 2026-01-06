<template>
  <div class="page-container">
    <!-- Page Header -->
    <VintedPageHeader
      title="Annonces Vinted"
      subtitle="Gérez vos annonces synchronisées depuis Vinted"
    />

    <!-- Content -->
    <Card class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <!-- Not connected -->
        <div v-if="!isConnected" class="text-center py-12">
          <i class="pi pi-link text-4xl text-gray-300 mb-4"/>
          <h3 class="text-xl font-bold text-secondary-900 mb-2">Connectez votre compte Vinted</h3>
          <p class="text-gray-500 mb-4">Accédez à vos annonces après connexion</p>
          <Button
            label="Connecter maintenant"
            icon="pi pi-link"
            class="btn-primary"
            @click="$router.push('/dashboard/platforms/vinted')"
          />
        </div>

        <!-- Connected -->
        <div v-else>
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

            <!-- Sync Button -->
            <Button
              label="Synchroniser"
              icon="pi pi-sync"
              :loading="syncing"
              class="btn-secondary"
              @click="syncProducts"
            />
          </div>

          <!-- Loading -->
          <div v-if="loading" class="text-center py-12">
            <ProgressSpinner style="width: 50px; height: 50px" />
            <p class="mt-4 text-gray-500">Chargement des annonces...</p>
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
              {{ products.length === 0 ? 'Aucune annonce synchronisée' : 'Aucun résultat pour cette recherche' }}
            </p>
            <Button
              v-if="products.length === 0"
              label="Synchroniser maintenant"
              icon="pi pi-sync"
              class="mt-4 btn-primary"
              @click="syncProducts"
            />
          </div>

          <!-- Products Table -->
          <DataTable
            v-else
            :value="filteredProducts"
            :paginator="true"
            :rows="20"
            :rowsPerPageOptions="[10, 20, 50]"
            dataKey="id"
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
                      :href="data.url"
                      target="_blank"
                      class="font-medium text-primary-600 hover:underline"
                    >
                      {{ data.title }}
                    </a>
                    <i
                      v-if="data.description"
                      class="pi pi-file-edit text-green-500"
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
                <span class="font-semibold text-green-600">
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

            <!-- Brand -->
            <Column field="brand" header="Marque" sortable style="width: 120px">
              <template #body="{ data }">
                {{ data.brand || '-' }}
              </template>
            </Column>

            <!-- Published -->
            <Column field="published_at" header="Publié" sortable style="width: 120px">
              <template #body="{ data }">
                {{ formatDate(data.published_at) }}
              </template>
            </Column>

            <!-- Link Status -->
            <Column header="Liaison" style="width: 150px">
              <template #body="{ data }">
                <div v-if="data.product_id" class="flex items-center gap-2">
                  <Tag severity="success" value="Lié" />
                  <Button
                    icon="pi pi-eye"
                    class="p-button-text p-button-sm p-button-success"
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

            <!-- Actions -->
            <Column header="Actions" style="width: 80px">
              <template #body="{ data }">
                <div class="flex gap-2">
                  <Button
                    icon="pi pi-external-link"
                    class="p-button-text p-button-sm"
                    v-tooltip.top="'Voir sur Vinted'"
                    @click="openVinted(data.url)"
                  />
                </div>
              </template>
            </Column>
          </DataTable>
        </div>
      </template>
    </Card>

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
import { usePlatformConnection } from '~/composables/usePlatformConnection'
import { formatDate, getStatusLabel, getStatusSeverity } from '~/utils/formatters'
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
const error = ref<string | null>(null)
const searchQuery = ref('')
const statusFilter = ref<string | null>(null)

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

// Computed
const filteredProducts = computed(() => {
  let result = products.value

  // Filter by status
  if (statusFilter.value) {
    result = result.filter(p => p.status === statusFilter.value)
  }

  // Filter by search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p =>
      p.title?.toLowerCase().includes(query) ||
      p.brand?.toLowerCase().includes(query) ||
      p.vinted_id?.toString().includes(query)
    )
  }

  return result
})

// Methods
const api = useApi()

async function fetchProducts() {
  loading.value = true
  error.value = null

  try {
    const response = await api.get<{ products: VintedProduct[] }>('/api/vinted/products?limit=500')
    products.value = response?.products || []
  } catch (e: any) {
    vintedLogger.error('Failed to fetch Vinted products', { error: e.message })
    error.value = e.message || 'Erreur lors du chargement des annonces'
  } finally {
    loading.value = false
  }
}

async function syncProducts() {
  syncing.value = true

  try {
    await api.post('/api/vinted/products/sync')
    await fetchProducts()
  } catch (e: any) {
    vintedLogger.error('Failed to sync Vinted products', { error: e.message })
    error.value = e.message || 'Erreur lors de la synchronisation'
  } finally {
    syncing.value = false
  }
}


function openVinted(url: string | null) {
  if (url) {
    window.open(url, '_blank')
  }
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
  if (isConnected.value) {
    await fetchProducts()
  }
})

// Watch connection
watch(isConnected, async (connected) => {
  if (connected && products.value.length === 0) {
    await fetchProducts()
  }
})
</script>

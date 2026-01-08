<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Lier le produit Vinted"
    :style="{ width: '600px' }"
    class="link-product-modal"
  >
    <!-- Vinted Product Info -->
    <div class="flex items-center gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
      <img
        v-if="vintedProduct?.image_url"
        :src="vintedProduct.image_url"
        :alt="vintedProduct.title"
        class="w-16 h-16 object-cover rounded-lg"
      />
      <div v-else class="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
        <i class="pi pi-image text-gray-400" />
      </div>
      <div>
        <h4 class="font-semibold text-gray-900">{{ vintedProduct?.title }}</h4>
        <p class="text-sm text-gray-500">
          {{ vintedProduct?.brand || 'Sans marque' }} - {{ Number(vintedProduct?.price)?.toFixed(2) }} €
        </p>
      </div>
    </div>

    <!-- Tabs -->
    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="existing">Produit existant</Tab>
        <Tab value="create">Créer nouveau</Tab>
      </TabList>

      <TabPanels>
        <!-- Tab: Link to existing product -->
        <TabPanel value="existing">
          <div class="py-4">
            <!-- Search -->
            <IconField class="mb-4">
              <InputIcon class="pi pi-search" />
              <InputText
                v-model="searchQuery"
                placeholder="Rechercher un produit..."
                class="w-full"
                @input="debouncedSearch"
              />
            </IconField>

            <!-- Loading -->
            <div v-if="loadingProducts" class="text-center py-8">
              <ProgressSpinner style="width: 30px; height: 30px" />
            </div>

            <!-- Products list -->
            <div v-else-if="linkableProducts.length > 0" class="space-y-2 max-h-64 overflow-y-auto">
              <div
                v-for="product in linkableProducts"
                :key="product.id"
                :class="[
                  'flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors',
                  selectedProductId === product.id
                    ? 'bg-primary-50 border-2 border-primary-500'
                    : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                ]"
                @click="selectedProductId = product.id"
              >
                <img
                  v-if="product.image_url"
                  :src="product.image_url"
                  :alt="product.title"
                  class="w-12 h-12 object-cover rounded"
                />
                <div v-else class="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                  <i class="pi pi-image text-gray-400 text-sm" />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="font-medium text-gray-900 truncate">{{ product.title }}</p>
                  <p class="text-sm text-gray-500">
                    {{ product.brand || 'Sans marque' }} - {{ Number(product.price)?.toFixed(2) }} €
                  </p>
                </div>
                <i
                  v-if="selectedProductId === product.id"
                  class="pi pi-check-circle text-primary-500 text-xl"
                />
              </div>
            </div>

            <!-- Empty -->
            <div v-else class="text-center py-8 text-gray-500">
              <i class="pi pi-box text-3xl mb-2" />
              <p>Aucun produit disponible</p>
              <p class="text-sm">Créez un nouveau produit ou modifiez la recherche</p>
            </div>
          </div>
        </TabPanel>

        <!-- Tab: Create new product -->
        <TabPanel value="create">
          <div class="py-4 space-y-4">
            <Message severity="info" :closable="false">
              Un nouveau produit sera créé avec les données du produit Vinted.
              Vous pourrez le modifier après création.
            </Message>

            <!-- Preview of data to import -->
            <div class="space-y-3">
              <div class="flex items-center gap-2">
                <label class="w-24 text-sm text-gray-500">Titre:</label>
                <span class="font-medium">{{ vintedProduct?.title }}</span>
              </div>
              <div class="flex items-center gap-2">
                <label class="w-24 text-sm text-gray-500">Prix:</label>
                <span class="font-medium">{{ Number(vintedProduct?.price)?.toFixed(2) }} €</span>
              </div>
              <div class="flex items-center gap-2">
                <label class="w-24 text-sm text-gray-500">Marque:</label>
                <span class="font-medium">{{ vintedProduct?.brand || '-' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <label class="w-24 text-sm text-gray-500">Taille:</label>
                <span class="font-medium">{{ vintedProduct?.size || '-' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <label class="w-24 text-sm text-gray-500">Couleur:</label>
                <span class="font-medium">{{ vintedProduct?.color || '-' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <label class="w-24 text-sm text-gray-500">Catégorie:</label>
                <span class="font-medium">{{ vintedProduct?.category || '-' }}</span>
              </div>
            </div>
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>

    <!-- Footer -->
    <template #footer>
      <div class="flex justify-end gap-2">
        <Button
          label="Annuler"
          severity="secondary"
          @click="close"
        />
        <Button
          v-if="activeTab === 'existing'"
          label="Lier"
          icon="pi pi-link"
          :disabled="!selectedProductId"
          :loading="linking"
          @click="linkToExisting"
        />
        <Button
          v-else
          label="Créer et lier"
          icon="pi pi-plus"
          :loading="linking"
          @click="createAndLink"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { useToast } from 'primevue/usetoast'
import { vintedLogger } from '~/utils/logger'

interface VintedProduct {
  id: number
  vinted_id: number
  product_id: number | null
  title: string
  description: string | null
  price: number | null
  brand: string | null
  size: string | null
  color: string | null
  category: string | null
  image_url: string | null
}

interface LinkableProduct {
  id: number
  title: string
  brand: string | null
  price: number | null
  category: string | null
  status: string | null
  image_url: string | null
}

const props = defineProps<{
  modelValue: boolean
  vintedProduct: VintedProduct | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'linked': [vintedId: number, productId: number]
  'created': [vintedId: number, productId: number]
}>()

// State
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const activeTab = ref('existing')
const searchQuery = ref('')
const selectedProductId = ref<number | null>(null)
const linkableProducts = ref<LinkableProduct[]>([])
const loadingProducts = ref(false)
const linking = ref(false)

const api = useApi()
const toast = import.meta.client ? useToast() : null

// Debounced search
let searchTimeout: NodeJS.Timeout | null = null
function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchLinkableProducts()
  }, 300)
}

// Fetch linkable products (uses main products API)
async function fetchLinkableProducts() {
  if (!props.vintedProduct) return

  loadingProducts.value = true
  try {
    const params = new URLSearchParams()
    params.set('limit', '20')
    if (searchQuery.value) params.set('search', searchQuery.value)

    const response = await api.get<{ products: LinkableProduct[] }>(
      `/api/products?${params}`
    )
    linkableProducts.value = response?.products || []
  } catch (e) {
    vintedLogger.error('Error fetching linkable products:', e)
    linkableProducts.value = []
  } finally {
    loadingProducts.value = false
  }
}

// Link to existing product
async function linkToExisting() {
  if (!props.vintedProduct || !selectedProductId.value) return

  linking.value = true
  try {
    await api.post(`/api/vinted/products/${props.vintedProduct.vinted_id}/link`, {
      product_id: selectedProductId.value
    })

    toast?.add({
      severity: 'success',
      summary: 'Produit lié',
      detail: 'Le produit Vinted a été lié avec succès',
      life: 3000
    })

    emit('linked', props.vintedProduct.vinted_id, selectedProductId.value)
    close()
  } catch (e: any) {
    vintedLogger.error('Error linking product:', e)
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: e.message || 'Impossible de lier le produit',
      life: 5000
    })
  } finally {
    linking.value = false
  }
}

// Create and link
async function createAndLink() {
  if (!props.vintedProduct) return

  linking.value = true
  try {
    // POST /link without product_id creates a new Product from VintedProduct
    const response = await api.post<{ product_id: number }>(
      `/api/vinted/products/${props.vintedProduct.vinted_id}/link`
    )

    toast?.add({
      severity: 'success',
      summary: 'Produit créé et lié',
      detail: 'Un nouveau produit a été créé à partir des données Vinted',
      life: 3000
    })

    emit('created', props.vintedProduct.vinted_id, response?.product_id || 0)
    close()
  } catch (e: any) {
    vintedLogger.error('Error creating product:', e)
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: e.message || 'Impossible de créer le produit',
      life: 5000
    })
  } finally {
    linking.value = false
  }
}

// Close modal
function close() {
  visible.value = false
  resetState()
}

// Reset state
function resetState() {
  activeTab.value = 'existing'
  searchQuery.value = ''
  selectedProductId.value = null
  linkableProducts.value = []
}

// Watch for modal open
watch(visible, (isVisible) => {
  if (isVisible && props.vintedProduct) {
    fetchLinkableProducts()
  } else {
    resetState()
  }
})
</script>

<style scoped>
.link-product-modal :deep(.p-dialog-content) {
  padding: 0 1.5rem;
}
</style>

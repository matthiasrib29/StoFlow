<template>
  <div class="page-container">
    <PageHeader
      title="Détail du produit"
      :subtitle="product?.title || 'Chargement...'"
    >
      <template #actions>
        <Button
          label="Retour"
          icon="pi pi-arrow-left"
          severity="secondary"
          text
          @click="$router.push('/dashboard/products')"
        />
      </template>
    </PageHeader>

    <!-- Loading -->
    <div v-if="productsStore.isLoading" class="text-center py-12">
      <ProgressBar mode="indeterminate" />
      <p class="text-gray-500 mt-4">Chargement du produit...</p>
    </div>

    <!-- Error -->
    <Card v-else-if="productsStore.error || !product" class="bg-secondary-50 border border-primary-200">
      <template #content>
        <div class="text-center text-secondary-600">
          <i class="pi pi-exclamation-triangle text-4xl mb-3"/>
          <p>{{ productsStore.error || 'Produit non trouvé' }}</p>
        </div>
      </template>
    </Card>

    <!-- Product Detail -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Image -->
      <Card>
        <template #content>
          <img
            :src="product.image_url"
            :alt="product.title"
            class="w-full h-auto rounded-lg"
          >
        </template>
      </Card>

      <!-- Info -->
      <div class="space-y-6">
        <Card>
          <template #title>
            <div class="flex justify-between items-start">
              <div>
                <h2 class="text-2xl font-bold">{{ product.title }}</h2>
                <p class="text-gray-500 mt-1">{{ product.brand }}</p>
              </div>
              <Badge
                :value="product.is_active ? 'Actif' : 'Inactif'"
                :severity="product.is_active ? 'success' : 'danger'"
              />
            </div>
          </template>
          <template #content>
            <div class="space-y-4">
              <div>
                <h3 class="text-3xl font-bold text-primary-600">
                  {{ product.price !== null ? Number(product.price).toFixed(2) : '-' }} €
                </h3>
              </div>

              <div>
                <h4 class="font-semibold text-gray-700 mb-2">Description</h4>
                <p class="text-gray-600">{{ product.description }}</p>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-sm text-gray-500">Catégorie</p>
                  <p class="font-medium">{{ product.category }}</p>
                </div>
                <div>
                  <p class="text-sm text-gray-500">État</p>
                  <p class="font-medium">{{ product.condition }}</p>
                </div>
                <div>
                  <p class="text-sm text-gray-500">Taille</p>
                  <p class="font-medium">{{ product.size }}</p>
                </div>
                <div>
                  <p class="text-sm text-gray-500">Couleur</p>
                  <p class="font-medium">{{ product.color }}</p>
                </div>
                <div>
                  <p class="text-sm text-gray-500">Matériau</p>
                  <p class="font-medium">{{ product.material }}</p>
                </div>
                <div>
                  <p class="text-sm text-gray-500">Stock</p>
                  <p class="font-medium">{{ product.stock_quantity }}</p>
                </div>
              </div>

              <div class="pt-4 border-t">
                <p class="text-xs text-gray-400">
                  ID: {{ product.id }} •
                  Créé le {{ formatDate(product.created_at) }}
                </p>
              </div>
            </div>
          </template>
          <template #footer>
            <div class="flex gap-3">
              <Button
                label="Modifier"
                icon="pi pi-pencil"
                severity="warning"
                @click="router.push(`/dashboard/products/${product.id}/edit`)"
              />
              <Button
                label="Publier sur Vinted"
                icon="pi pi-send"
                @click="publishToVinted"
              />
            </div>
          </template>
        </Card>

        <!-- Pricing Section -->
        <Card>
          <template #title>
            <h3 class="text-lg font-semibold">Intelligent Pricing</h3>
          </template>
          <template #content>
            <div class="space-y-4">
              <Button
                class="w-full"
                :disabled="isLoadingPrice || !canCalculatePrice"
                :severity="priceResult ? 'success' : 'primary'"
                @click="handleCalculatePrice"
              >
                <span v-if="!isLoadingPrice">
                  <i class="pi pi-calculator mr-2" />
                  {{ priceResult ? 'Recalculate Price' : 'Calculate Price' }}
                </span>
                <span v-else class="flex items-center justify-center">
                  <i class="pi pi-spin pi-spinner mr-2" />
                  Calculating...
                </span>
              </Button>

              <!-- Error Message -->
              <div v-if="priceError" class="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
                <i class="pi pi-exclamation-triangle mr-2" />
                {{ priceError }}
              </div>

              <!-- Pricing Display Component -->
              <Transition name="fade">
                <div v-if="priceResult" class="mt-4">
                  <ProductsPricingDisplay :pricing="priceResult" />
                </div>
              </Transition>

              <p v-if="!canCalculatePrice" class="text-sm text-gray-500 italic">
                Brand and category are required to calculate pricing.
              </p>
            </div>
          </template>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatDate } from '~/utils/formatters'
import type { PriceInput } from '~/composables/usePricingCalculation'
import { productLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

const route = useRoute()
const router = useRouter()
const productsStore = useProductsStore()
const { showSuccess, showError, showInfo, showWarn } = useAppToast()
const { isLoading: isLoadingPrice, error: priceError, priceResult, calculatePrice, reset } = usePricingCalculation()

const id = computed(() => parseInt(route.params.id as string))
const product = computed(() => productsStore.getProductById(id.value))

// Charger le produit si pas encore en store
onMounted(async () => {
  if (!product.value) {
    try {
      await productsStore.fetchProducts()
    } catch (error) {
      showError('Erreur', 'Impossible de charger le produit', 5000)
    }
  }
})

const canCalculatePrice = computed(() => {
  return product.value?.brand && product.value?.category
})

const handleCalculatePrice = async () => {
  if (!product.value) return

  // Build PriceInput from product data
  const input: PriceInput = {
    brand: product.value.brand || '',
    category: product.value.category || '',
    materials: product.value.material ? [product.value.material] : [],
    model_name: product.value.model || undefined,
    condition_score: product.value.condition ? Math.round(product.value.condition / 2) : 3, // Convert 0-10 to 0-5
    supplements: product.value.condition_sup || [],
    condition_sensitivity: 1.0,
    actual_origin: product.value.origin || 'Unknown',
    expected_origins: [], // TODO: determine from category/brand in future phase
    actual_decade: product.value.decade || '2020s',
    expected_decades: [],
    actual_trends: product.value.trend ? [product.value.trend] : [],
    expected_trends: [],
    actual_features: [],
    expected_features: []
  }

  try {
    await calculatePrice(input)
    showSuccess('Success', 'Price calculated successfully', 3000)
  } catch (err) {
    // Error already handled in composable
    productLogger.error('Price calculation failed:', err)
  }
}

const publishToVinted = () => {
  showInfo('Fonctionnalité à venir', 'La publication sur Vinted sera disponible dans la prochaine version', 3000)
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

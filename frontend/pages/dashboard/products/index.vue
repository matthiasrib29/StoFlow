<template>
  <div class="p-4 lg:p-8">
    <!-- Page Header -->
    <div class="mb-6 lg:mb-8">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-2">
        <div>
          <h1 class="text-2xl lg:text-3xl font-bold text-secondary-900 mb-1">Produits StoFlow</h1>
          <p class="text-gray-600 text-sm lg:text-base">Gérez votre catalogue de produits</p>
        </div>
        <Button
          label="Créer un produit"
          icon="pi pi-plus"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold w-full sm:w-auto"
          @click="$router.push('/dashboard/products/create')"
        />
      </div>
    </div>

    <!-- Filters -->
    <ProductsFilterBar
      v-model:search="searchQuery"
      v-model:category="selectedCategory"
      v-model:status="selectedStatus"
      v-model:view="viewMode"
      :selected-count="selectedProducts.length"
      @bulk-activate="bulkActivate"
      @bulk-deactivate="bulkDeactivate"
      @bulk-delete="confirmBulkDelete"
    />

    <!-- Loading State with Skeleton Cards -->
    <div v-if="productsStore.isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 stagger-grid">
      <SkeletonCard
        v-for="n in 8"
        :key="n"
        :show-image="true"
        image-height="240px"
        :lines="2"
        :show-actions="true"
        :actions-count="3"
      />
    </div>

    <!-- Table Mode Container -->
    <div v-else-if="viewMode === 'table'">
      <!-- Desktop: DataTable -->
      <div class="hidden lg:block bg-white rounded-xl border border-gray-200 overflow-hidden">
        <DataTable
        v-model:selection="selectedProducts"
        :value="filteredProducts"
        data-key="id"
        :lazy="true"
        :paginator="true"
        :rows="rowsPerPage"
        :total-records="productsStore.pagination.total"
        :first="(currentPage - 1) * rowsPerPage"
        :rows-per-page-options="[10, 20, 50, 100]"
        paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
        current-page-report-template="{first}-{last} sur {totalRecords} produits"
        :loading="productsStore.isLoading"
        class="products-table"
        @page="onPageChange"
      >
        <template #empty>
          <div class="text-center py-16">
            <div class="w-20 h-20 rounded-full bg-gray-50 flex items-center justify-center mx-auto mb-4">
              <i class="pi pi-box text-4xl text-gray-300"/>
            </div>
            <p class="text-secondary-900 font-semibold text-lg mb-1">Aucun produit</p>
            <p class="text-gray-400 text-sm mb-6">Commencez par créer votre premier produit</p>
            <Button
              label="Créer un produit"
              icon="pi pi-plus"
              class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
              @click="$router.push('/dashboard/products/create')"
            />
          </div>
        </template>

        <Column selection-mode="multiple" header-style="width: 3rem" />

        <Column field="image_url" header="" style="width: 70px">
          <template #body="slotProps">
            <img
              :src="getProductImageUrl(slotProps.data)"
              :alt="slotProps.data.title"
              class="w-12 h-12 object-cover rounded-lg"
            >
          </template>
        </Column>

        <Column field="title" header="Produit" sortable style="min-width: 220px">
          <template #body="slotProps">
            <div>
              <p class="font-semibold text-secondary-900">{{ slotProps.data.title }}</p>
              <p class="text-xs text-gray-400">{{ slotProps.data.id }}</p>
            </div>
          </template>
        </Column>

        <Column field="brand" header="Marque" sortable>
          <template #body="slotProps">
            <span class="text-secondary-800">{{ slotProps.data.brand }}</span>
          </template>
        </Column>

        <Column field="category" header="Catégorie" sortable>
          <template #body="slotProps">
            <span class="text-sm text-gray-600">{{ slotProps.data.category }}</span>
          </template>
        </Column>

        <Column field="price" header="Prix" sortable style="width: 100px">
          <template #body="slotProps">
            <span class="font-semibold text-secondary-900">{{ formatPrice(slotProps.data.price) }}</span>
          </template>
        </Column>

        <Column field="stock_quantity" header="Stock" sortable style="width: 80px">
          <template #body="slotProps">
            <span
              class="text-sm font-medium"
              :class="slotProps.data.stock_quantity > 0 ? 'text-green-600' : 'text-red-500'"
            >
              {{ slotProps.data.stock_quantity }}
            </span>
          </template>
        </Column>

        <Column field="is_active" header="Statut" sortable style="width: 90px">
          <template #body="slotProps">
            <span
              class="inline-flex items-center gap-1.5 text-xs font-medium"
              :class="slotProps.data.is_active ? 'text-green-600' : 'text-gray-400'"
            >
              <span
                class="w-2 h-2 rounded-full"
                :class="slotProps.data.is_active ? 'bg-green-500' : 'bg-gray-300'"
              />
              {{ slotProps.data.is_active ? 'Actif' : 'Inactif' }}
            </span>
          </template>
        </Column>

        <Column header="" style="width: 90px">
          <template #body="slotProps">
            <div class="flex gap-1 justify-end">
              <button
                class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                @click="editProduct(slotProps.data)"
              >
                <i class="pi pi-pencil text-sm"/>
              </button>
              <button
                class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                @click="confirmDelete(slotProps.data)"
              >
                <i class="pi pi-trash text-sm"/>
              </button>
            </div>
          </template>
        </Column>
        </DataTable>
      </div>

      <!-- Mobile: Cards View -->
      <div class="lg:hidden grid grid-cols-1 sm:grid-cols-2 gap-4">
        <ProductsProductCard
          v-for="product in filteredProducts"
          :key="product.id"
          :product="product"
          :selectable="true"
          :is-selected="selectedProducts.some(p => p.id === product.id)"
          @click="editProduct"
          @edit="editProduct"
          @delete="confirmDelete"
          @toggle-selection="toggleSelection"
        />

        <!-- Empty State for Mobile -->
        <div v-if="filteredProducts.length === 0" class="col-span-full">
          <Card class="shadow-md">
            <template #content>
              <EmptyState
                animation-type="empty-box"
                title="Aucun produit trouvé"
                description="Commencez par créer votre premier produit"
                action-label="Créer un produit"
                action-icon="pi pi-plus"
                @action="$router.push('/dashboard/products/create')"
              />
            </template>
          </Card>
        </div>
      </div>
    </div>

    <!-- Grid View -->
    <div v-else v-auto-animate class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 stagger-grid">
      <ProductsProductCard
        v-for="product in filteredProducts"
        :key="product.id"
        :product="product"
        :selectable="true"
        :is-selected="selectedProducts.some(p => p.id === product.id)"
        @click="editProduct"
        @edit="editProduct"
        @delete="confirmDelete"
        @toggle-selection="toggleSelection"
      />

      <!-- Empty State for Grid -->
      <div v-if="filteredProducts.length === 0" class="col-span-full">
        <Card class="shadow-md">
          <template #content>
            <EmptyState
              animation-type="empty-box"
              title="Aucun produit trouvé"
              description="Commencez par créer votre premier produit pour le voir apparaître ici"
              action-label="Créer votre premier produit"
              action-icon="pi pi-plus"
              @action="$router.push('/dashboard/products/create')"
            />
          </template>
        </Card>
      </div>
    </div>

    <!-- Delete Confirmation Dialog -->
    <Dialog
      v-model:visible="deleteDialog"
      :style="{ width: '450px' }"
      header="Confirmer la suppression"
      :modal="true"
    >
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle text-5xl text-secondary-500"/>
        <div>
          <p class="text-secondary-900">
            Êtes-vous sûr de vouloir supprimer
            <strong>{{ productToDelete?.title }}</strong> ?
          </p>
          <p class="text-sm text-secondary-600 mt-2">Cette action est irréversible.</p>
        </div>
      </div>
      <template #footer>
        <Button
          label="Annuler"
          icon="pi pi-times"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="deleteDialog = false"
        />
        <Button
          label="Supprimer"
          icon="pi pi-trash"
          class="bg-secondary-500 hover:bg-secondary-600 text-white border-0"
          :loading="isDeleting"
          @click="handleDelete"
        />
      </template>
    </Dialog>

    <!-- Bulk Delete Confirmation Dialog -->
    <Dialog
      v-model:visible="bulkDeleteDialog"
      :style="{ width: '450px' }"
      header="Confirmer la suppression multiple"
      :modal="true"
    >
      <div class="flex items-center gap-4">
        <i class="pi pi-exclamation-triangle text-5xl text-secondary-500"/>
        <div>
          <p class="text-secondary-900">
            Êtes-vous sûr de vouloir supprimer
            <strong>{{ selectedProducts.length }} produit(s)</strong> ?
          </p>
          <p class="text-sm text-secondary-600 mt-2">Cette action est irréversible.</p>
        </div>
      </div>
      <template #footer>
        <Button
          label="Annuler"
          icon="pi pi-times"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="bulkDeleteDialog = false"
        />
        <Button
          label="Supprimer tout"
          icon="pi pi-trash"
          class="bg-secondary-500 hover:bg-secondary-600 text-white border-0"
          :loading="isDeleting"
          @click="handleBulkDelete"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import type { Product } from '~/stores/products'
import { getProductImageUrl } from '~/stores/products'
import { useToast } from 'primevue/usetoast'

definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()
const { showSuccess, showError, showInfo, showWarn } = useAppToast()
const productsStore = useProductsStore()

// SSR-safe: useToast requires client-side ToastService
const toast = import.meta.client ? useToast() : null

// View mode
const viewMode = ref<'table' | 'grid'>('table')

// Pagination
const currentPage = ref(1)
const rowsPerPage = ref(20)

// Filters
const searchQuery = ref('')
const selectedCategory = ref<string | null>(null)
const selectedStatus = ref<string | null>(null)

// Selection
const selectedProducts = ref<Product[]>([])

// Delete dialogs
const deleteDialog = ref(false)
const bulkDeleteDialog = ref(false)
const productToDelete = ref<Product | null>(null)
const isDeleting = ref(false)

// Computed
const filteredProducts = computed(() => {
  let products = productsStore.products

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    products = products.filter(p =>
      p.title.toLowerCase().includes(query) ||
      p.brand.toLowerCase().includes(query) ||
      p.id.toString().includes(query)
    )
  }

  if (selectedCategory.value) {
    products = products.filter(p => p.category === selectedCategory.value)
  }

  if (selectedStatus.value) {
    const isActive = selectedStatus.value === 'active'
    products = products.filter(p => p.is_active === isActive)
  }

  return products
})

// Methods
const formatPrice = (price: number) => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(price)
}

const editProduct = (product: Product) => {
  router.push(`/dashboard/products/${product.id}/edit`)
}

const confirmDelete = (product: Product) => {
  productToDelete.value = product
  deleteDialog.value = true
}

const handleDelete = async () => {
  if (!productToDelete.value) return

  isDeleting.value = true
  try {
    await productsStore.deleteProduct(productToDelete.value.id)

    showSuccess('Produit supprimé', `${productToDelete.value.title} a été supprimé`, 3000)

    deleteDialog.value = false
    productToDelete.value = null
  } catch (error: any) {
    showError('Erreur', error.message || 'Impossible de supprimer le produit', 5000)
  } finally {
    isDeleting.value = false
  }
}

const confirmBulkDelete = () => {
  bulkDeleteDialog.value = true
}

const handleBulkDelete = async () => {
  isDeleting.value = true
  try {
    await Promise.all(
      selectedProducts.value.map(p => productsStore.deleteProduct(p.id))
    )

    showSuccess('Produits supprimés', `${selectedProducts.value.length} produit(s) supprimé(s)`, 3000)

    bulkDeleteDialog.value = false
    selectedProducts.value = []
  } catch (error: any) {
    showError('Erreur', 'Impossible de supprimer les produits', 5000)
  } finally {
    isDeleting.value = false
  }
}

const bulkActivate = async () => {
  try {
    await Promise.all(
      selectedProducts.value.map(p =>
        productsStore.updateProduct(p.id, { is_active: true })
      )
    )

    showSuccess('Produits activés', `${selectedProducts.value.length} produit(s) activé(s)`, 3000)

    selectedProducts.value = []
  } catch (error: any) {
    showError('Erreur', 'Impossible d\'activer les produits', 5000)
  }
}

const bulkDeactivate = async () => {
  try {
    await Promise.all(
      selectedProducts.value.map(p =>
        productsStore.updateProduct(p.id, { is_active: false })
      )
    )

    showSuccess('Produits désactivés', `${selectedProducts.value.length} produit(s) désactivé(s)`, 3000)

    selectedProducts.value = []
  } catch (error: any) {
    showError('Erreur', 'Impossible de désactiver les produits', 5000)
  }
}

const toggleSelection = (product: Product) => {
  const index = selectedProducts.value.findIndex(p => p.id === product.id)
  if (index > -1) {
    selectedProducts.value.splice(index, 1)
  } else {
    selectedProducts.value.push(product)
  }
}

// Pagination handler
const onPageChange = async (event: { page: number; rows: number }) => {
  currentPage.value = event.page + 1  // PrimeVue uses 0-based index
  rowsPerPage.value = event.rows
  await loadProducts()
}

// Load products with current pagination
const loadProducts = async () => {
  try {
    await productsStore.fetchProducts({
      page: currentPage.value,
      limit: rowsPerPage.value,
      status: selectedStatus.value || undefined,
      category: selectedCategory.value || undefined
    })
  } catch (error) {
    showError('Erreur', 'Impossible de charger les produits', 5000)
  }
}

// Watch filters to reload products
watch([selectedStatus, selectedCategory], async () => {
  currentPage.value = 1  // Reset to first page
  await loadProducts()
})

// Fetch products on mount
onMounted(async () => {
  await loadProducts()
})
</script>

<style scoped>
/* DataTable styling - clean minimal design */
:deep(.products-table) {
  .p-datatable-header {
    display: none;
  }

  .p-datatable-thead > tr > th {
    background: transparent;
    border: none;
    border-bottom: 1px solid #f3f4f6;
    padding: 0.75rem 1rem;
    font-weight: 500;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #9ca3af;
  }

  .p-datatable-tbody > tr {
    transition: background-color 0.1s ease;
  }

  .p-datatable-tbody > tr > td {
    border: none;
    border-bottom: 1px solid #f9fafb;
    padding: 0.75rem 1rem;
    vertical-align: middle;
  }

  .p-datatable-tbody > tr:hover {
    background: #fffbeb !important;
  }

  .p-datatable-tbody > tr:last-child > td {
    border-bottom: none;
  }

  /* Paginator */
  .p-paginator {
    background: #fafafa;
    border: none;
    border-top: 1px solid #f3f4f6;
    padding: 0.75rem 1rem;
    justify-content: flex-end;
    gap: 0.5rem;
  }

  .p-paginator .p-paginator-pages .p-paginator-page {
    min-width: 2rem;
    height: 2rem;
    border-radius: 0.375rem;
    margin: 0;
    font-size: 0.875rem;
    color: #6b7280;
  }

  .p-paginator .p-paginator-pages .p-paginator-page:hover {
    background: #f3f4f6;
  }

  .p-paginator .p-paginator-pages .p-paginator-page.p-highlight {
    background: #facc15;
    color: #1f2937;
    border-color: #facc15;
    font-weight: 600;
  }

  .p-paginator .p-dropdown {
    height: 2rem;
    border-radius: 0.375rem;
    border-color: #e5e7eb;
  }

  .p-paginator-first,
  .p-paginator-prev,
  .p-paginator-next,
  .p-paginator-last {
    min-width: 2rem;
    height: 2rem;
    border-radius: 0.375rem;
    color: #6b7280;
  }

  .p-paginator-first:hover,
  .p-paginator-prev:hover,
  .p-paginator-next:hover,
  .p-paginator-last:hover {
    background: #f3f4f6;
  }

  .p-paginator-current {
    font-size: 0.875rem;
    color: #6b7280;
  }

  /* Checkbox styling */
  .p-checkbox .p-checkbox-box {
    width: 1.125rem;
    height: 1.125rem;
    border-radius: 0.25rem;
    border-color: #d1d5db;
  }

  .p-checkbox .p-checkbox-box.p-highlight {
    background: #facc15;
    border-color: #facc15;
  }

  .p-checkbox .p-checkbox-box .p-checkbox-icon {
    color: #1f2937;
  }
}
</style>

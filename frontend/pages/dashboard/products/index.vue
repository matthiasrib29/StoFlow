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
    <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 stagger-grid">
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
        <ProductsDataTable
          v-model:selection="selectedProducts"
          :products="filteredProducts"
          :total-records="pagination.total"
          :current-page="currentPage"
          :rows-per-page="rowsPerPage"
          :loading="isLoading"
          @page="onPageChange"
          @edit="editProduct"
          @delete="confirmDelete"
          @create="$router.push('/dashboard/products/create')"
        />
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

    <!-- Delete Dialogs -->
    <ProductsDeleteDialogs
      v-model:delete-dialog-visible="deleteDialog"
      v-model:bulk-delete-dialog-visible="bulkDeleteDialog"
      :product-to-delete="productToDelete"
      :selected-count="selectedProducts.length"
      :loading="isDeleting"
      @delete="handleDelete"
      @bulk-delete="handleBulkDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { useProductsPage } from '~/composables/useProductsPage'

definePageMeta({
  layout: 'dashboard'
})

const {
  // State
  viewMode,
  currentPage,
  rowsPerPage,
  searchQuery,
  selectedCategory,
  selectedStatus,
  selectedProducts,
  deleteDialog,
  bulkDeleteDialog,
  productToDelete,
  isDeleting,

  // Computed
  filteredProducts,

  // Store proxies
  isLoading,
  pagination,

  // Methods
  loadProducts,
  editProduct,
  onPageChange,
  toggleSelection,
  confirmDelete,
  handleDelete,
  confirmBulkDelete,
  handleBulkDelete,
  bulkActivate,
  bulkDeactivate,
} = useProductsPage()

// Fetch products on mount
onMounted(async () => {
  await loadProducts()
})
</script>

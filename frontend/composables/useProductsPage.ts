import type { Product } from '~/stores/products'

export function useProductsPage() {
  const router = useRouter()
  const { showSuccess, showError } = useAppToast()
  const productsStore = useProductsStore()

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

  // Delete state
  const deleteDialog = ref(false)
  const bulkDeleteDialog = ref(false)
  const productToDelete = ref<Product | null>(null)
  const isDeleting = ref(false)

  // Computed - Filtered products
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

  // Edit product
  const editProduct = (product: Product) => {
    router.push(`/dashboard/products/${product.id}/edit`)
  }

  // Pagination handler
  const onPageChange = async (event: { page: number; rows: number }) => {
    currentPage.value = event.page + 1
    rowsPerPage.value = event.rows
    await loadProducts()
  }

  // Toggle selection
  const toggleSelection = (product: Product) => {
    const index = selectedProducts.value.findIndex(p => p.id === product.id)
    if (index > -1) {
      selectedProducts.value.splice(index, 1)
    } else {
      selectedProducts.value.push(product)
    }
  }

  // Single delete
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

  // Bulk delete
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

  // Bulk activate
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

  // Bulk deactivate
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

  // Watch filters to reload products
  watch([selectedStatus, selectedCategory], async () => {
    currentPage.value = 1
    await loadProducts()
  })

  return {
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
    isLoading: productsStore.isLoading,
    pagination: productsStore.pagination,

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
  }
}

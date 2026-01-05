/**
 * Composable for eBay products management.
 * Handles loading, importing, enriching products.
 */

export function useEbayProducts() {
  const { get, post } = useApi()
  const { showSuccess, showError, showInfo, showWarn } = useAppToast()

  // State
  const products = ref<any[]>([])
  const isLoading = ref(false)
  const isImporting = ref(false)
  const isEnriching = ref(false)
  const isRefreshingAspects = ref(false)
  const syncingProductId = ref<number | null>(null)
  const totalProducts = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const totalPages = ref(0)

  // Computed stats
  const productStats = computed(() => ({
    total: totalProducts.value,
    published: products.value.filter((p: any) => p.status === 'active').length,
    draft: products.value.filter((p: any) => p.status === 'inactive' || !p.status).length,
    outOfStock: products.value.filter((p: any) => (p.quantity || 0) === 0).length
  }))

  /**
   * Load products from API.
   */
  const loadProducts = async (page: number = 1): Promise<void> => {
    isLoading.value = true
    try {
      const response = await get<{
        items: any[]
        total: number
        page: number
        page_size: number
        total_pages: number
      }>(`/api/ebay/products?page=${page}&page_size=${pageSize.value}`)

      products.value = response?.items || []
      totalProducts.value = response?.total || 0
      currentPage.value = response?.page || 1
      totalPages.value = response?.total_pages || 0
    } catch (error: any) {
      console.error('Error loading eBay products:', error)
      showError('Erreur', 'Impossible de charger les produits eBay', 5000)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Handle page change from DataTable.
   */
  const onPageChange = (event: any): void => {
    const newPage = Math.floor(event.first / event.rows) + 1
    pageSize.value = event.rows
    loadProducts(newPage)
  }

  /**
   * Import products from eBay.
   */
  const importProducts = async (): Promise<void> => {
    isImporting.value = true
    try {
      const response = await post<{ imported_count: number }>('/api/ebay/products/import')
      showSuccess('Import terminé', `${response?.imported_count || 0} produit(s) importé(s)`, 3000)
      await loadProducts()
    } catch (error: any) {
      console.error('Error importing eBay products:', error)
      showError('Erreur', error.message || 'Impossible d\'importer les produits', 5000)
    } finally {
      isImporting.value = false
    }
  }

  /**
   * Enrich products with additional data.
   */
  const enrichProducts = async (): Promise<void> => {
    isEnriching.value = true
    try {
      const response = await post<{
        enriched: number
        errors: number
        remaining: number
      }>('/api/ebay/products/enrich')

      const { enriched, errors, remaining } = response || { enriched: 0, errors: 0, remaining: 0 }

      if (enriched > 0) {
        showSuccess('Enrichissement terminé', `${enriched} produit(s) enrichi(s). ${remaining} restant(s).`, 5000)
      } else if (remaining === 0) {
        showInfo('Terminé', 'Tous les produits ont déjà leurs prix', 3000)
      } else {
        showWarn('Avertissement', `${errors} erreur(s). Réessayez pour les ${remaining} restant(s).`, 5000)
      }

      await loadProducts()
    } catch (error: any) {
      console.error('Error enriching eBay products:', error)
      showError('Erreur', error.message || 'Impossible d\'enrichir les produits', 5000)
    } finally {
      isEnriching.value = false
    }
  }

  /**
   * Refresh product aspects (brands, etc.).
   */
  const refreshAspects = async (): Promise<void> => {
    isRefreshingAspects.value = true
    try {
      const response = await post<{
        updated: number
        errors: number
        remaining: number
      }>('/api/ebay/products/refresh-aspects?batch_size=500')

      const { updated, errors, remaining } = response || { updated: 0, errors: 0, remaining: 0 }

      if (updated > 0) {
        showSuccess('Marques corrigées', `${updated} produit(s) mis à jour. ${remaining} restant(s).`, 5000)
      } else if (remaining === 0) {
        showInfo('Terminé', 'Toutes les marques sont déjà renseignées', 3000)
      } else {
        showWarn('Avertissement', 'Aucun produit à corriger', 3000)
      }

      await loadProducts()
    } catch (error: any) {
      console.error('Error refreshing aspects:', error)
      showError('Erreur', error.message || 'Impossible de corriger les marques', 5000)
    } finally {
      isRefreshingAspects.value = false
    }
  }

  /**
   * Sync a single product to eBay.
   */
  const syncProduct = async (productId: number): Promise<boolean> => {
    syncingProductId.value = productId
    try {
      await post(`/api/ebay/products/${productId}/sync`)
      showSuccess('Synchronisé', 'Produit synchronisé avec eBay', 3000)
      await loadProducts(currentPage.value)
      return true
    } catch (error: any) {
      console.error('Error syncing product:', error)
      showError('Erreur', error.message || 'Impossible de synchroniser le produit', 5000)
      return false
    } finally {
      syncingProductId.value = null
    }
  }

  return {
    // State
    products: readonly(products),
    isLoading: readonly(isLoading),
    isImporting: readonly(isImporting),
    isEnriching: readonly(isEnriching),
    isRefreshingAspects: readonly(isRefreshingAspects),
    syncingProductId: readonly(syncingProductId),
    totalProducts: readonly(totalProducts),
    currentPage: readonly(currentPage),
    pageSize,
    totalPages: readonly(totalPages),
    productStats,

    // Methods
    loadProducts,
    onPageChange,
    importProducts,
    enrichProducts,
    refreshAspects,
    syncProduct
  }
}

/**
 * Composable for Vinted product synchronization.
 * Extracted from vinted/index.vue to reduce file size.
 */

export interface SyncStats {
  created: number
  updated: number
  enriched: number
  enrichment_errors: number
  errors: number
}

export interface SyncResult {
  timestamp: string
  stats?: SyncStats
  syncResponse?: any
  products?: any[]
  totalProducts?: number
  error?: boolean
  message?: string
  details?: any
}

export function useVintedSync() {
  const { get, post } = useApi()
  const { showSuccess, showError, showInfo } = useAppToast()

  // State
  const syncLoading = ref(false)
  const syncedProducts = ref<any[]>([])
  const rawSyncResult = ref<SyncResult | null>(null)
  const syncModalVisible = ref(false)

  /**
   * Synchronize products from Vinted via plugin.
   * Fetches products and stores raw result for display.
   */
  const syncProducts = async (): Promise<SyncResult | null> => {
    try {
      syncLoading.value = true
      rawSyncResult.value = null

      showInfo('Synchronisation en cours', 'Récupération des produits depuis Vinted via le plugin...', 5000)

      // 1. Call sync endpoint
      const syncResponse = await post<SyncStats>('/vinted/products/sync')

      // 2. Fetch products from DB
      const productsResponse = await get<{ products: any[]; total: number }>('/vinted/products?limit=100')

      // 3. Store complete raw result
      const result: SyncResult = {
        timestamp: new Date().toISOString(),
        stats: {
          created: syncResponse.created || 0,
          updated: syncResponse.updated || 0,
          enriched: syncResponse.enriched || 0,
          enrichment_errors: syncResponse.enrichment_errors || 0,
          errors: syncResponse.errors || 0
        },
        syncResponse,
        products: productsResponse.products || [],
        totalProducts: productsResponse.total || 0
      }

      rawSyncResult.value = result
      syncedProducts.value = productsResponse.products || []

      const totalProcessed = (syncResponse.created || 0) + (syncResponse.updated || 0)
      const enriched = syncResponse.enriched || 0
      showSuccess(
        'Synchronisation terminée',
        `${totalProcessed} produit(s) synchronisé(s)${enriched > 0 ? `, ${enriched} enrichi(s)` : ''}`,
        5000
      )

      return result

    } catch (error: any) {
      // Store error in raw result
      rawSyncResult.value = {
        timestamp: new Date().toISOString(),
        error: true,
        message: error.message || 'Erreur inconnue',
        details: error
      }

      showError('Erreur de synchronisation', error.message || 'Échec de la synchronisation', 5000)
      return null

    } finally {
      syncLoading.value = false
    }
  }

  /**
   * Quick sync without raw result display.
   */
  const quickSync = async (): Promise<boolean> => {
    try {
      syncLoading.value = true
      syncedProducts.value = []

      showInfo('Synchronisation', 'Récupération de vos produits Vinted...', 3000)

      const syncResponse = await post<SyncStats>('/vinted/products/sync')
      const productsResponse = await get<{ products: any[]; total: number }>('/vinted/products?limit=100')

      syncedProducts.value = productsResponse.products || []

      const totalSynced = (syncResponse.created || 0) + (syncResponse.updated || 0)
      const enrichedCount = syncResponse.enriched || 0
      showSuccess(
        'Synchronisé',
        `${totalSynced} produit(s) synchronisé(s)${enrichedCount > 0 ? `, ${enrichedCount} enrichi(s)` : ''}`,
        5000
      )

      if (syncedProducts.value.length > 0) {
        syncModalVisible.value = true
      }

      return true

    } catch (error: any) {
      showError('Erreur de synchronisation', error.message || 'Échec de la synchronisation', 5000)
      return false

    } finally {
      syncLoading.value = false
    }
  }

  /**
   * Copy raw result JSON to clipboard.
   */
  const copyRawResult = async (): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(rawSyncResult.value, null, 2))
      showSuccess('Copié', 'Résultat JSON copié dans le presse-papiers', 2000)
      return true
    } catch {
      showError('Erreur', 'Impossible de copier', 2000)
      return false
    }
  }

  /**
   * Copy synced products JSON to clipboard.
   */
  const copySyncedProducts = async (): Promise<boolean> => {
    try {
      const jsonString = JSON.stringify(syncedProducts.value, null, 2)
      await navigator.clipboard.writeText(jsonString)
      showSuccess('Copié', 'Le JSON a été copié dans le presse-papier', 2000)
      return true
    } catch {
      showError('Erreur', 'Impossible de copier le JSON', 3000)
      return false
    }
  }

  /**
   * Clear sync results.
   */
  const clearSyncResult = () => {
    rawSyncResult.value = null
  }

  const clearSyncedProducts = () => {
    syncedProducts.value = []
  }

  return {
    // State
    syncLoading: readonly(syncLoading),
    syncedProducts: readonly(syncedProducts),
    rawSyncResult: readonly(rawSyncResult),
    syncModalVisible,

    // Methods
    syncProducts,
    quickSync,
    copyRawResult,
    copySyncedProducts,
    clearSyncResult,
    clearSyncedProducts
  }
}

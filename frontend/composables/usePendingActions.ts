/**
 * Composable for managing pending actions (confirmation queue).
 *
 * Provides API calls and state management for the pending actions
 * widget on the dashboard. Users can confirm or reject actions
 * detected by marketplace sync workflows.
 */

export interface PendingActionProduct {
  id: number
  title: string
  price: number
  brand: string | null
  status: string
  image_url: string | null
}

export interface PendingAction {
  id: number
  product_id: number
  action_type: string
  marketplace: string
  reason: string | null
  context_data: Record<string, any> | null
  previous_status: string | null
  detected_at: string
  confirmed_at: string | null
  confirmed_by: string | null
  is_confirmed: boolean | null
  product: PendingActionProduct | null
}

export interface PendingActionCount {
  count: number
}

export interface BulkActionResponse {
  processed: number
  total: number
}

export interface ActionResultResponse {
  success: boolean
  product_id: number
  new_status: string
}

const PAGE_SIZE = 20

export function usePendingActions() {
  const { get, post } = useApi()
  const { showSuccess, showError } = useAppToast()

  // State
  const pendingActions = ref<PendingAction[]>([])
  const pendingCount = ref(0)
  const currentPage = ref(1)
  const isLoading = ref(false)

  // Computed
  const totalPages = computed(() => Math.max(1, Math.ceil(pendingCount.value / PAGE_SIZE)))

  /**
   * Fetch the count of pending actions (for badge display).
   */
  async function fetchCount(): Promise<number> {
    try {
      const response = await get<PendingActionCount>('/pending-actions/count')
      pendingCount.value = response.count
      return response.count
    } catch (e) {
      console.error('Failed to fetch pending actions count:', e)
      return 0
    }
  }

  /**
   * Fetch a page of pending actions.
   */
  async function fetchPendingActions(page = 1): Promise<PendingAction[]> {
    isLoading.value = true
    try {
      // Fetch count first to know total
      await fetchCount()

      const offset = (page - 1) * PAGE_SIZE
      const response = await get<PendingAction[]>(`/pending-actions?limit=${PAGE_SIZE}&offset=${offset}`)
      pendingActions.value = response
      currentPage.value = page
      return response
    } catch (e) {
      console.error('Failed to fetch pending actions:', e)
      return []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Go to next page.
   */
  async function nextPage() {
    if (currentPage.value < totalPages.value) {
      await fetchPendingActions(currentPage.value + 1)
    }
  }

  /**
   * Go to previous page.
   */
  async function prevPage() {
    if (currentPage.value > 1) {
      await fetchPendingActions(currentPage.value - 1)
    }
  }

  /**
   * Confirm a single pending action (apply the status change).
   */
  async function confirmAction(actionId: number): Promise<boolean> {
    try {
      await post<ActionResultResponse>(`/pending-actions/${actionId}/confirm`)
      // Remove from local list
      pendingActions.value = pendingActions.value.filter(a => a.id !== actionId)
      pendingCount.value = Math.max(0, pendingCount.value - 1)
      showSuccess('Action confirmée', 'Le produit a été marqué comme vendu.')

      // If page is now empty and not first page, go back
      if (pendingActions.value.length === 0 && currentPage.value > 1) {
        await fetchPendingActions(currentPage.value - 1)
      }
      return true
    } catch (e) {
      showError('Erreur', 'Impossible de confirmer cette action.')
      return false
    }
  }

  /**
   * Reject a single pending action (restore product).
   */
  async function rejectAction(actionId: number): Promise<boolean> {
    try {
      await post<ActionResultResponse>(`/pending-actions/${actionId}/reject`)
      // Remove from local list
      pendingActions.value = pendingActions.value.filter(a => a.id !== actionId)
      pendingCount.value = Math.max(0, pendingCount.value - 1)
      showSuccess('Action restaurée', 'Le produit a été restauré à son statut précédent.')

      // If page is now empty and not first page, go back
      if (pendingActions.value.length === 0 && currentPage.value > 1) {
        await fetchPendingActions(currentPage.value - 1)
      }
      return true
    } catch (e) {
      showError('Erreur', 'Impossible de restaurer ce produit.')
      return false
    }
  }

  /**
   * Confirm ALL pending actions across all pages.
   * Uses the /confirm-all endpoint (no IDs needed).
   */
  async function confirmAllPending(): Promise<boolean> {
    try {
      const response = await post<BulkActionResponse>('/pending-actions/confirm-all')
      pendingActions.value = []
      pendingCount.value = 0
      currentPage.value = 1
      showSuccess('Tout confirmé', `${response.processed} produits marqués comme vendus.`)
      return true
    } catch (e) {
      showError('Erreur', 'Impossible de confirmer les actions en masse.')
      return false
    }
  }

  /**
   * Confirm visible page actions only.
   */
  async function bulkConfirmAll(): Promise<boolean> {
    const ids = pendingActions.value.map(a => a.id)
    if (ids.length === 0) return true

    try {
      const response = await post<BulkActionResponse>('/pending-actions/bulk-confirm', { action_ids: ids })
      showSuccess('Page confirmée', `${response.processed} actions confirmées.`)
      // Reload current page (or go back if was last page)
      await fetchPendingActions(Math.min(currentPage.value, Math.max(1, totalPages.value - 1)))
      return true
    } catch (e) {
      showError('Erreur', 'Impossible de confirmer les actions en masse.')
      return false
    }
  }

  /**
   * Reject visible page actions only.
   */
  async function bulkRejectAll(): Promise<boolean> {
    const ids = pendingActions.value.map(a => a.id)
    if (ids.length === 0) return true

    try {
      const response = await post<BulkActionResponse>('/pending-actions/bulk-reject', { action_ids: ids })
      showSuccess('Page restaurée', `${response.processed} produits restaurés.`)
      // Reload current page
      await fetchPendingActions(Math.min(currentPage.value, Math.max(1, totalPages.value - 1)))
      return true
    } catch (e) {
      showError('Erreur', 'Impossible de restaurer les produits en masse.')
      return false
    }
  }

  /**
   * Get a human-readable label for action type.
   */
  function getActionTypeLabel(actionType: string): string {
    const labels: Record<string, string> = {
      mark_sold: 'Vendu',
      delete: 'Supprimé',
      archive: 'Archivé',
      delete_vinted_listing: 'Supprimer de Vinted',
      delete_ebay_listing: 'Supprimer d\'eBay',
    }
    return labels[actionType] || actionType
  }

  /**
   * Get a human-readable label for marketplace.
   */
  function getMarketplaceLabel(marketplace: string): string {
    const labels: Record<string, string> = {
      vinted: 'Vinted',
      ebay: 'eBay',
      etsy: 'Etsy',
    }
    return labels[marketplace] || marketplace
  }

  /**
   * Get a contextual description for a pending action.
   * Differentiates between "sold on marketplace" vs "sold on StoFlow, delete from marketplace".
   */
  function getActionDescription(action: PendingAction): string {
    switch (action.action_type) {
      case 'delete_vinted_listing':
        return 'Vendu sur StoFlow — à supprimer de Vinted'
      case 'delete_ebay_listing':
        return 'Vendu sur StoFlow — à supprimer d\'eBay'
      case 'mark_sold':
        return `Vendu sur ${getMarketplaceLabel(action.marketplace)}`
      default:
        return `${getActionTypeLabel(action.action_type)} sur ${getMarketplaceLabel(action.marketplace)}`
    }
  }

  /**
   * Get the confirm button label for a pending action.
   */
  function getConfirmLabel(action: PendingAction): string {
    switch (action.action_type) {
      case 'delete_vinted_listing':
        return 'Supprimer de Vinted'
      case 'delete_ebay_listing':
        return 'Supprimer d\'eBay'
      case 'mark_sold':
        return 'Marquer vendu'
      default:
        return 'Confirmer'
    }
  }

  return {
    // State
    pendingActions,
    pendingCount,
    currentPage,
    totalPages,
    isLoading,
    // Actions
    fetchCount,
    fetchPendingActions,
    nextPage,
    prevPage,
    confirmAction,
    rejectAction,
    confirmAllPending,
    bulkConfirmAll,
    bulkRejectAll,
    // Helpers
    getActionTypeLabel,
    getMarketplaceLabel,
    getActionDescription,
    getConfirmLabel,
  }
}

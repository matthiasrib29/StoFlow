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

export function usePendingActions() {
  const { get, post } = useApi()
  const { showSuccess, showError } = useAppToast()

  // State
  const pendingActions = ref<PendingAction[]>([])
  const pendingCount = ref(0)
  const isLoading = ref(false)

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
   * Fetch the list of pending actions.
   */
  async function fetchPendingActions(limit = 50): Promise<PendingAction[]> {
    isLoading.value = true
    try {
      const response = await get<PendingAction[]>(`/pending-actions?limit=${limit}`)
      pendingActions.value = response
      pendingCount.value = response.length
      return response
    } catch (e) {
      console.error('Failed to fetch pending actions:', e)
      return []
    } finally {
      isLoading.value = false
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
      return true
    } catch (e) {
      showError('Erreur', 'Impossible de restaurer ce produit.')
      return false
    }
  }

  /**
   * Confirm all pending actions at once.
   */
  async function bulkConfirmAll(): Promise<boolean> {
    const ids = pendingActions.value.map(a => a.id)
    if (ids.length === 0) return true

    try {
      const response = await post<BulkActionResponse>('/pending-actions/bulk-confirm', {
        body: JSON.stringify({ action_ids: ids }),
      })
      pendingActions.value = []
      pendingCount.value = 0
      showSuccess('Tout confirmé', `${response.processed} actions confirmées.`)
      return true
    } catch (e) {
      showError('Erreur', 'Impossible de confirmer les actions en masse.')
      return false
    }
  }

  /**
   * Reject all pending actions at once (restore all products).
   */
  async function bulkRejectAll(): Promise<boolean> {
    const ids = pendingActions.value.map(a => a.id)
    if (ids.length === 0) return true

    try {
      const response = await post<BulkActionResponse>('/pending-actions/bulk-reject', {
        body: JSON.stringify({ action_ids: ids }),
      })
      pendingActions.value = []
      pendingCount.value = 0
      showSuccess('Tout restauré', `${response.processed} produits restaurés.`)
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

  return {
    // State
    pendingActions,
    pendingCount,
    isLoading,
    // Actions
    fetchCount,
    fetchPendingActions,
    confirmAction,
    rejectAction,
    bulkConfirmAll,
    bulkRejectAll,
    // Helpers
    getActionTypeLabel,
    getMarketplaceLabel,
  }
}

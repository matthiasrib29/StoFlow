/**
 * Composable for eBay returns management
 *
 * Provides API methods for:
 * - Fetching and listing returns
 * - Syncing returns from eBay
 * - Return actions (accept, decline, refund, mark received, send message)
 * - Statistics
 */

import type {
  EbayReturn,
  EbayReturnListResponse,
  EbayReturnStatistics,
  EbayReturnSyncResponse,
  EbayReturnActionResponse,
  EbayReturnStatus
} from '~/types/ebay'

interface FetchReturnsParams {
  page?: number
  page_size?: number
  state?: 'OPEN' | 'CLOSED' | null
  status?: string | null
  needs_action?: boolean
  past_deadline?: boolean
}

interface SyncReturnsParams {
  days_back?: number
  return_state?: 'OPEN' | 'CLOSED' | null
}

export const useEbayReturns = () => {
  const api = useApi()

  // =========================================================================
  // FETCH METHODS
  // =========================================================================

  /**
   * Fetch returns with pagination and filters
   */
  const fetchReturns = async (
    params: FetchReturnsParams = {}
  ): Promise<EbayReturnListResponse> => {
    const queryParams: Record<string, string | number | boolean> = {}

    if (params.page) queryParams.page = params.page
    if (params.page_size) queryParams.page_size = params.page_size
    if (params.state) queryParams.state = params.state
    if (params.status) queryParams.status = params.status

    return await api.get<EbayReturnListResponse>('/ebay/returns', {
      params: queryParams
    })
  }

  /**
   * Fetch a single return by ID
   */
  const fetchReturn = async (returnId: number): Promise<EbayReturn> => {
    return await api.get<EbayReturn>(`/ebay/returns/${returnId}`)
  }

  /**
   * Fetch returns needing action
   */
  const fetchReturnsNeedingAction = async (
    limit: number = 100
  ): Promise<EbayReturn[]> => {
    return await api.get<EbayReturn[]>('/ebay/returns/needs-action', {
      params: { limit }
    })
  }

  /**
   * Fetch returns past deadline
   */
  const fetchReturnsPastDeadline = async (
    limit: number = 100
  ): Promise<EbayReturn[]> => {
    return await api.get<EbayReturn[]>('/ebay/returns/past-deadline', {
      params: { limit }
    })
  }

  /**
   * Fetch return statistics
   */
  const fetchStatistics = async (): Promise<EbayReturnStatistics> => {
    return await api.get<EbayReturnStatistics>('/ebay/returns/statistics')
  }

  // =========================================================================
  // SYNC METHOD
  // =========================================================================

  /**
   * Sync returns from eBay
   */
  const syncReturns = async (
    params: SyncReturnsParams = {}
  ): Promise<EbayReturnSyncResponse> => {
    const body: Record<string, unknown> = {}

    if (params.days_back) body.days_back = params.days_back
    if (params.return_state) body.return_state = params.return_state

    return await api.post<EbayReturnSyncResponse>('/ebay/returns/sync', body)
  }

  // =========================================================================
  // ACTION METHODS
  // =========================================================================

  /**
   * Accept a return
   */
  const acceptReturn = async (
    returnId: number,
    options: { comments?: string; rma_number?: string } = {}
  ): Promise<EbayReturnActionResponse> => {
    return await api.post<EbayReturnActionResponse>(
      `/ebay/returns/${returnId}/accept`,
      options
    )
  }

  /**
   * Decline a return
   */
  const declineReturn = async (
    returnId: number,
    comments: string
  ): Promise<EbayReturnActionResponse> => {
    return await api.post<EbayReturnActionResponse>(
      `/ebay/returns/${returnId}/decline`,
      { comments }
    )
  }

  /**
   * Issue a refund
   */
  const issueRefund = async (
    returnId: number,
    options: {
      refund_amount?: number
      currency?: string
      comments?: string
    } = {}
  ): Promise<EbayReturnActionResponse> => {
    return await api.post<EbayReturnActionResponse>(
      `/ebay/returns/${returnId}/refund`,
      options
    )
  }

  /**
   * Mark return item as received
   */
  const markAsReceived = async (
    returnId: number,
    comments?: string
  ): Promise<EbayReturnActionResponse> => {
    return await api.post<EbayReturnActionResponse>(
      `/ebay/returns/${returnId}/received`,
      { comments }
    )
  }

  /**
   * Send message to buyer
   */
  const sendMessage = async (
    returnId: number,
    message: string
  ): Promise<EbayReturnActionResponse> => {
    return await api.post<EbayReturnActionResponse>(
      `/ebay/returns/${returnId}/message`,
      { message }
    )
  }

  // =========================================================================
  // HELPER METHODS
  // =========================================================================

  /**
   * Get human-readable label for return status
   */
  const getStatusLabel = (status: EbayReturnStatus | null): string => {
    if (!status) return 'Inconnu'

    const labels: Record<EbayReturnStatus, string> = {
      RETURN_REQUESTED: 'Demandé',
      RETURN_WAITING_FOR_RMA: 'Attente RMA',
      RETURN_ACCEPTED: 'Accepté',
      RETURN_DECLINED: 'Refusé',
      RETURN_ITEM_SHIPPED: 'Article expédié',
      RETURN_ITEM_DELIVERED: 'Article reçu',
      RETURN_CLOSED: 'Fermé',
      RETURN_CANCELLED: 'Annulé'
    }

    return labels[status] || status
  }

  /**
   * Get PrimeVue Tag severity for return status
   */
  const getStatusSeverity = (
    status: EbayReturnStatus | null
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' => {
    if (!status) return 'secondary'

    const severities: Record<
      EbayReturnStatus,
      'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'
    > = {
      RETURN_REQUESTED: 'warn',
      RETURN_WAITING_FOR_RMA: 'warn',
      RETURN_ACCEPTED: 'info',
      RETURN_DECLINED: 'danger',
      RETURN_ITEM_SHIPPED: 'info',
      RETURN_ITEM_DELIVERED: 'success',
      RETURN_CLOSED: 'secondary',
      RETURN_CANCELLED: 'secondary'
    }

    return severities[status] || 'secondary'
  }

  /**
   * Get human-readable label for return state
   */
  const getStateLabel = (state: 'OPEN' | 'CLOSED' | null): string => {
    if (!state) return 'Inconnu'
    return state === 'OPEN' ? 'Ouvert' : 'Fermé'
  }

  /**
   * Get PrimeVue Tag severity for return state
   */
  const getStateSeverity = (
    state: 'OPEN' | 'CLOSED' | null
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' => {
    if (!state) return 'secondary'
    return state === 'OPEN' ? 'warn' : 'secondary'
  }

  /**
   * Check if a return requires immediate action
   */
  const requiresAction = (ret: EbayReturn): boolean => {
    return ret.needs_action || ret.is_past_deadline
  }

  /**
   * Get reason display text
   */
  const getReasonLabel = (reason: string | null): string => {
    if (!reason) return 'Non spécifié'

    // Map common eBay reason codes to French labels
    const reasonLabels: Record<string, string> = {
      ITEM_NOT_AS_DESCRIBED: 'Article non conforme',
      ITEM_NOT_RECEIVED: 'Article non reçu',
      BUYER_REMORSE: 'Changement d\'avis',
      DEFECTIVE_ITEM: 'Article défectueux',
      WRONG_ITEM_SENT: 'Mauvais article envoyé',
      MISSING_PARTS: 'Pièces manquantes',
      ARRIVED_DAMAGED: 'Arrivé endommagé',
      OTHER: 'Autre'
    }

    return reasonLabels[reason] || reason
  }

  return {
    // Fetch methods
    fetchReturns,
    fetchReturn,
    fetchReturnsNeedingAction,
    fetchReturnsPastDeadline,
    fetchStatistics,
    // Sync method
    syncReturns,
    // Action methods
    acceptReturn,
    declineReturn,
    issueRefund,
    markAsReceived,
    sendMessage,
    // Helper methods
    getStatusLabel,
    getStatusSeverity,
    getStateLabel,
    getStateSeverity,
    requiresAction,
    getReasonLabel
  }
}

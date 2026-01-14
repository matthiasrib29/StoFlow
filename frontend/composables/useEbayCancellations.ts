/**
 * Composable for eBay cancellations management
 *
 * Provides API methods for:
 * - Fetching and listing cancellations
 * - Syncing cancellations from eBay
 * - Cancellation actions (approve, reject, create)
 * - Eligibility check
 * - Statistics
 */

import type {
  EbayCancellation,
  EbayCancellationListResponse,
  EbayCancellationStatistics,
  EbayCancellationSyncResponse,
  EbayCancellationActionResponse,
  EbayCancellationEligibilityResponse,
  EbayCancellationStatus,
  EbayCancellationReason,
  EbayCancellationRejectReason
} from '~/types/ebay'

interface FetchCancellationsParams {
  page?: number
  page_size?: number
  state?: 'CLOSED' | null
  status?: string | null
  order_id?: string | null
}

interface SyncCancellationsParams {
  days_back?: number
  cancel_state?: 'CLOSED' | null
}

export const useEbayCancellations = () => {
  const api = useApi()

  // =========================================================================
  // FETCH METHODS
  // =========================================================================

  /**
   * Fetch cancellations with pagination and filters
   */
  const fetchCancellations = async (
    params: FetchCancellationsParams = {}
  ): Promise<EbayCancellationListResponse> => {
    const queryParams: Record<string, string | number | boolean> = {}

    if (params.page) queryParams.page = params.page
    if (params.page_size) queryParams.page_size = params.page_size
    if (params.state) queryParams.state = params.state
    if (params.status) queryParams.status = params.status
    if (params.order_id) queryParams.order_id = params.order_id

    return await api.get<EbayCancellationListResponse>('/ebay/cancellations', {
      params: queryParams
    })
  }

  /**
   * Fetch a single cancellation by ID
   */
  const fetchCancellation = async (cancellationId: number): Promise<EbayCancellation> => {
    return await api.get<EbayCancellation>(`/ebay/cancellations/${cancellationId}`)
  }

  /**
   * Fetch cancellations needing action
   */
  const fetchCancellationsNeedingAction = async (
    limit: number = 100
  ): Promise<EbayCancellationListResponse> => {
    return await api.get<EbayCancellationListResponse>('/ebay/cancellations/needs-action', {
      params: { limit }
    })
  }

  /**
   * Fetch cancellations past due
   */
  const fetchCancellationsPastDue = async (
    limit: number = 100
  ): Promise<EbayCancellationListResponse> => {
    return await api.get<EbayCancellationListResponse>('/ebay/cancellations/past-due', {
      params: { limit }
    })
  }

  /**
   * Fetch cancellation statistics
   */
  const fetchStatistics = async (): Promise<EbayCancellationStatistics> => {
    return await api.get<EbayCancellationStatistics>('/ebay/cancellations/statistics')
  }

  // =========================================================================
  // SYNC METHOD
  // =========================================================================

  /**
   * Sync cancellations from eBay
   */
  const syncCancellations = async (
    params: SyncCancellationsParams = {}
  ): Promise<EbayCancellationSyncResponse> => {
    const body: Record<string, unknown> = {}

    if (params.days_back) body.days_back = params.days_back
    if (params.cancel_state) body.cancel_state = params.cancel_state

    return await api.post<EbayCancellationSyncResponse>('/ebay/cancellations/sync', body)
  }

  // =========================================================================
  // ACTION METHODS
  // =========================================================================

  /**
   * Check if an order is eligible for cancellation
   */
  const checkEligibility = async (
    orderId: string
  ): Promise<EbayCancellationEligibilityResponse> => {
    return await api.post<EbayCancellationEligibilityResponse>(
      '/ebay/cancellations/check-eligibility',
      { order_id: orderId }
    )
  }

  /**
   * Create a seller-initiated cancellation
   */
  const createCancellation = async (
    orderId: string,
    reason: EbayCancellationReason,
    comments?: string
  ): Promise<EbayCancellationActionResponse> => {
    return await api.post<EbayCancellationActionResponse>(
      '/ebay/cancellations/create',
      {
        order_id: orderId,
        reason,
        comments
      }
    )
  }

  /**
   * Approve a buyer's cancellation request
   */
  const approveCancellation = async (
    cancellationId: number,
    comments?: string
  ): Promise<EbayCancellationActionResponse> => {
    return await api.post<EbayCancellationActionResponse>(
      `/ebay/cancellations/${cancellationId}/approve`,
      { comments }
    )
  }

  /**
   * Reject a buyer's cancellation request
   */
  const rejectCancellation = async (
    cancellationId: number,
    reason: EbayCancellationRejectReason,
    options: {
      tracking_number?: string
      carrier?: string
      comments?: string
    } = {}
  ): Promise<EbayCancellationActionResponse> => {
    return await api.post<EbayCancellationActionResponse>(
      `/ebay/cancellations/${cancellationId}/reject`,
      {
        reason,
        ...options
      }
    )
  }

  // =========================================================================
  // HELPER METHODS
  // =========================================================================

  /**
   * Get human-readable label for cancellation status
   */
  const getStatusLabel = (status: EbayCancellationStatus | null): string => {
    if (!status) return 'Inconnu'

    const labels: Record<EbayCancellationStatus, string> = {
      CANCEL_REQUESTED: 'Demandée',
      CANCEL_PENDING: 'En attente',
      CANCEL_CLOSED_WITH_REFUND: 'Approuvée (remboursé)',
      CANCEL_CLOSED_UNKNOWN_REFUND: 'Approuvée (remboursement inconnu)',
      CANCEL_CLOSED_NO_REFUND: 'Approuvée (sans remboursement)',
      CANCEL_REJECTED: 'Rejetée'
    }

    return labels[status] || status
  }

  /**
   * Get PrimeVue Tag severity for cancellation status
   */
  const getStatusSeverity = (
    status: EbayCancellationStatus | null
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' => {
    if (!status) return 'secondary'

    const severities: Record<
      EbayCancellationStatus,
      'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'
    > = {
      CANCEL_REQUESTED: 'warn',
      CANCEL_PENDING: 'warn',
      CANCEL_CLOSED_WITH_REFUND: 'success',
      CANCEL_CLOSED_UNKNOWN_REFUND: 'info',
      CANCEL_CLOSED_NO_REFUND: 'info',
      CANCEL_REJECTED: 'danger'
    }

    return severities[status] || 'secondary'
  }

  /**
   * Get human-readable label for cancellation reason
   */
  const getReasonLabel = (reason: string | null): string => {
    if (!reason) return 'Non spécifié'

    const reasonLabels: Record<string, string> = {
      OUT_OF_STOCK: 'Rupture de stock',
      ADDRESS_ISSUES: 'Problème d\'adresse',
      BUYER_ASKED_CANCEL: 'Demande de l\'acheteur',
      ORDER_UNPAID: 'Commande non payée',
      OTHER_SELLER_CANCEL_REASON: 'Autre raison',
      ALREADY_SHIPPED: 'Déjà expédié',
      OTHER_SELLER_REJECT_REASON: 'Autre raison de refus'
    }

    return reasonLabels[reason] || reason
  }

  /**
   * Get human-readable label for requestor role
   */
  const getRequestorLabel = (role: string | null): string => {
    if (!role) return 'Inconnu'
    return role === 'BUYER' ? 'Acheteur' : 'Vendeur'
  }

  /**
   * Get PrimeVue Tag severity for requestor role
   */
  const getRequestorSeverity = (
    role: string | null
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' => {
    if (!role) return 'secondary'
    return role === 'BUYER' ? 'info' : 'secondary'
  }

  /**
   * Check if a cancellation requires immediate action
   */
  const requiresAction = (cancellation: EbayCancellation): boolean => {
    return cancellation.needs_action || cancellation.is_past_response_due
  }

  /**
   * Format refund amount
   */
  const formatRefundAmount = (cancellation: EbayCancellation): string => {
    if (!cancellation.refund_amount) return '-'
    const currency = cancellation.refund_currency || 'EUR'
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency
    }).format(cancellation.refund_amount)
  }

  /**
   * Get state label
   */
  const getStateLabel = (state: 'CLOSED' | null): string => {
    return state === 'CLOSED' ? 'Fermée' : 'Active'
  }

  /**
   * Get state severity
   */
  const getStateSeverity = (
    state: 'CLOSED' | null
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' => {
    return state === 'CLOSED' ? 'secondary' : 'warn'
  }

  return {
    // Fetch methods
    fetchCancellations,
    fetchCancellation,
    fetchCancellationsNeedingAction,
    fetchCancellationsPastDue,
    fetchStatistics,
    // Sync method
    syncCancellations,
    // Action methods
    checkEligibility,
    createCancellation,
    approveCancellation,
    rejectCancellation,
    // Helper methods
    getStatusLabel,
    getStatusSeverity,
    getReasonLabel,
    getRequestorLabel,
    getRequestorSeverity,
    requiresAction,
    formatRefundAmount,
    getStateLabel,
    getStateSeverity
  }
}

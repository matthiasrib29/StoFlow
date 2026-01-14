/**
 * Composable for eBay refunds management
 *
 * Provides API methods for:
 * - Fetching and listing refunds
 * - Syncing refunds from eBay orders
 * - Issuing new refunds
 * - Statistics
 */

import type {
  EbayRefund,
  EbayRefundListResponse,
  EbayRefundStatistics,
  EbayRefundSyncResponse,
  EbayRefundIssueResponse,
  EbayRefundStatus,
  EbayRefundSource,
  EbayRefundReason
} from '~/types/ebay'

interface FetchRefundsParams {
  page?: number
  page_size?: number
  status?: EbayRefundStatus | null
  source?: EbayRefundSource | null
  order_id?: string | null
}

interface SyncRefundsParams {
  days_back?: number
}

interface SyncRefundsFromOrderParams {
  order_id: string
}

interface IssueRefundParams {
  order_id: string
  reason: EbayRefundReason
  amount: number
  currency?: string
  line_item_id?: string | null
  comment?: string | null
}

export const useEbayRefunds = () => {
  const api = useApi()

  // =========================================================================
  // FETCH METHODS
  // =========================================================================

  /**
   * Fetch refunds with pagination and filters
   */
  const fetchRefunds = async (
    params: FetchRefundsParams = {}
  ): Promise<EbayRefundListResponse> => {
    const queryParams: Record<string, string | number | boolean> = {}

    if (params.page) queryParams.page = params.page
    if (params.page_size) queryParams.page_size = params.page_size
    if (params.status) queryParams.status = params.status
    if (params.source) queryParams.source = params.source
    if (params.order_id) queryParams.order_id = params.order_id

    return await api.get<EbayRefundListResponse>('/ebay/refunds', {
      params: queryParams
    })
  }

  /**
   * Fetch a single refund by ID
   */
  const fetchRefund = async (refundId: number): Promise<EbayRefund> => {
    return await api.get<EbayRefund>(`/ebay/refunds/${refundId}`)
  }

  /**
   * Fetch pending refunds
   */
  const fetchPendingRefunds = async (
    limit: number = 100
  ): Promise<EbayRefundListResponse> => {
    return await api.get<EbayRefundListResponse>('/ebay/refunds/pending', {
      params: { limit }
    })
  }

  /**
   * Fetch failed refunds
   */
  const fetchFailedRefunds = async (
    limit: number = 100
  ): Promise<EbayRefundListResponse> => {
    return await api.get<EbayRefundListResponse>('/ebay/refunds/failed', {
      params: { limit }
    })
  }

  /**
   * Fetch refund statistics
   */
  const fetchStatistics = async (): Promise<EbayRefundStatistics> => {
    return await api.get<EbayRefundStatistics>('/ebay/refunds/statistics')
  }

  // =========================================================================
  // SYNC METHODS
  // =========================================================================

  /**
   * Sync refunds from recent orders
   */
  const syncRefunds = async (
    params: SyncRefundsParams = {}
  ): Promise<EbayRefundSyncResponse> => {
    const body: Record<string, unknown> = {}

    if (params.days_back) body.days_back = params.days_back

    return await api.post<EbayRefundSyncResponse>('/ebay/refunds/sync', body)
  }

  /**
   * Sync refunds from a specific order
   */
  const syncRefundsFromOrder = async (
    params: SyncRefundsFromOrderParams
  ): Promise<EbayRefundSyncResponse> => {
    return await api.post<EbayRefundSyncResponse>('/ebay/refunds/sync-order', {
      order_id: params.order_id
    })
  }

  // =========================================================================
  // ACTION METHODS
  // =========================================================================

  /**
   * Issue a new refund
   */
  const issueRefund = async (
    params: IssueRefundParams
  ): Promise<EbayRefundIssueResponse> => {
    return await api.post<EbayRefundIssueResponse>('/ebay/refunds/issue', {
      order_id: params.order_id,
      reason: params.reason,
      amount: params.amount,
      currency: params.currency || 'EUR',
      line_item_id: params.line_item_id,
      comment: params.comment
    })
  }

  // =========================================================================
  // HELPER METHODS
  // =========================================================================

  /**
   * Get human-readable label for refund status
   */
  const getStatusLabel = (status: EbayRefundStatus | null): string => {
    if (!status) return 'Inconnu'

    const labels: Record<EbayRefundStatus, string> = {
      PENDING: 'En attente',
      REFUNDED: 'Remboursé',
      FAILED: 'Échoué'
    }

    return labels[status] || status
  }

  /**
   * Get PrimeVue Tag severity for refund status
   */
  const getStatusSeverity = (
    status: EbayRefundStatus | null
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' => {
    if (!status) return 'secondary'

    const severities: Record<
      EbayRefundStatus,
      'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'
    > = {
      PENDING: 'warn',
      REFUNDED: 'success',
      FAILED: 'danger'
    }

    return severities[status] || 'secondary'
  }

  /**
   * Get human-readable label for refund source
   */
  const getSourceLabel = (source: EbayRefundSource | null): string => {
    if (!source) return 'Inconnu'

    const labels: Record<EbayRefundSource, string> = {
      RETURN: 'Retour',
      CANCELLATION: 'Annulation',
      MANUAL: 'Manuel',
      OTHER: 'Autre'
    }

    return labels[source] || source
  }

  /**
   * Get PrimeVue Tag severity for refund source
   */
  const getSourceSeverity = (
    source: EbayRefundSource | null
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' => {
    if (!source) return 'secondary'

    const severities: Record<
      EbayRefundSource,
      'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'
    > = {
      RETURN: 'info',
      CANCELLATION: 'warn',
      MANUAL: 'contrast',
      OTHER: 'secondary'
    }

    return severities[source] || 'secondary'
  }

  /**
   * Get human-readable label for refund reason
   */
  const getReasonLabel = (reason: string | null): string => {
    if (!reason) return 'Non spécifié'

    const labels: Record<string, string> = {
      BUYER_CANCEL: 'Annulation acheteur',
      BUYER_RETURN: 'Retour acheteur',
      ITEM_NOT_RECEIVED: 'Non reçu',
      SELLER_WRONG_ITEM: 'Mauvais article',
      SELLER_OUT_OF_STOCK: 'Rupture de stock',
      SELLER_FOUND_ISSUE: 'Problème détecté',
      OTHER: 'Autre'
    }

    return labels[reason] || reason
  }

  /**
   * Format refund amount
   */
  const formatAmount = (refund: EbayRefund): string => {
    if (!refund.refund_amount) return '-'
    const currency = refund.refund_currency || 'EUR'
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency
    }).format(refund.refund_amount)
  }

  /**
   * Format date
   */
  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return '-'
    try {
      return new Intl.DateTimeFormat('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(new Date(dateStr))
    } catch {
      return dateStr
    }
  }

  /**
   * Get icon for refund source
   */
  const getSourceIcon = (source: EbayRefundSource | null): string => {
    if (!source) return 'pi pi-question-circle'

    const icons: Record<EbayRefundSource, string> = {
      RETURN: 'pi pi-replay',
      CANCELLATION: 'pi pi-times-circle',
      MANUAL: 'pi pi-user',
      OTHER: 'pi pi-question-circle'
    }

    return icons[source] || 'pi pi-question-circle'
  }

  /**
   * Get available reason options for the issue refund form
   */
  const getReasonOptions = () => [
    { label: 'Annulation acheteur', value: 'BUYER_CANCEL' },
    { label: 'Retour acheteur', value: 'BUYER_RETURN' },
    { label: 'Article non reçu', value: 'ITEM_NOT_RECEIVED' },
    { label: 'Mauvais article envoyé', value: 'SELLER_WRONG_ITEM' },
    { label: 'Rupture de stock', value: 'SELLER_OUT_OF_STOCK' },
    { label: 'Problème détecté par vendeur', value: 'SELLER_FOUND_ISSUE' },
    { label: 'Autre raison', value: 'OTHER' }
  ]

  return {
    // Fetch methods
    fetchRefunds,
    fetchRefund,
    fetchPendingRefunds,
    fetchFailedRefunds,
    fetchStatistics,
    // Sync methods
    syncRefunds,
    syncRefundsFromOrder,
    // Action methods
    issueRefund,
    // Helper methods
    getStatusLabel,
    getStatusSeverity,
    getSourceLabel,
    getSourceSeverity,
    getReasonLabel,
    formatAmount,
    formatDate,
    getSourceIcon,
    getReasonOptions
  }
}

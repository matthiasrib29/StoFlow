/**
 * Composable for eBay payment disputes management
 *
 * Provides API methods for:
 * - Fetching and listing payment disputes
 * - Syncing disputes from eBay
 * - Accepting and contesting disputes
 * - Adding evidence
 * - Statistics
 */

import type {
  EbayPaymentDispute,
  EbayPaymentDisputeListResponse,
  EbayPaymentDisputeStatistics,
  EbayPaymentDisputeSyncResponse,
  EbayPaymentDisputeActionResponse,
  EbayPaymentDisputeEvidenceResponse,
  EbayPaymentDisputeState,
  EbayPaymentDisputeEvidenceType
} from '~/types/ebay'

interface FetchDisputesParams {
  page?: number
  page_size?: number
  state?: EbayPaymentDisputeState | null
  order_id?: string | null
}

interface ContestDisputeParams {
  evidence_type: EbayPaymentDisputeEvidenceType
  evidence_info?: string | null
  comment?: string | null
}

interface AddEvidenceParams {
  evidence_type: EbayPaymentDisputeEvidenceType
  evidence_info: string
  description?: string | null
}

export const useEbayPaymentDisputes = () => {
  const api = useApi()

  // =========================================================================
  // FETCH METHODS
  // =========================================================================

  /**
   * Fetch payment disputes with pagination and filters
   */
  const fetchDisputes = async (
    params: FetchDisputesParams = {}
  ): Promise<EbayPaymentDisputeListResponse> => {
    const queryParams: Record<string, string | number | boolean> = {}

    if (params.page) queryParams.page = params.page
    if (params.page_size) queryParams.page_size = params.page_size
    if (params.state) queryParams.state = params.state
    if (params.order_id) queryParams.order_id = params.order_id

    return await api.get<EbayPaymentDisputeListResponse>(
      '/ebay/payment-disputes',
      { params: queryParams }
    )
  }

  /**
   * Fetch a single payment dispute by ID
   */
  const fetchDispute = async (
    disputeId: number
  ): Promise<EbayPaymentDispute> => {
    return await api.get<EbayPaymentDispute>(
      `/ebay/payment-disputes/${disputeId}`
    )
  }

  /**
   * Fetch urgent disputes (ACTION_NEEDED or past due)
   */
  const fetchUrgentDisputes = async (
    limit: number = 100
  ): Promise<EbayPaymentDisputeListResponse> => {
    return await api.get<EbayPaymentDisputeListResponse>(
      '/ebay/payment-disputes/urgent',
      { params: { limit } }
    )
  }

  /**
   * Fetch payment dispute statistics
   */
  const fetchStatistics = async (): Promise<EbayPaymentDisputeStatistics> => {
    return await api.get<EbayPaymentDisputeStatistics>(
      '/ebay/payment-disputes/statistics'
    )
  }

  // =========================================================================
  // SYNC METHODS
  // =========================================================================

  /**
   * Sync all payment disputes from eBay
   */
  const syncDisputes = async (): Promise<EbayPaymentDisputeSyncResponse> => {
    return await api.post<EbayPaymentDisputeSyncResponse>(
      '/ebay/payment-disputes/sync'
    )
  }

  /**
   * Sync a single dispute from eBay
   */
  const syncDispute = async (
    disputeId: string
  ): Promise<EbayPaymentDisputeSyncResponse> => {
    return await api.post<EbayPaymentDisputeSyncResponse>(
      `/ebay/payment-disputes/sync/${disputeId}`
    )
  }

  // =========================================================================
  // ACTION METHODS
  // =========================================================================

  /**
   * Accept a payment dispute (seller agrees with buyer claim)
   */
  const acceptDispute = async (
    disputeId: number,
    comment?: string | null
  ): Promise<EbayPaymentDisputeActionResponse> => {
    return await api.post<EbayPaymentDisputeActionResponse>(
      `/ebay/payment-disputes/${disputeId}/accept`,
      { comment }
    )
  }

  /**
   * Contest a payment dispute (seller disagrees with buyer claim)
   */
  const contestDispute = async (
    disputeId: number,
    params: ContestDisputeParams
  ): Promise<EbayPaymentDisputeActionResponse> => {
    return await api.post<EbayPaymentDisputeActionResponse>(
      `/ebay/payment-disputes/${disputeId}/contest`,
      {
        evidence_type: params.evidence_type,
        evidence_info: params.evidence_info,
        comment: params.comment
      }
    )
  }

  /**
   * Add evidence to a payment dispute
   */
  const addEvidence = async (
    disputeId: number,
    params: AddEvidenceParams
  ): Promise<EbayPaymentDisputeEvidenceResponse> => {
    return await api.post<EbayPaymentDisputeEvidenceResponse>(
      `/ebay/payment-disputes/${disputeId}/add-evidence`,
      {
        evidence_type: params.evidence_type,
        evidence_info: params.evidence_info,
        description: params.description
      }
    )
  }

  // =========================================================================
  // HELPER METHODS
  // =========================================================================

  /**
   * Get human-readable label for dispute state
   */
  const getStateLabel = (state: EbayPaymentDisputeState | null): string => {
    if (!state) return 'Inconnu'

    const labels: Record<EbayPaymentDisputeState, string> = {
      OPEN: 'Ouvert',
      ACTION_NEEDED: 'Action requise',
      CLOSED: 'Fermé'
    }

    return labels[state] || state
  }

  /**
   * Get PrimeVue Tag severity for dispute state
   */
  const getStateSeverity = (
    state: EbayPaymentDisputeState | null
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' => {
    if (!state) return 'secondary'

    const severities: Record<
      EbayPaymentDisputeState,
      'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'
    > = {
      OPEN: 'info',
      ACTION_NEEDED: 'danger',
      CLOSED: 'success'
    }

    return severities[state] || 'secondary'
  }

  /**
   * Get human-readable label for dispute reason
   */
  const getReasonLabel = (reason: string | null): string => {
    if (!reason) return 'Non spécifié'

    const labels: Record<string, string> = {
      ITEM_NOT_RECEIVED: 'Article non reçu',
      ITEM_SIGNIFICANTLY_NOT_AS_DESCRIBED: 'Article non conforme',
      UNAUTHORIZED_TRANSACTION: 'Transaction non autorisée',
      DUPLICATE_TRANSACTION: 'Transaction dupliquée',
      CREDIT_NOT_PROCESSED: 'Crédit non traité',
      MERCHANDISE_NOT_AS_DESCRIBED: 'Marchandise non conforme',
      MERCHANDISE_NOT_RECEIVED: 'Marchandise non reçue',
      OTHER: 'Autre'
    }

    return labels[reason] || reason
  }

  /**
   * Get human-readable label for seller response
   */
  const getSellerResponseLabel = (response: string | null): string => {
    if (!response) return 'Aucune réponse'

    const labels: Record<string, string> = {
      CONTEST: 'Contesté',
      ACCEPT: 'Accepté'
    }

    return labels[response] || response
  }

  /**
   * Get PrimeVue Tag severity for seller response
   */
  const getSellerResponseSeverity = (
    response: string | null
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' => {
    if (!response) return 'secondary'

    const severities: Record<
      string,
      'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'
    > = {
      CONTEST: 'warn',
      ACCEPT: 'info'
    }

    return severities[response] || 'secondary'
  }

  /**
   * Get human-readable label for evidence type
   */
  const getEvidenceTypeLabel = (type: string | null): string => {
    if (!type) return 'Non spécifié'

    const labels: Record<string, string> = {
      PROOF_OF_DELIVERY: 'Preuve de livraison',
      PROOF_OF_AUTHENTICITY: "Preuve d'authenticité",
      PROOF_OF_ITEM_AS_DESCRIBED: 'Preuve de conformité',
      PROOF_OF_PICKUP: "Preuve d'enlèvement",
      TRACKING_INFORMATION: 'Informations de suivi'
    }

    return labels[type] || type
  }

  /**
   * Get icon for dispute state
   */
  const getStateIcon = (state: EbayPaymentDisputeState | null): string => {
    if (!state) return 'pi pi-question-circle'

    const icons: Record<EbayPaymentDisputeState, string> = {
      OPEN: 'pi pi-exclamation-circle',
      ACTION_NEEDED: 'pi pi-exclamation-triangle',
      CLOSED: 'pi pi-check-circle'
    }

    return icons[state] || 'pi pi-question-circle'
  }

  /**
   * Get icon for dispute reason
   */
  const getReasonIcon = (reason: string | null): string => {
    if (!reason) return 'pi pi-question-circle'

    const icons: Record<string, string> = {
      ITEM_NOT_RECEIVED: 'pi pi-inbox',
      ITEM_SIGNIFICANTLY_NOT_AS_DESCRIBED: 'pi pi-image',
      UNAUTHORIZED_TRANSACTION: 'pi pi-lock',
      DUPLICATE_TRANSACTION: 'pi pi-copy',
      CREDIT_NOT_PROCESSED: 'pi pi-credit-card',
      MERCHANDISE_NOT_AS_DESCRIBED: 'pi pi-image',
      MERCHANDISE_NOT_RECEIVED: 'pi pi-inbox',
      OTHER: 'pi pi-question-circle'
    }

    return icons[reason] || 'pi pi-question-circle'
  }

  /**
   * Format dispute amount
   */
  const formatAmount = (dispute: EbayPaymentDispute): string => {
    if (!dispute.dispute_amount) return '-'
    const currency = dispute.dispute_currency || 'EUR'
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency
    }).format(dispute.dispute_amount)
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
   * Get available evidence type options for forms
   */
  const getEvidenceTypeOptions = () => [
    { label: 'Preuve de livraison', value: 'PROOF_OF_DELIVERY' },
    { label: "Preuve d'authenticité", value: 'PROOF_OF_AUTHENTICITY' },
    { label: 'Preuve de conformité', value: 'PROOF_OF_ITEM_AS_DESCRIBED' },
    { label: "Preuve d'enlèvement", value: 'PROOF_OF_PICKUP' },
    { label: 'Informations de suivi', value: 'TRACKING_INFORMATION' }
  ]

  /**
   * Check if a dispute needs urgent attention
   */
  const isUrgent = (dispute: EbayPaymentDispute): boolean => {
    return (
      dispute.needs_action ||
      dispute.is_past_due ||
      dispute.dispute_state === 'ACTION_NEEDED'
    )
  }

  /**
   * Get days until response deadline
   */
  const getDaysUntilDeadline = (dispute: EbayPaymentDispute): number | null => {
    if (!dispute.response_due_date) return null
    const now = new Date()
    const deadline = new Date(dispute.response_due_date)
    const diffTime = deadline.getTime() - now.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  return {
    // Fetch methods
    fetchDisputes,
    fetchDispute,
    fetchUrgentDisputes,
    fetchStatistics,
    // Sync methods
    syncDisputes,
    syncDispute,
    // Action methods
    acceptDispute,
    contestDispute,
    addEvidence,
    // Helper methods
    getStateLabel,
    getStateSeverity,
    getReasonLabel,
    getSellerResponseLabel,
    getSellerResponseSeverity,
    getEvidenceTypeLabel,
    getStateIcon,
    getReasonIcon,
    formatAmount,
    formatDate,
    getEvidenceTypeOptions,
    isUrgent,
    getDaysUntilDeadline
  }
}

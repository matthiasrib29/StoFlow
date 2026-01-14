/**
 * Composable for eBay INR inquiries management
 *
 * Provides API methods for:
 * - Fetching and listing inquiries
 * - Syncing inquiries from eBay
 * - Providing shipment info
 * - Providing refunds
 * - Sending messages
 * - Escalating to cases
 * - Statistics
 */

import type {
  EbayInquiry,
  EbayInquiryListResponse,
  EbayInquiryStatistics,
  EbayInquirySyncResponse,
  EbayInquiryActionResponse,
  EbayInquiryState,
  EbayInquiryStatus
} from '~/types/ebay'

interface FetchInquiriesParams {
  page?: number
  page_size?: number
  state?: EbayInquiryState | null
  status?: EbayInquiryStatus | null
  order_id?: string | null
}

interface ProvideShipmentInfoParams {
  tracking_number: string
  carrier: string
  shipped_date?: string | null
  comments?: string | null
}

interface ProvideRefundParams {
  refund_amount?: number | null
  currency?: string | null
  comments?: string | null
}

export const useEbayInquiries = () => {
  const api = useApi()

  // =========================================================================
  // FETCH METHODS
  // =========================================================================

  /**
   * Fetch inquiries with pagination and filters
   */
  const fetchInquiries = async (
    params: FetchInquiriesParams = {}
  ): Promise<EbayInquiryListResponse> => {
    const queryParams: Record<string, string | number | boolean> = {}

    if (params.page) queryParams.page = params.page
    if (params.page_size) queryParams.page_size = params.page_size
    if (params.state) queryParams.state = params.state
    if (params.status) queryParams.status = params.status
    if (params.order_id) queryParams.order_id = params.order_id

    return await api.get<EbayInquiryListResponse>('/ebay/inquiries', {
      params: queryParams
    })
  }

  /**
   * Fetch a single inquiry by ID
   */
  const fetchInquiry = async (inquiryId: number): Promise<EbayInquiry> => {
    return await api.get<EbayInquiry>(`/ebay/inquiries/${inquiryId}`)
  }

  /**
   * Fetch inquiries needing seller action
   */
  const fetchNeedsAction = async (
    limit: number = 100
  ): Promise<EbayInquiryListResponse> => {
    return await api.get<EbayInquiryListResponse>('/ebay/inquiries/needs-action', {
      params: { limit }
    })
  }

  /**
   * Fetch inquiries past deadline
   */
  const fetchPastDeadline = async (
    limit: number = 100
  ): Promise<EbayInquiryListResponse> => {
    return await api.get<EbayInquiryListResponse>('/ebay/inquiries/past-deadline', {
      params: { limit }
    })
  }

  /**
   * Fetch inquiry statistics
   */
  const fetchStatistics = async (): Promise<EbayInquiryStatistics> => {
    return await api.get<EbayInquiryStatistics>('/ebay/inquiries/statistics')
  }

  // =========================================================================
  // SYNC METHODS
  // =========================================================================

  /**
   * Sync all inquiries from eBay
   */
  const syncInquiries = async (
    state?: EbayInquiryState | null
  ): Promise<EbayInquirySyncResponse> => {
    const body = state ? { inquiry_state: state } : {}
    return await api.post<EbayInquirySyncResponse>('/ebay/inquiries/sync', body)
  }

  // =========================================================================
  // ACTION METHODS
  // =========================================================================

  /**
   * Provide shipment tracking information for an inquiry
   */
  const provideShipmentInfo = async (
    inquiryId: number,
    params: ProvideShipmentInfoParams
  ): Promise<EbayInquiryActionResponse> => {
    return await api.post<EbayInquiryActionResponse>(
      `/ebay/inquiries/${inquiryId}/shipment-info`,
      {
        tracking_number: params.tracking_number,
        carrier: params.carrier,
        shipped_date: params.shipped_date,
        comments: params.comments
      }
    )
  }

  /**
   * Provide refund for an inquiry
   */
  const provideRefund = async (
    inquiryId: number,
    params: ProvideRefundParams = {}
  ): Promise<EbayInquiryActionResponse> => {
    return await api.post<EbayInquiryActionResponse>(
      `/ebay/inquiries/${inquiryId}/refund`,
      {
        refund_amount: params.refund_amount,
        currency: params.currency,
        comments: params.comments
      }
    )
  }

  /**
   * Send message to buyer about inquiry
   */
  const sendMessage = async (
    inquiryId: number,
    message: string
  ): Promise<EbayInquiryActionResponse> => {
    return await api.post<EbayInquiryActionResponse>(
      `/ebay/inquiries/${inquiryId}/message`,
      { message }
    )
  }

  /**
   * Escalate inquiry to an eBay case
   */
  const escalateInquiry = async (
    inquiryId: number,
    comments?: string | null
  ): Promise<EbayInquiryActionResponse> => {
    return await api.post<EbayInquiryActionResponse>(
      `/ebay/inquiries/${inquiryId}/escalate`,
      { comments }
    )
  }

  // =========================================================================
  // HELPER METHODS
  // =========================================================================

  /**
   * Get human-readable label for inquiry state
   */
  const getStateLabel = (state: EbayInquiryState | null): string => {
    if (!state) return 'Inconnu'

    const labels: Record<EbayInquiryState, string> = {
      OPEN: 'Ouvert',
      CLOSED: 'Fermé'
    }

    return labels[state] || state
  }

  /**
   * Get PrimeVue Tag severity for inquiry state
   */
  const getStateSeverity = (
    state: EbayInquiryState | null
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' => {
    if (!state) return 'secondary'

    const severities: Record<
      EbayInquiryState,
      'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'
    > = {
      OPEN: 'warn',
      CLOSED: 'success'
    }

    return severities[state] || 'secondary'
  }

  /**
   * Get human-readable label for inquiry status
   */
  const getStatusLabel = (status: EbayInquiryStatus | string | null): string => {
    if (!status) return 'Inconnu'

    const labels: Record<string, string> = {
      INR_WAITING_FOR_SELLER: 'En attente vendeur',
      INR_WAITING_FOR_BUYER: 'En attente acheteur',
      INR_CLOSED_SELLER_PROVIDED_INFO: 'Fermé - Info fournie',
      INR_CLOSED_REFUND: 'Fermé - Remboursé',
      INR_CLOSED_BUYER_CONFIRMED: 'Fermé - Acheteur confirmé',
      INR_CLOSED_ITEM_DELIVERED: 'Fermé - Article livré',
      INR_ESCALATED: 'Escaladé'
    }

    return labels[status] || status
  }

  /**
   * Get PrimeVue Tag severity for inquiry status
   */
  const getStatusSeverity = (
    status: EbayInquiryStatus | string | null
  ): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' => {
    if (!status) return 'secondary'

    const severities: Record<
      string,
      'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast'
    > = {
      INR_WAITING_FOR_SELLER: 'danger',
      INR_WAITING_FOR_BUYER: 'info',
      INR_CLOSED_SELLER_PROVIDED_INFO: 'success',
      INR_CLOSED_REFUND: 'success',
      INR_CLOSED_BUYER_CONFIRMED: 'success',
      INR_CLOSED_ITEM_DELIVERED: 'success',
      INR_ESCALATED: 'danger'
    }

    return severities[status] || 'secondary'
  }

  /**
   * Get icon for inquiry state
   */
  const getStateIcon = (state: EbayInquiryState | null): string => {
    if (!state) return 'pi pi-question-circle'

    const icons: Record<EbayInquiryState, string> = {
      OPEN: 'pi pi-exclamation-circle',
      CLOSED: 'pi pi-check-circle'
    }

    return icons[state] || 'pi pi-question-circle'
  }

  /**
   * Get icon for inquiry status
   */
  const getStatusIcon = (status: EbayInquiryStatus | string | null): string => {
    if (!status) return 'pi pi-question-circle'

    const icons: Record<string, string> = {
      INR_WAITING_FOR_SELLER: 'pi pi-clock',
      INR_WAITING_FOR_BUYER: 'pi pi-user-edit',
      INR_CLOSED_SELLER_PROVIDED_INFO: 'pi pi-check',
      INR_CLOSED_REFUND: 'pi pi-money-bill',
      INR_CLOSED_BUYER_CONFIRMED: 'pi pi-thumbs-up',
      INR_CLOSED_ITEM_DELIVERED: 'pi pi-truck',
      INR_ESCALATED: 'pi pi-exclamation-triangle'
    }

    return icons[status] || 'pi pi-question-circle'
  }

  /**
   * Format inquiry amount
   */
  const formatAmount = (inquiry: EbayInquiry): string => {
    if (!inquiry.claim_amount) return '-'
    const currency = inquiry.claim_currency || 'EUR'
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency
    }).format(inquiry.claim_amount)
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
   * Get available carrier options for forms
   */
  const getCarrierOptions = () => [
    { label: 'UPS', value: 'UPS' },
    { label: 'FedEx', value: 'FEDEX' },
    { label: 'DHL', value: 'DHL' },
    { label: 'La Poste', value: 'LA_POSTE' },
    { label: 'Colissimo', value: 'COLISSIMO' },
    { label: 'Chronopost', value: 'CHRONOPOST' },
    { label: 'Mondial Relay', value: 'MONDIAL_RELAY' },
    { label: 'GLS', value: 'GLS' },
    { label: 'USPS', value: 'USPS' },
    { label: 'Royal Mail', value: 'ROYAL_MAIL' },
    { label: 'Deutsche Post', value: 'DEUTSCHE_POST' },
    { label: 'Autre', value: 'OTHER' }
  ]

  /**
   * Check if an inquiry needs urgent attention
   */
  const isUrgent = (inquiry: EbayInquiry): boolean => {
    return inquiry.needs_action || inquiry.is_past_due || inquiry.is_escalated
  }

  /**
   * Get days until response deadline
   */
  const getDaysUntilDeadline = (inquiry: EbayInquiry): number | null => {
    if (!inquiry.respond_by_date) return null
    const now = new Date()
    const deadline = new Date(inquiry.respond_by_date)
    const diffTime = deadline.getTime() - now.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  /**
   * Get deadline urgency level
   */
  const getDeadlineUrgency = (
    inquiry: EbayInquiry
  ): 'danger' | 'warn' | 'info' | null => {
    const days = getDaysUntilDeadline(inquiry)
    if (days === null) return null
    if (days <= 0) return 'danger'
    if (days <= 2) return 'warn'
    return 'info'
  }

  return {
    // Fetch methods
    fetchInquiries,
    fetchInquiry,
    fetchNeedsAction,
    fetchPastDeadline,
    fetchStatistics,
    // Sync methods
    syncInquiries,
    // Action methods
    provideShipmentInfo,
    provideRefund,
    sendMessage,
    escalateInquiry,
    // Helper methods
    getStateLabel,
    getStateSeverity,
    getStatusLabel,
    getStatusSeverity,
    getStateIcon,
    getStatusIcon,
    formatAmount,
    formatDate,
    getCarrierOptions,
    isUrgent,
    getDaysUntilDeadline,
    getDeadlineUrgency
  }
}

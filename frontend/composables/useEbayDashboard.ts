/**
 * Composable for eBay unified dashboard
 *
 * Provides API calls for fetching unified statistics, urgent items,
 * and recent activity across all post-sale domains.
 *
 * @returns {Object} Dashboard functions and helpers
 */

import type {
  EbayDashboardStatistics,
  EbayUrgentItemsResponse,
  EbayUrgentItem,
  EbayRecentActivityResponse,
  EbayActivityItem
} from '~/types/ebay'

export function useEbayDashboard() {
  const config = useRuntimeConfig()
  const { token } = useAuth()

  const apiBase = `${config.public.apiUrl}/ebay/dashboard`

  // =========================================================================
  // API CALLS
  // =========================================================================

  /**
   * Fetch unified statistics across all domains
   */
  async function fetchStatistics(): Promise<EbayDashboardStatistics> {
    const response = await $fetch<EbayDashboardStatistics>(`${apiBase}/statistics`, {
      headers: {
        Authorization: `Bearer ${token.value}`
      }
    })
    return response
  }

  /**
   * Fetch urgent items requiring action
   */
  async function fetchUrgentItems(limit: number = 20): Promise<EbayUrgentItemsResponse> {
    const response = await $fetch<EbayUrgentItemsResponse>(`${apiBase}/urgent`, {
      headers: {
        Authorization: `Bearer ${token.value}`
      },
      params: { limit }
    })
    return response
  }

  /**
   * Fetch recent activity timeline
   */
  async function fetchRecentActivity(limit: number = 20): Promise<EbayRecentActivityResponse> {
    const response = await $fetch<EbayRecentActivityResponse>(`${apiBase}/activity`, {
      headers: {
        Authorization: `Bearer ${token.value}`
      },
      params: { limit }
    })
    return response
  }

  // =========================================================================
  // HELPERS
  // =========================================================================

  /**
   * Get type label in French
   */
  function getTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      return: 'Retour',
      cancellation: 'Annulation',
      refund: 'Remboursement',
      payment_dispute: 'Litige',
      inquiry: 'INR'
    }
    return labels[type] || type
  }

  /**
   * Get type icon
   */
  function getTypeIcon(type: string): string {
    const icons: Record<string, string> = {
      return: 'pi pi-replay',
      cancellation: 'pi pi-times-circle',
      refund: 'pi pi-euro',
      payment_dispute: 'pi pi-exclamation-triangle',
      inquiry: 'pi pi-inbox'
    }
    return icons[type] || 'pi pi-circle'
  }

  /**
   * Get type route
   */
  function getTypeRoute(type: string, id: number): string {
    const routes: Record<string, string> = {
      return: `/dashboard/platforms/ebay/returns/${id}`,
      cancellation: `/dashboard/platforms/ebay/cancellations/${id}`,
      refund: `/dashboard/platforms/ebay/refunds/${id}`,
      payment_dispute: `/dashboard/platforms/ebay/payment-disputes/${id}`,
      inquiry: `/dashboard/platforms/ebay/inquiries/${id}`
    }
    return routes[type] || `/dashboard/platforms/ebay`
  }

  /**
   * Get urgency severity for PrimeVue Tag
   */
  function getUrgencySeverity(urgency: string): 'danger' | 'warn' | 'secondary' {
    if (urgency === 'critical') return 'danger'
    if (urgency === 'high') return 'warn'
    return 'secondary'
  }

  /**
   * Get urgency label in French
   */
  function getUrgencyLabel(urgency: string): string {
    const labels: Record<string, string> = {
      critical: 'Critique',
      high: 'Urgent'
    }
    return labels[urgency] || urgency
  }

  /**
   * Format amount with currency
   */
  function formatAmount(item: EbayUrgentItem | EbayActivityItem): string {
    let amount: number | null | undefined
    let currency: string | null | undefined

    if ('refund_amount' in item && item.refund_amount) {
      amount = item.refund_amount
      currency = item.refund_currency
    } else if ('dispute_amount' in item && item.dispute_amount) {
      amount = item.dispute_amount
      currency = item.dispute_currency
    } else if ('claim_amount' in item && item.claim_amount) {
      amount = item.claim_amount
      currency = item.claim_currency
    } else if ('amount' in item && item.amount) {
      amount = item.amount
      currency = item.currency
    }

    if (!amount) return '-'

    const formatter = new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: currency || 'EUR'
    })
    return formatter.format(amount)
  }

  /**
   * Format date for display
   */
  function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return new Intl.DateTimeFormat('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  /**
   * Format date short (without time)
   */
  function formatDateShort(dateStr: string | null | undefined): string {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return new Intl.DateTimeFormat('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }).format(date)
  }

  /**
   * Get relative time (e.g., "il y a 2 heures")
   */
  function getRelativeTime(dateStr: string | null | undefined): string {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return "à l'instant"
    if (diffMins < 60) return `il y a ${diffMins} min`
    if (diffHours < 24) return `il y a ${diffHours}h`
    if (diffDays === 1) return 'hier'
    if (diffDays < 7) return `il y a ${diffDays} jours`
    return formatDateShort(dateStr)
  }

  /**
   * Get external ID based on type
   */
  function getExternalId(item: EbayUrgentItem): string {
    if (item.return_id) return item.return_id
    if (item.cancel_id) return item.cancel_id
    if (item.dispute_id) return item.dispute_id
    if (item.inquiry_id) return item.inquiry_id
    return '-'
  }

  /**
   * Get status display
   */
  function getStatusDisplay(item: EbayUrgentItem | EbayActivityItem): string {
    if (!item.status) return '-'
    // Simplify status for display
    const status = item.status
      .replace('RETURN_', '')
      .replace('CANCEL_', '')
      .replace('INR_', '')
      .replace(/_/g, ' ')
      .toLowerCase()
    return status.charAt(0).toUpperCase() + status.slice(1)
  }

  return {
    // API
    fetchStatistics,
    fetchUrgentItems,
    fetchRecentActivity,
    // Helpers
    getTypeLabel,
    getTypeIcon,
    getTypeRoute,
    getUrgencySeverity,
    getUrgencyLabel,
    formatAmount,
    formatDate,
    formatDateShort,
    getRelativeTime,
    getExternalId,
    getStatusDisplay
  }
}

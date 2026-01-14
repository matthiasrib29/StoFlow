/**
 * Types for eBay integration
 * Extracted from stores/ebay.ts for better organization
 */

export interface EbayAccount {
  userId: string
  username: string
  email: string
  accountType: 'individual' | 'business'
  registrationDate: string
  sellerLevel: 'top_rated' | 'above_standard' | 'standard' | 'below_standard'
  feedbackScore: number
  feedbackPercentage: number
  storeName?: string
  storeUrl?: string
  // Additional info from Commerce Identity API
  firstName?: string
  lastName?: string
  businessName?: string
  phone?: string
  address?: string
  marketplace?: string
  programs?: Array<{ programType: string }>
  fulfillmentPoliciesCount?: number
  accessTokenExpiresAt?: string
  sandboxMode?: boolean
}

export interface EbayTokens {
  accessToken: string
  refreshToken: string
  expiresAt: string
  scope: string[]
}

export interface EbayShippingPolicy {
  id: string
  name: string
  description?: string
  type: 'flat_rate' | 'calculated' | 'free_shipping'
  domesticShipping: {
    service: string
    cost: number
    additionalCost?: number
    handlingTime: number
  }
  internationalShipping?: {
    enabled: boolean
    service?: string
    cost?: number
    countries?: string[]
  }
  isDefault: boolean
}

export interface EbayReturnPolicy {
  id: string
  name: string
  description?: string
  returnsAccepted: boolean
  returnPeriod: number // days
  refundMethod: 'money_back' | 'exchange' | 'store_credit'
  shippingCostPaidBy: 'buyer' | 'seller'
  isDefault: boolean
}

export interface EbayPaymentPolicy {
  id: string
  name: string
  description?: string
  paymentMethods: ('paypal' | 'credit_card' | 'bank_transfer')[]
  immediatePay: boolean
  isDefault: boolean
}

export interface EbayCategory {
  id: string
  name: string
  parentId?: string
  level: number
  leafCategory: boolean
  children?: EbayCategory[]
}

export interface EbaySyncSettings {
  autoSync: boolean
  syncInterval: number // in minutes
  syncStock: boolean
  syncPrices: boolean
  syncDescriptions: boolean
  lastSyncAt?: string
  nextSyncAt?: string
}

export interface EbayStats {
  activeListings: number
  totalViews: number
  totalWatchers: number
  totalSales: number
  totalRevenue: number
  averagePrice: number
  conversionRate: number
  impressions: number
}

// =============================================================================
// RETURNS TYPES
// =============================================================================

/**
 * eBay return status values
 */
export type EbayReturnStatus =
  | 'RETURN_REQUESTED'
  | 'RETURN_WAITING_FOR_RMA'
  | 'RETURN_ACCEPTED'
  | 'RETURN_DECLINED'
  | 'RETURN_ITEM_SHIPPED'
  | 'RETURN_ITEM_DELIVERED'
  | 'RETURN_CLOSED'
  | 'RETURN_CANCELLED'

/**
 * eBay return state (high-level)
 */
export type EbayReturnState = 'OPEN' | 'CLOSED'

/**
 * eBay return from API
 */
export interface EbayReturn {
  id: number
  return_id: string
  order_id: string | null
  state: EbayReturnState | null
  status: EbayReturnStatus | null
  return_type: string | null
  reason: string | null
  reason_detail: string | null
  refund_amount: number | null
  refund_currency: string | null
  refund_status: string | null
  buyer_username: string | null
  buyer_comments: string | null
  seller_comments: string | null
  rma_number: string | null
  return_tracking_number: string | null
  return_carrier: string | null
  creation_date: string | null
  deadline_date: string | null
  closed_date: string | null
  received_date: string | null
  created_at: string
  updated_at: string
  // Computed fields from API
  is_open: boolean
  needs_action: boolean
  is_past_deadline: boolean
}

/**
 * Paginated list of returns
 */
export interface EbayReturnListResponse {
  items: EbayReturn[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * Return statistics
 */
export interface EbayReturnStatistics {
  open: number
  closed: number
  needs_action: number
  past_deadline: number
}

/**
 * Sync returns response
 */
export interface EbayReturnSyncResponse {
  created: number
  updated: number
  skipped: number
  errors: number
  total_fetched: number
}

/**
 * Return action response (accept, decline, refund, etc.)
 */
export interface EbayReturnActionResponse {
  success: boolean
  return_id: string
  new_status: string | null
  refund_status: string | null
  message: string | null
}

// =============================================================================
// CANCELLATIONS TYPES
// =============================================================================

/**
 * eBay cancellation status values
 */
export type EbayCancellationStatus =
  | 'CANCEL_REQUESTED'
  | 'CANCEL_PENDING'
  | 'CANCEL_CLOSED_WITH_REFUND'
  | 'CANCEL_CLOSED_UNKNOWN_REFUND'
  | 'CANCEL_CLOSED_NO_REFUND'
  | 'CANCEL_REJECTED'

/**
 * eBay cancellation state (high-level)
 */
export type EbayCancellationState = 'CLOSED' | null

/**
 * eBay cancellation reason codes
 */
export type EbayCancellationReason =
  | 'OUT_OF_STOCK'
  | 'ADDRESS_ISSUES'
  | 'BUYER_ASKED_CANCEL'
  | 'ORDER_UNPAID'
  | 'OTHER_SELLER_CANCEL_REASON'

/**
 * eBay cancellation rejection reason codes
 */
export type EbayCancellationRejectReason =
  | 'ALREADY_SHIPPED'
  | 'OTHER_SELLER_REJECT_REASON'

/**
 * eBay cancellation requestor role
 */
export type EbayCancellationRequestorRole = 'BUYER' | 'SELLER'

/**
 * eBay cancellation from API
 */
export interface EbayCancellation {
  id: number
  cancel_id: string
  order_id: string | null
  cancel_state: EbayCancellationState
  cancel_status: EbayCancellationStatus | null
  cancel_reason: string | null
  requestor_role: EbayCancellationRequestorRole | null
  request_date: string | null
  response_due_date: string | null
  refund_amount: number | null
  refund_currency: string | null
  refund_status: string | null
  buyer_username: string | null
  buyer_comments: string | null
  seller_comments: string | null
  reject_reason: string | null
  tracking_number: string | null
  carrier: string | null
  shipped_date: string | null
  creation_date: string | null
  closed_date: string | null
  created_at: string
  updated_at: string
  // Computed fields from API
  is_closed: boolean
  is_pending: boolean
  needs_action: boolean
  is_past_response_due: boolean
  was_approved: boolean
  was_rejected: boolean
}

/**
 * Paginated list of cancellations
 */
export interface EbayCancellationListResponse {
  items: EbayCancellation[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * Cancellation statistics
 */
export interface EbayCancellationStatistics {
  pending: number
  closed: number
  needs_action: number
  past_due: number
}

/**
 * Sync cancellations response
 */
export interface EbayCancellationSyncResponse {
  created: number
  updated: number
  skipped: number
  errors: number
  total_fetched: number
}

/**
 * Cancellation action response (approve, reject, create)
 */
export interface EbayCancellationActionResponse {
  success: boolean
  cancel_id: string
  new_status: string | null
  message: string | null
}

/**
 * Eligibility check response
 */
export interface EbayCancellationEligibilityResponse {
  eligible: boolean
  eligibility_status: string | null
  order_id: string
  reasons: string[]
}

/**
 * State interface for the eBay store
 */
export interface EbayState {
  // Connection
  isConnected: boolean
  isConnecting: boolean
  connectionError: string | null

  // Account
  account: EbayAccount | null
  tokens: EbayTokens | null

  // Policies
  shippingPolicies: EbayShippingPolicy[]
  returnPolicies: EbayReturnPolicy[]
  paymentPolicies: EbayPaymentPolicy[]

  // Categories
  categories: EbayCategory[]
  selectedCategories: string[]

  // Sync settings
  syncSettings: EbaySyncSettings

  // Stats
  stats: EbayStats

  // Loading states
  isLoading: boolean
  isLoadingPolicies: boolean
  isLoadingCategories: boolean
  isSyncing: boolean
}

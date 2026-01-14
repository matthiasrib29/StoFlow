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

// =============================================================================
// REFUNDS TYPES
// =============================================================================

/**
 * eBay refund status values
 */
export type EbayRefundStatus = 'PENDING' | 'REFUNDED' | 'FAILED'

/**
 * eBay refund source values
 */
export type EbayRefundSource = 'RETURN' | 'CANCELLATION' | 'MANUAL' | 'OTHER'

/**
 * eBay refund reason codes
 */
export type EbayRefundReason =
  | 'BUYER_CANCEL'
  | 'BUYER_RETURN'
  | 'ITEM_NOT_RECEIVED'
  | 'SELLER_WRONG_ITEM'
  | 'SELLER_OUT_OF_STOCK'
  | 'SELLER_FOUND_ISSUE'
  | 'OTHER'

/**
 * eBay refund from API
 */
export interface EbayRefund {
  id: number
  refund_id: string
  order_id: string | null

  // Source
  refund_source: EbayRefundSource | null
  return_id: string | null
  cancel_id: string | null

  // Status
  refund_status: EbayRefundStatus | null

  // Amount
  refund_amount: number | null
  refund_currency: string | null
  original_amount: number | null

  // Reason
  reason: string | null
  comment: string | null

  // Buyer
  buyer_username: string | null

  // Reference IDs
  refund_reference_id: string | null
  transaction_id: string | null
  line_item_id: string | null

  // Dates
  refund_date: string | null
  creation_date: string | null
  created_at: string
  updated_at: string

  // Computed fields from API
  is_completed: boolean
  is_pending: boolean
  is_failed: boolean
  is_from_return: boolean
  is_from_cancellation: boolean
  is_manual: boolean
}

/**
 * Paginated list of refunds
 */
export interface EbayRefundListResponse {
  items: EbayRefund[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * Refund statistics by source
 */
export interface EbayRefundSourceStatistics {
  RETURN: number
  CANCELLATION: number
  MANUAL: number
}

/**
 * Refund statistics
 */
export interface EbayRefundStatistics {
  pending: number
  completed: number
  failed: number
  total_refunded: number
  by_source: EbayRefundSourceStatistics
}

/**
 * Sync refunds response
 */
export interface EbayRefundSyncResponse {
  created: number
  updated: number
  skipped: number
  errors: number
}

/**
 * Issue refund response
 */
export interface EbayRefundIssueResponse {
  success: boolean
  refund_id: string | null
  refund_status: string | null
  message: string | null
}

// =============================================================================
// PAYMENT DISPUTES TYPES
// =============================================================================

/**
 * eBay payment dispute state values
 */
export type EbayPaymentDisputeState = 'OPEN' | 'ACTION_NEEDED' | 'CLOSED'

/**
 * eBay payment dispute reason values
 */
export type EbayPaymentDisputeReason =
  | 'ITEM_NOT_RECEIVED'
  | 'ITEM_SIGNIFICANTLY_NOT_AS_DESCRIBED'
  | 'UNAUTHORIZED_TRANSACTION'
  | 'DUPLICATE_TRANSACTION'
  | 'CREDIT_NOT_PROCESSED'
  | 'MERCHANDISE_NOT_AS_DESCRIBED'
  | 'MERCHANDISE_NOT_RECEIVED'
  | 'OTHER'

/**
 * eBay seller response types for payment disputes
 */
export type EbayPaymentDisputeSellerResponse = 'CONTEST' | 'ACCEPT'

/**
 * eBay evidence types for payment dispute contest
 */
export type EbayPaymentDisputeEvidenceType =
  | 'PROOF_OF_DELIVERY'
  | 'PROOF_OF_AUTHENTICITY'
  | 'PROOF_OF_ITEM_AS_DESCRIBED'
  | 'PROOF_OF_PICKUP'
  | 'TRACKING_INFORMATION'

/**
 * eBay payment dispute from API
 */
export interface EbayPaymentDispute {
  id: number
  dispute_id: string
  order_id: string | null

  // State
  dispute_state: EbayPaymentDisputeState | null
  dispute_status: string | null
  dispute_reason: string | null
  reason_code: string | null

  // Amount
  dispute_amount: number | null
  dispute_currency: string | null
  original_order_amount: number | null

  // Buyer
  buyer_username: string | null
  buyer_claimed: string | null

  // Seller response
  seller_response: EbayPaymentDisputeSellerResponse | null
  seller_evidence: string | null
  seller_comment: string | null

  // Resolution
  resolution_status: string | null
  resolution_method: string | null
  resolution_amount: number | null

  // Dates
  creation_date: string | null
  response_due_date: string | null
  resolution_date: string | null
  closed_date: string | null
  created_at: string
  updated_at: string

  // Computed fields from API
  is_open: boolean
  needs_action: boolean
  is_past_due: boolean
  was_contested: boolean
  was_accepted: boolean
}

/**
 * Paginated list of payment disputes
 */
export interface EbayPaymentDisputeListResponse {
  items: EbayPaymentDispute[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * Payment dispute statistics
 */
export interface EbayPaymentDisputeStatistics {
  open: number
  action_needed: number
  closed: number
  total_disputed: number
}

/**
 * Sync payment disputes response
 */
export interface EbayPaymentDisputeSyncResponse {
  created: number
  updated: number
  skipped: number
  errors: number
  total_fetched: number
}

/**
 * Payment dispute action response (accept, contest)
 */
export interface EbayPaymentDisputeActionResponse {
  success: boolean
  dispute_id: string
  new_state: string | null
  message: string | null
}

/**
 * Add evidence response
 */
export interface EbayPaymentDisputeEvidenceResponse {
  success: boolean
  dispute_id: string
  evidence_id: string | null
  message: string | null
}

// =============================================================================
// INR INQUIRIES TYPES
// =============================================================================

/**
 * eBay inquiry state values
 */
export type EbayInquiryState = 'OPEN' | 'CLOSED'

/**
 * eBay inquiry status values
 */
export type EbayInquiryStatus =
  | 'INR_WAITING_FOR_SELLER'
  | 'INR_WAITING_FOR_BUYER'
  | 'INR_CLOSED_SELLER_PROVIDED_INFO'
  | 'INR_CLOSED_REFUND'
  | 'INR_CLOSED_BUYER_CONFIRMED'
  | 'INR_CLOSED_ITEM_DELIVERED'
  | 'INR_ESCALATED'

/**
 * eBay inquiry type values
 */
export type EbayInquiryType = 'INR'

/**
 * eBay seller response types for inquiries
 */
export type EbayInquirySellerResponse =
  | 'SHIPMENT_INFO'
  | 'REFUND'
  | 'MESSAGE'
  | 'ESCALATION'

/**
 * eBay INR inquiry from API
 */
export interface EbayInquiry {
  id: number
  inquiry_id: string
  order_id: string | null

  // State
  inquiry_state: EbayInquiryState | null
  inquiry_status: EbayInquiryStatus | null
  inquiry_type: EbayInquiryType | null

  // Amount
  claim_amount: number | null
  claim_currency: string | null

  // Buyer info
  buyer_username: string | null
  buyer_comments: string | null

  // Seller response
  seller_response: string | null

  // Item info
  item_id: string | null
  item_title: string | null

  // Shipment info
  shipment_tracking_number: string | null
  shipment_carrier: string | null

  // Dates
  creation_date: string | null
  respond_by_date: string | null
  closed_date: string | null
  escalation_date: string | null
  created_at: string
  updated_at: string

  // Computed fields from API
  is_open: boolean
  needs_action: boolean
  is_past_due: boolean
  is_escalated: boolean
}

/**
 * Paginated list of inquiries
 */
export interface EbayInquiryListResponse {
  items: EbayInquiry[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * Inquiry statistics
 */
export interface EbayInquiryStatistics {
  open: number
  closed: number
  needs_action: number
  past_deadline: number
}

/**
 * Sync inquiries response
 */
export interface EbayInquirySyncResponse {
  success: boolean
  created: number
  updated: number
  total_fetched: number
  errors: string[]
}

/**
 * Inquiry action response (shipment info, refund, message, escalate)
 */
export interface EbayInquiryActionResponse {
  success: boolean
  inquiry_id: string
  new_status: string | null
  message: string | null
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

// =============================================================================
// DASHBOARD TYPES
// =============================================================================

/**
 * Return statistics for dashboard
 */
export interface DashboardReturnStatistics {
  open: number
  closed: number
  needs_action: number
  past_deadline: number
}

/**
 * Cancellation statistics for dashboard
 */
export interface DashboardCancellationStatistics {
  pending: number
  closed: number
  needs_action: number
  past_due: number
}

/**
 * Refund statistics for dashboard
 */
export interface DashboardRefundStatistics {
  pending: number
  completed: number
  failed: number
  total_refunded: number
}

/**
 * Payment dispute statistics for dashboard
 */
export interface DashboardPaymentDisputeStatistics {
  open: number
  action_needed: number
  closed: number
  total_disputed: number
}

/**
 * Inquiry statistics for dashboard
 */
export interface DashboardInquiryStatistics {
  open: number
  closed: number
  needs_action: number
  past_deadline: number
}

/**
 * Totals statistics for dashboard
 */
export interface DashboardTotalsStatistics {
  open: number
  needs_action: number
  past_deadline: number
}

/**
 * Unified dashboard statistics response
 */
export interface EbayDashboardStatistics {
  returns: DashboardReturnStatistics
  cancellations: DashboardCancellationStatistics
  refunds: DashboardRefundStatistics
  payment_disputes: DashboardPaymentDisputeStatistics
  inquiries: DashboardInquiryStatistics
  totals: DashboardTotalsStatistics
  generated_at: string
}

/**
 * Urgent item requiring action
 */
export interface EbayUrgentItem {
  id: number
  type: 'return' | 'cancellation' | 'payment_dispute' | 'inquiry'
  urgency: 'critical' | 'high'
  order_id: string | null
  status: string | null
  reason: string | null
  buyer_username: string | null
  deadline_date: string | null
  is_past_due: boolean | null

  // Type-specific fields
  return_id?: string | null
  cancel_id?: string | null
  dispute_id?: string | null
  inquiry_id?: string | null
  refund_amount?: number | null
  refund_currency?: string | null
  dispute_amount?: number | null
  dispute_currency?: string | null
  claim_amount?: number | null
  claim_currency?: string | null
  item_title?: string | null
  is_escalated?: boolean | null
  requestor_role?: string | null
}

/**
 * Urgent items response
 */
export interface EbayUrgentItemsResponse {
  returns: EbayUrgentItem[]
  cancellations: EbayUrgentItem[]
  payment_disputes: EbayUrgentItem[]
  inquiries: EbayUrgentItem[]
  total_count: number
  generated_at: string
}

/**
 * Recent activity item
 */
export interface EbayActivityItem {
  type: 'return' | 'cancellation' | 'refund' | 'payment_dispute' | 'inquiry'
  id: number
  external_id: string | null
  order_id: string | null
  status: string | null
  amount: number | null
  currency: string | null
  buyer_username: string | null
  date: string | null
  updated_at: string | null
}

/**
 * Recent activity response
 */
export interface EbayRecentActivityResponse {
  items: EbayActivityItem[]
  total_count: number
}

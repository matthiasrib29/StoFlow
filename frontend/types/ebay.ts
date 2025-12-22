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

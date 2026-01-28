/**
 * eBay Integration Store
 * Simplified store using composables for business logic
 *
 * Related composables:
 * - useEbayOAuth: OAuth authentication flow
 * - useEbayPolicies: Shipping, return, payment policies
 * - useEbayAccount: Account info, stats, sync settings
 */

import { defineStore } from 'pinia'
import { ebayLogger } from '~/utils/logger'
import type {
  EbayAccount,
  EbayTokens,
  EbayShippingPolicy,
  EbayReturnPolicy,
  EbayPaymentPolicy,
  EbayCategory,
  EbaySyncSettings,
  EbayStats
} from '~/types/ebay'

// Re-export types for backward compatibility
export type {
  EbayAccount,
  EbayTokens,
  EbayShippingPolicy,
  EbayReturnPolicy,
  EbayPaymentPolicy,
  EbayCategory,
  EbaySyncSettings,
  EbayStats
}

export const useEbayStore = defineStore('ebay', {
  state: () => ({
    // Connection
    isConnected: false,
    isConnecting: false,
    connectionError: null as string | null,

    // Account
    account: null as EbayAccount | null,
    tokens: null as EbayTokens | null,

    // Policies
    shippingPolicies: [] as EbayShippingPolicy[],
    returnPolicies: [] as EbayReturnPolicy[],
    paymentPolicies: [] as EbayPaymentPolicy[],

    // Categories
    categories: [] as EbayCategory[],
    selectedCategories: [] as string[],

    // Sync settings
    syncSettings: {
      autoSync: true,
      syncInterval: 30,
      syncStock: true,
      syncPrices: true,
      syncDescriptions: false,
      lastSyncAt: undefined,
      nextSyncAt: undefined
    } as EbaySyncSettings,

    // Stats
    stats: {
      activeListings: 0,
      totalViews: 0,
      totalWatchers: 0,
      totalSales: 0,
      totalRevenue: 0,
      averagePrice: 0,
      conversionRate: 0,
      impressions: 0
    } as EbayStats,

    // Loading states
    isLoading: false,
    isLoadingPolicies: false,
    isLoadingCategories: false,
    isSyncing: false
  }),

  getters: {
    hasValidTokens(): boolean {
      if (!this.tokens) return false
      return new Date(this.tokens.expiresAt) > new Date()
    },

    defaultShippingPolicy(): EbayShippingPolicy | undefined {
      return this.shippingPolicies.find(p => p.isDefault)
    },

    defaultReturnPolicy(): EbayReturnPolicy | undefined {
      return this.returnPolicies.find(p => p.isDefault)
    },

    defaultPaymentPolicy(): EbayPaymentPolicy | undefined {
      return this.paymentPolicies.find(p => p.isDefault)
    },

    sellerLevelLabel(): string {
      if (!this.account?.sellerLevel) return 'Non connecté'
      const labels: Record<string, string> = {
        top_rated: 'Vendeur Top Fiabilité',
        above_standard: 'Au-dessus des standards',
        standard: 'Standard',
        below_standard: 'En dessous des standards'
      }
      return labels[this.account.sellerLevel] || this.account.sellerLevel
    }
  },

  actions: {
    // ==================== OAuth Actions ====================

    getOAuthUrl(): string {
      const { getOAuthUrl } = useEbayOAuth()
      return getOAuthUrl()
    },

    async initiateOAuth() {
      this.isConnecting = true
      this.connectionError = null

      try {
        const { initiateOAuth } = useEbayOAuth()
        await initiateOAuth(() => {
          // Check connection after popup closes
          this.checkConnectionStatus()
        })
      } catch (error: any) {
        this.connectionError = error.message
        throw error
      } finally {
        this.isConnecting = false
      }
    },

    async exchangeCodeForTokens(code: string) {
      this.isConnecting = true

      try {
        const { exchangeCodeForTokens } = useEbayOAuth()
        const response = await exchangeCodeForTokens(code)

        this.tokens = response.tokens
        this.account = response.account
        this.isConnected = true

        // Load data
        await Promise.all([
          this.fetchPolicies(),
          this.fetchStats()
        ])

        return response
      } catch (error: any) {
        this.connectionError = error.message
        throw error
      } finally {
        this.isConnecting = false
      }
    },

    async checkConnectionStatus() {
      try {
        const { checkConnectionStatus, parseAccountFromStatus } = useEbayOAuth()
        const status = await checkConnectionStatus()

        this.isConnected = status.is_connected
        if (status.is_connected) {
          this.account = parseAccountFromStatus(status)
        }

        return status
      } catch (error) {
        ebayLogger.error('Erreur vérification statut eBay', { error })
        this.isConnected = false
        throw error
      }
    },

    async connectMock() {
      this.isConnecting = true
      this.connectionError = null

      try {
        const { connectMock } = useEbayOAuth()
        const { account, tokens } = await connectMock()

        this.account = account
        this.tokens = tokens
        this.isConnected = true

        // Load mock data
        await Promise.all([
          this.fetchPoliciesMock(),
          this.fetchStatsMock()
        ])
      } catch (error: any) {
        this.connectionError = error.message
        throw error
      } finally {
        this.isConnecting = false
      }
    },

    async disconnect() {
      this.isLoading = true

      try {
        const { disconnect } = useEbayOAuth()
        await disconnect()
        this.$reset()
      } finally {
        this.isLoading = false
      }
    },

    // ==================== Policies Actions ====================

    async fetchPolicies(marketplaceId: string = 'EBAY_FR') {
      this.isLoadingPolicies = true

      try {
        const { fetchPolicies } = useEbayPolicies()
        const { shipping, returns, payment } = await fetchPolicies(marketplaceId)

        this.shippingPolicies = shipping
        this.returnPolicies = returns
        this.paymentPolicies = payment
      } catch (error) {
        ebayLogger.error('Erreur chargement politiques', { error })
      } finally {
        this.isLoadingPolicies = false
      }
    },

    async fetchPoliciesMock() {
      this.isLoadingPolicies = true

      try {
        const { fetchPoliciesMock } = useEbayPolicies()
        const { shipping, returns, payment } = await fetchPoliciesMock()

        this.shippingPolicies = shipping
        this.returnPolicies = returns
        this.paymentPolicies = payment
      } finally {
        this.isLoadingPolicies = false
      }
    },

    async createPaymentPolicy(data: { name: string; marketplace_id: string; immediate_pay?: boolean }) {
      this.isLoading = true

      try {
        const { createPaymentPolicy } = useEbayPolicies()
        await createPaymentPolicy(data)
        await this.fetchPolicies(data.marketplace_id)
      } finally {
        this.isLoading = false
      }
    },

    async createFulfillmentPolicy(data: {
      name: string
      marketplace_id: string
      handling_time_value?: number
      shipping_services: Array<{
        shipping_carrier_code: string
        shipping_service_code: string
        shipping_cost: number
        currency?: string
        free_shipping?: boolean
      }>
    }) {
      this.isLoading = true

      try {
        const { createFulfillmentPolicy } = useEbayPolicies()
        await createFulfillmentPolicy(data)
        await this.fetchPolicies(data.marketplace_id)
      } finally {
        this.isLoading = false
      }
    },

    async createReturnPolicy(data: {
      name: string
      marketplace_id: string
      returns_accepted?: boolean
      return_period_value?: number
      refund_method?: string
      return_shipping_cost_payer?: string
    }) {
      this.isLoading = true

      try {
        const { createReturnPolicy } = useEbayPolicies()
        await createReturnPolicy(data)
        await this.fetchPolicies(data.marketplace_id)
      } finally {
        this.isLoading = false
      }
    },

    async deletePolicy(type: 'shipping' | 'return' | 'payment', policyId: string, marketplaceId: string = 'EBAY_FR') {
      this.isLoading = true

      try {
        const { deletePolicy } = useEbayPolicies()
        await deletePolicy(type, policyId, marketplaceId)
        await this.fetchPolicies(marketplaceId)
      } finally {
        this.isLoading = false
      }
    },

    async updatePolicy(type: 'shipping' | 'return' | 'payment', policyId: string, data: any, marketplaceId: string = 'EBAY_FR') {
      this.isLoading = true

      try {
        const { updatePaymentPolicy, updateFulfillmentPolicy, updateReturnPolicy } = useEbayPolicies()

        switch (type) {
          case 'payment':
            await updatePaymentPolicy(policyId, data)
            break
          case 'shipping':
            await updateFulfillmentPolicy(policyId, data)
            break
          case 'return':
            await updateReturnPolicy(policyId, data)
            break
        }

        await this.fetchPolicies(marketplaceId)
      } finally {
        this.isLoading = false
      }
    },

    async applyPolicyToOffers(policyType: 'payment' | 'fulfillment' | 'return', policyId: string, marketplaceId: string = 'EBAY_FR') {
      this.isLoading = true

      try {
        const { applyPolicyToOffers } = useEbayPolicies()
        return await applyPolicyToOffers({
          policy_type: policyType,
          policy_id: policyId,
          marketplace_id: marketplaceId
        })
      } finally {
        this.isLoading = false
      }
    },

    async fetchCategoriesMock() {
      this.isLoadingCategories = true

      try {
        const { fetchCategoriesMock } = useEbayPolicies()
        this.categories = await fetchCategoriesMock()
      } finally {
        this.isLoadingCategories = false
      }
    },

    // ==================== Account & Stats Actions ====================

    async fetchAccountInfo() {
      try {
        const { fetchAccountInfo } = useEbayAccount()
        this.account = await fetchAccountInfo(this.account)
        return this.account
      } catch (error) {
        ebayLogger.error('Erreur chargement infos compte eBay', { error })
        throw error
      }
    },

    async fetchStats() {
      try {
        const { fetchStats } = useEbayAccount()
        this.stats = await fetchStats()
      } catch (error) {
        ebayLogger.error('Erreur chargement stats', { error })
      }
    },

    async fetchStatsMock() {
      const { fetchStatsMock } = useEbayAccount()
      this.stats = await fetchStatsMock()
    },

    async syncData() {
      this.isSyncing = true

      try {
        const { syncData } = useEbayAccount()
        this.syncSettings = await syncData(this.syncSettings, (stats) => {
          this.stats = stats
        })
      } finally {
        this.isSyncing = false
      }
    },

    async saveSyncSettings(settings: Partial<EbaySyncSettings>) {
      const { saveSyncSettings } = useEbayAccount()
      await saveSyncSettings(settings)
      this.syncSettings = { ...this.syncSettings, ...settings }
    }
  }

  // Note: Persist to localStorage requires pinia-plugin-persistedstate
  // For now, persistence is handled manually in useEbayOAuth composable
})

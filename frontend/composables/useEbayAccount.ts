/**
 * Composable for eBay account information and stats
 * Handles fetching account details, stats, and sync settings
 */

import type { EbayAccount, EbayStats, EbaySyncSettings } from '~/types/ebay'

interface AccountInfoResponse {
  success: boolean
  seller_info?: Record<string, any>
  programs?: Array<{ programType: string }>
  fulfillment_policies_count?: number
  access_token_expires_at?: string
  sandbox_mode?: boolean
}

export const useEbayAccount = () => {
  const api = useApi()

  /**
   * Fetch account info from API
   */
  const fetchAccountInfo = async (currentAccount: EbayAccount | null): Promise<EbayAccount> => {
    const response = await api.get<AccountInfoResponse>('/api/ebay/account-info')

    // Start with current account or create new one
    const account: EbayAccount = currentAccount || {
      userId: '',
      username: '',
      email: '',
      accountType: 'individual',
      registrationDate: '',
      sellerLevel: 'standard',
      feedbackScore: 0,
      feedbackPercentage: 0
    }

    if (response.success && response.seller_info) {
      const info = response.seller_info

      // Basic data from Commerce Identity
      account.userId = info.userId || account.userId
      account.username = info.username || account.username
      account.accountType = info.accountType || account.accountType
      account.marketplace = info.registrationMarketplaceId

      // Business Account
      if (info.businessAccount) {
        const business = info.businessAccount
        account.businessName = business.name
        account.email = business.email

        // Phone
        if (business.primaryPhone) {
          account.phone = `+${business.primaryPhone.countryCode} ${business.primaryPhone.number}`
        }

        // Address
        if (business.address) {
          const addr = business.address
          account.address = [
            addr.addressLine1,
            addr.addressLine2,
            `${addr.postalCode} ${addr.city}`,
            addr.country
          ].filter(Boolean).join(', ')
        }

        // Primary contact
        if (business.primaryContact) {
          account.firstName = business.primaryContact.firstName
          account.lastName = business.primaryContact.lastName
        }
      }
      // Individual Account
      else if (info.individualAccount) {
        const individual = info.individualAccount
        account.firstName = individual.firstName
        account.lastName = individual.lastName
        account.email = individual.email

        // Phone
        if (individual.primaryPhone) {
          account.phone = `+${individual.primaryPhone.countryCode} ${individual.primaryPhone.number}`
        }

        // Address
        if (individual.registrationAddress) {
          const addr = individual.registrationAddress
          account.address = [
            addr.addressLine1,
            addr.addressLine2,
            `${addr.postalCode} ${addr.city}`,
            addr.country
          ].filter(Boolean).join(', ')
        }
      }

      // Data from Trading API
      if (info.feedback_score !== undefined) {
        account.feedbackScore = info.feedback_score
        account.feedbackPercentage = info.positive_feedback_percent || 0
      }
      if (info.registration_date) {
        account.registrationDate = info.registration_date
      }
      if (info.seller_level) {
        account.sellerLevel = info.top_rated_seller ? 'top_rated' : info.seller_level
      }
    }

    // Always add programs and policies count
    account.programs = response.programs
    account.fulfillmentPoliciesCount = response.fulfillment_policies_count
    account.accessTokenExpiresAt = response.access_token_expires_at
    account.sandboxMode = response.sandbox_mode

    return account
  }

  /**
   * Fetch stats from API
   */
  const fetchStats = async (): Promise<EbayStats> => {
    return await api.get<EbayStats>('/api/ebay/stats')
  }

  /**
   * Mock: Fetch stats for testing
   */
  const fetchStatsMock = async (): Promise<EbayStats> => {
    await new Promise(resolve => setTimeout(resolve, 500))

    return {
      activeListings: 47,
      totalViews: 12847,
      totalWatchers: 234,
      totalSales: 156,
      totalRevenue: 8947.50,
      averagePrice: 57.35,
      conversionRate: 3.2,
      impressions: 45680
    }
  }

  /**
   * Sync data with eBay
   */
  const syncData = async (
    syncSettings: EbaySyncSettings,
    onStatsUpdate: (stats: EbayStats) => void
  ): Promise<EbaySyncSettings> => {
    // TODO: Replace with actual API call
    await new Promise(resolve => setTimeout(resolve, 2000))

    const updatedSettings: EbaySyncSettings = {
      ...syncSettings,
      lastSyncAt: new Date().toISOString(),
      nextSyncAt: new Date(Date.now() + syncSettings.syncInterval * 60 * 1000).toISOString()
    }

    // Reload stats
    const stats = await fetchStatsMock()
    onStatsUpdate(stats)

    return updatedSettings
  }

  /**
   * Save sync settings
   */
  const saveSyncSettings = async (settings: Partial<EbaySyncSettings>): Promise<void> => {
    // TODO: Replace with actual API call
    await new Promise(resolve => setTimeout(resolve, 300))
  }

  /**
   * Get seller level label in French
   */
  const getSellerLevelLabel = (sellerLevel: string): string => {
    const labels: Record<string, string> = {
      top_rated: 'Vendeur Top Fiabilité',
      above_standard: 'Au-dessus des standards',
      standard: 'Standard',
      below_standard: 'En dessous des standards'
    }
    return labels[sellerLevel] || sellerLevel
  }

  return {
    fetchAccountInfo,
    fetchStats,
    fetchStatsMock,
    syncData,
    saveSyncSettings,
    getSellerLevelLabel
  }
}

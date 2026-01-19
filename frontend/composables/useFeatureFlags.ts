/**
 * Feature flags for PMV phases
 *
 * Features marked as PMV2 are hidden during phase 1.
 * Set to true when ready to enable the feature.
 */

// PMV2 features - set to true to enable
const PMV2_FEATURES = {
  // Platform statistics pages (Vinted, eBay, Etsy)
  platformStatistics: false,

  // eBay post-sale management (returns, cancellations, refunds, disputes, INR)
  ebayPostSale: false,

  // Etsy platform (entire integration)
  etsyPlatform: false,

  // Add more PMV2 features here as needed
  // example: advancedReporting: false,
} as const

type FeatureKey = keyof typeof PMV2_FEATURES

export function useFeatureFlags() {
  /**
   * Check if a feature is enabled
   */
  const isEnabled = (feature: FeatureKey): boolean => {
    return PMV2_FEATURES[feature] ?? false
  }

  /**
   * Check if a feature is PMV2 (hidden for now)
   */
  const isPMV2 = (feature: FeatureKey): boolean => {
    return !PMV2_FEATURES[feature]
  }

  return {
    isEnabled,
    isPMV2,
    // Direct access to check specific features
    showPlatformStatistics: PMV2_FEATURES.platformStatistics,
    showEbayPostSale: PMV2_FEATURES.ebayPostSale,
    showEtsyPlatform: PMV2_FEATURES.etsyPlatform,
  }
}

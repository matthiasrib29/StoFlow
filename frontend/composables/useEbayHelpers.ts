/**
 * Composable for eBay-specific helper functions.
 * Extracted from ebay.vue to reduce file size.
 */

import { formatCurrency } from '~/utils/formatters'

/**
 * Shipping type labels mapping.
 */
const SHIPPING_TYPE_LABELS: Record<string, string> = {
  flat_rate: 'Forfait',
  calculated: 'Calculé',
  free_shipping: 'Gratuit',
  FLAT_RATE: 'Forfait',
  CALCULATED: 'Calculé',
  FREE: 'Gratuit'
}

/**
 * Payment method labels mapping.
 */
const PAYMENT_METHOD_LABELS: Record<string, string> = {
  paypal: 'PayPal',
  credit_card: 'Carte',
  bank_transfer: 'Virement'
}

/**
 * eBay program names mapping.
 */
const PROGRAM_NAMES: Record<string, string> = {
  'SELLING_POLICY_MANAGEMENT': 'Gestion Politiques',
  'PROMOTED_LISTINGS_STANDARD': 'Annonces sponsorisées',
  'OFFSITE_ADS': 'Publicités hors site',
  'OUT_OF_STOCK_CONTROL': 'Contrôle stock'
}

/**
 * eBay condition labels mapping.
 */
const CONDITION_LABELS: Record<string, string> = {
  NEW: 'Neuf',
  LIKE_NEW: 'Comme neuf',
  NEW_OTHER: 'Neuf autre',
  NEW_WITH_DEFECTS: 'Neuf avec défauts',
  MANUFACTURER_REFURBISHED: 'Reconditionné fabricant',
  CERTIFIED_REFURBISHED: 'Certifié reconditionné',
  EXCELLENT_REFURBISHED: 'Excellent reconditionné',
  VERY_GOOD_REFURBISHED: 'Très bon reconditionné',
  GOOD_REFURBISHED: 'Bon reconditionné',
  SELLER_REFURBISHED: 'Reconditionné vendeur',
  USED_EXCELLENT: 'Occasion excellent',
  USED_VERY_GOOD: 'Occasion très bon',
  USED_GOOD: 'Occasion bon',
  USED_ACCEPTABLE: 'Occasion acceptable',
  FOR_PARTS_OR_NOT_WORKING: 'Pour pièces'
}

/**
 * Listing status labels mapping.
 */
const LISTING_STATUS_LABELS: Record<string, string> = {
  active: 'Actif',
  inactive: 'Inactif',
  ended: 'Terminé',
  sold: 'Vendu',
  ACTIVE: 'Actif',
  DRAFT: 'Brouillon',
  ENDED: 'Terminé',
  OUT_OF_STOCK: 'Hors stock'
}

/**
 * Listing status severities mapping.
 */
const LISTING_STATUS_SEVERITIES: Record<string, string> = {
  active: 'success',
  inactive: 'warning',
  ended: 'secondary',
  sold: 'info',
  ACTIVE: 'success',
  DRAFT: 'warning',
  ENDED: 'secondary',
  OUT_OF_STOCK: 'danger'
}

export function useEbayHelpers() {
  /**
   * Get shipping type label.
   */
  const getShippingTypeLabel = (type: string): string => {
    return SHIPPING_TYPE_LABELS[type] || type || 'Standard'
  }

  /**
   * Get shipping cost from policy object.
   */
  const getShippingCost = (policy: any): string => {
    // Check shippingOptions array (eBay API format)
    if (policy.shippingOptions && policy.shippingOptions.length > 0) {
      const option = policy.shippingOptions[0]
      if (option.costType === 'FREE' || option.shippingCost?.value === '0') {
        return 'Gratuit'
      }
      if (option.shippingCost?.value) {
        return formatCurrency(parseFloat(option.shippingCost.value))
      }
    }
    // Fallback to domesticShipping (old format)
    if (policy.domesticShipping?.cost) {
      return formatCurrency(policy.domesticShipping.cost)
    }
    return '-'
  }

  /**
   * Get shipping type from policy object.
   */
  const getShippingTypeFromPolicy = (policy: any): string => {
    if (policy.shippingOptions && policy.shippingOptions.length > 0) {
      const option = policy.shippingOptions[0]
      if (option.costType === 'FREE') return 'Gratuit'
      if (option.costType === 'FLAT_RATE') return 'Forfait'
      if (option.costType === 'CALCULATED') return 'Calculé'
      return option.costType || 'Standard'
    }
    return policy.type ? getShippingTypeLabel(policy.type) : 'Standard'
  }

  /**
   * Check if policy has free shipping.
   */
  const isFreeShipping = (policy: any): boolean => {
    if (policy.shippingOptions && policy.shippingOptions.length > 0) {
      return policy.shippingOptions[0].costType === 'FREE'
    }
    return policy.type === 'free_shipping'
  }

  /**
   * Get payment method label.
   */
  const getPaymentMethodLabel = (method: string): string => {
    return PAYMENT_METHOD_LABELS[method] || method
  }

  /**
   * Get seller level severity for UI display.
   */
  const getSellerLevelSeverity = (level: string | undefined): string => {
    if (level === 'top_rated') return 'success'
    if (level === 'above_standard') return 'info'
    if (level === 'standard') return 'warning'
    return 'danger'
  }

  /**
   * Get seller level label.
   */
  const getSellerLevelLabel = (level: string | undefined): string => {
    const labels: Record<string, string> = {
      'top_rated': 'Top Vendeur',
      'above_standard': 'Au-dessus de la norme',
      'standard': 'Standard',
      'below_standard': 'En dessous de la norme'
    }
    return labels[level || ''] || level || 'Inconnu'
  }

  /**
   * Format eBay program name.
   */
  const formatProgramName = (programType: string): string => {
    return PROGRAM_NAMES[programType] || programType.replace(/_/g, ' ')
  }

  /**
   * Get condition label from condition code.
   */
  const getConditionLabel = (condition: string): string => {
    return CONDITION_LABELS[condition] || condition || 'Non spécifié'
  }

  /**
   * Get listing status label.
   */
  const getListingStatusLabel = (status: string): string => {
    return LISTING_STATUS_LABELS[status] || status || 'Inconnu'
  }

  /**
   * Get listing status severity for Tag component.
   */
  const getListingStatusSeverity = (status: string): string => {
    return LISTING_STATUS_SEVERITIES[status] || 'info'
  }

  /**
   * Open an eBay listing in a new tab.
   */
  const openEbayListing = (url: string): void => {
    window.open(url, '_blank')
  }

  return {
    getShippingTypeLabel,
    getShippingCost,
    getShippingTypeFromPolicy,
    isFreeShipping,
    getPaymentMethodLabel,
    getSellerLevelSeverity,
    getSellerLevelLabel,
    formatProgramName,
    getConditionLabel,
    getListingStatusLabel,
    getListingStatusSeverity,
    openEbayListing
  }
}

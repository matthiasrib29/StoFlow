/**
 * Composable for eBay policies management
 * Handles shipping, return, and payment policies
 */

import type {
  EbayShippingPolicy,
  EbayReturnPolicy,
  EbayPaymentPolicy,
  EbayCategory
} from '~/types/ebay'

interface PoliciesState {
  shippingPolicies: Ref<EbayShippingPolicy[]>
  returnPolicies: Ref<EbayReturnPolicy[]>
  paymentPolicies: Ref<EbayPaymentPolicy[]>
  categories: Ref<EbayCategory[]>
  isLoading: Ref<boolean>
  isLoadingCategories: Ref<boolean>
}

export const useEbayPolicies = () => {
  const api = useApi()

  /**
   * Fetch all policies from API for a given marketplace
   */
  const fetchPolicies = async (marketplaceId: string = 'EBAY_FR'): Promise<{
    shipping: EbayShippingPolicy[]
    returns: EbayReturnPolicy[]
    payment: EbayPaymentPolicy[]
  }> => {
    const response = await api.get<{
      fulfillment_policies: EbayShippingPolicy[]
      return_policies: EbayReturnPolicy[]
      payment_policies: EbayPaymentPolicy[]
    }>(`/ebay/policies?marketplace_id=${marketplaceId}`)

    return {
      shipping: response.fulfillment_policies || [],
      returns: response.return_policies || [],
      payment: response.payment_policies || []
    }
  }

  /**
   * Create a payment policy via API
   */
  const createPaymentPolicy = async (data: {
    name: string
    marketplace_id: string
    immediate_pay?: boolean
  }): Promise<any> => {
    return api.post('/ebay/policies/payment', data)
  }

  /**
   * Create a fulfillment (shipping) policy via API
   */
  const createFulfillmentPolicy = async (data: {
    name: string
    marketplace_id: string
    handling_time_value?: number
    shipping_services: Array<{
      shipping_carrier_code: string
      shipping_service_code: string
      shipping_cost: number
      currency?: string
      free_shipping?: boolean
      additional_cost?: number
    }>
  }): Promise<any> => {
    return api.post('/ebay/policies/fulfillment', data)
  }

  /**
   * Create a return policy via API
   */
  const createReturnPolicy = async (data: {
    name: string
    marketplace_id: string
    returns_accepted?: boolean
    return_period_value?: number
    refund_method?: string
    return_shipping_cost_payer?: string
  }): Promise<any> => {
    return api.post('/ebay/policies/return', data)
  }

  /**
   * Update a payment policy via API
   */
  const updatePaymentPolicy = async (policyId: string, data: {
    name: string
    marketplace_id: string
    immediate_pay?: boolean
  }): Promise<any> => {
    return api.put(`/ebay/policies/payment/${policyId}`, data)
  }

  /**
   * Update a fulfillment (shipping) policy via API
   */
  const updateFulfillmentPolicy = async (policyId: string, data: {
    name: string
    marketplace_id: string
    handling_time_value?: number
    shipping_services: Array<{
      shipping_carrier_code: string
      shipping_service_code: string
      shipping_cost: number
      currency?: string
      free_shipping?: boolean
      additional_cost?: number
    }>
  }): Promise<any> => {
    return api.put(`/ebay/policies/fulfillment/${policyId}`, data)
  }

  /**
   * Update a return policy via API
   */
  const updateReturnPolicy = async (policyId: string, data: {
    name: string
    marketplace_id: string
    returns_accepted?: boolean
    return_period_value?: number
    refund_method?: string
    return_shipping_cost_payer?: string
  }): Promise<any> => {
    return api.put(`/ebay/policies/return/${policyId}`, data)
  }

  /**
   * Delete a policy via API
   */
  const deletePolicy = async (
    type: 'shipping' | 'return' | 'payment',
    policyId: string,
    marketplaceId: string = 'EBAY_FR'
  ): Promise<void> => {
    const typeMap: Record<string, string> = {
      shipping: 'fulfillment',
      return: 'return',
      payment: 'payment'
    }
    await api.del(`/ebay/policies/${typeMap[type]}/${policyId}?marketplace_id=${marketplaceId}`)
  }

  /**
   * Apply a policy to all existing eBay offers for a marketplace
   */
  const applyPolicyToOffers = async (data: {
    policy_type: 'payment' | 'fulfillment' | 'return'
    policy_id: string
    marketplace_id: string
  }): Promise<{ updated: number; skipped: number; errors: any[]; settings_updated: boolean }> => {
    return api.post('/ebay/policies/apply-to-offers', data)
  }

  /**
   * Mock: Fetch policies for testing
   */
  const fetchPoliciesMock = async (): Promise<{
    shipping: EbayShippingPolicy[]
    returns: EbayReturnPolicy[]
    payment: EbayPaymentPolicy[]
  }> => {
    await new Promise(resolve => setTimeout(resolve, 800))

    const shipping: EbayShippingPolicy[] = [
      {
        id: 'ship_1',
        name: 'Livraison Standard France',
        description: 'Colissimo sous 3-5 jours',
        type: 'flat_rate',
        domesticShipping: {
          service: 'FR_ColipostColissimo',
          cost: 5.99,
          additionalCost: 1.50,
          handlingTime: 1
        },
        internationalShipping: {
          enabled: true,
          service: 'FR_ColipostInternational',
          cost: 12.99,
          countries: ['BE', 'DE', 'ES', 'IT', 'NL']
        },
        isDefault: true
      },
      {
        id: 'ship_2',
        name: 'Livraison Express',
        description: 'Chronopost 24h',
        type: 'flat_rate',
        domesticShipping: {
          service: 'FR_Chronopost',
          cost: 9.99,
          handlingTime: 0
        },
        isDefault: false
      },
      {
        id: 'ship_3',
        name: 'Livraison Gratuite',
        description: 'Pour commandes > 50€',
        type: 'free_shipping',
        domesticShipping: {
          service: 'FR_ColipostColissimo',
          cost: 0,
          handlingTime: 2
        },
        isDefault: false
      }
    ]

    const returns: EbayReturnPolicy[] = [
      {
        id: 'ret_1',
        name: 'Retours 30 jours',
        description: 'Remboursement complet sous 30 jours',
        returnsAccepted: true,
        returnPeriod: 30,
        refundMethod: 'money_back',
        shippingCostPaidBy: 'buyer',
        isDefault: true
      },
      {
        id: 'ret_2',
        name: 'Retours 14 jours',
        description: 'Conforme à la loi EU',
        returnsAccepted: true,
        returnPeriod: 14,
        refundMethod: 'money_back',
        shippingCostPaidBy: 'seller',
        isDefault: false
      },
      {
        id: 'ret_3',
        name: 'Pas de retours',
        description: 'Ventes finales uniquement',
        returnsAccepted: false,
        returnPeriod: 0,
        refundMethod: 'money_back',
        shippingCostPaidBy: 'buyer',
        isDefault: false
      }
    ]

    const payment: EbayPaymentPolicy[] = [
      {
        id: 'pay_1',
        name: 'Paiement Immédiat PayPal',
        description: 'PayPal avec paiement immédiat requis',
        paymentMethods: ['paypal', 'credit_card'],
        immediatePay: true,
        isDefault: true
      },
      {
        id: 'pay_2',
        name: 'Paiement Flexible',
        description: 'Plusieurs méthodes acceptées',
        paymentMethods: ['paypal', 'credit_card', 'bank_transfer'],
        immediatePay: false,
        isDefault: false
      }
    ]

    return { shipping, returns, payment }
  }

  /**
   * Mock: Fetch categories for testing
   */
  const fetchCategoriesMock = async (): Promise<EbayCategory[]> => {
    await new Promise(resolve => setTimeout(resolve, 600))

    return [
      {
        id: '11450',
        name: 'Vêtements, accessoires',
        level: 1,
        leafCategory: false,
        children: [
          {
            id: '11483',
            name: 'Vêtements homme',
            parentId: '11450',
            level: 2,
            leafCategory: false,
            children: [
              { id: '57988', name: 'T-shirts', parentId: '11483', level: 3, leafCategory: true },
              { id: '57989', name: 'Chemises', parentId: '11483', level: 3, leafCategory: true },
              { id: '57990', name: 'Jeans', parentId: '11483', level: 3, leafCategory: true },
              { id: '57991', name: 'Vestes & Manteaux', parentId: '11483', level: 3, leafCategory: true },
              { id: '57992', name: 'Pulls & Sweats', parentId: '11483', level: 3, leafCategory: true }
            ]
          },
          {
            id: '11484',
            name: 'Vêtements femme',
            parentId: '11450',
            level: 2,
            leafCategory: false,
            children: [
              { id: '63861', name: 'Robes', parentId: '11484', level: 3, leafCategory: true },
              { id: '63862', name: 'Tops & T-shirts', parentId: '11484', level: 3, leafCategory: true },
              { id: '63863', name: 'Jupes', parentId: '11484', level: 3, leafCategory: true },
              { id: '63864', name: 'Pantalons', parentId: '11484', level: 3, leafCategory: true }
            ]
          },
          {
            id: '11485',
            name: 'Chaussures',
            parentId: '11450',
            level: 2,
            leafCategory: false,
            children: [
              { id: '93427', name: 'Baskets', parentId: '11485', level: 3, leafCategory: true },
              { id: '93428', name: 'Chaussures de ville', parentId: '11485', level: 3, leafCategory: true },
              { id: '93429', name: 'Bottes', parentId: '11485', level: 3, leafCategory: true }
            ]
          }
        ]
      },
      {
        id: '26395',
        name: 'Maison, jardin',
        level: 1,
        leafCategory: false,
        children: [
          { id: '38227', name: 'Décoration', parentId: '26395', level: 2, leafCategory: true },
          { id: '38228', name: 'Mobilier', parentId: '26395', level: 2, leafCategory: true }
        ]
      }
    ]
  }

  return {
    fetchPolicies,
    createPaymentPolicy,
    createFulfillmentPolicy,
    createReturnPolicy,
    updatePaymentPolicy,
    updateFulfillmentPolicy,
    updateReturnPolicy,
    deletePolicy,
    applyPolicyToOffers,
    fetchPoliciesMock,
    fetchCategoriesMock
  }
}

/**
 * Composable pour gérer les appels API d'abonnement
 *
 * Fournit des méthodes pour :
 * - Récupérer les informations d'abonnement
 * - Lister les tiers disponibles
 * - Simuler le paiement d'un upgrade
 * - Acheter des crédits IA
 */

export interface SubscriptionInfo {
  user_id: number
  current_tier: string
  price: number

  // Quotas
  max_products: number
  max_platforms: number
  ai_credits_monthly: number

  // Usage counters
  current_products_count: number
  current_platforms_count: number

  // AI Credits
  ai_credits_purchased: number
  ai_credits_used_this_month: number
  ai_credits_remaining: number
}

export interface SubscriptionTier {
  tier: string
  price: number
  max_products: number
  max_platforms: number
  ai_credits_monthly: number
  is_current: boolean
}

export interface TiersResponse {
  tiers: SubscriptionTier[]
}

export interface CreditPack {
  id: number
  credits: number
  price: number
  price_per_credit: number
  is_popular: boolean
  display_order: number
}

export interface CreditPacksResponse {
  packs: CreditPack[]
}

export const useSubscription = () => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()

  /**
   * Récupère les informations d'abonnement de l'utilisateur connecté
   */
  const getSubscriptionInfo = async (): Promise<SubscriptionInfo> => {
    const response = await $fetch<SubscriptionInfo>(`${config.public.apiBaseUrl}/subscription/info`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    return response
  }

  /**
   * Récupère la liste des tiers d'abonnement disponibles
   */
  const getAvailableTiers = async (): Promise<SubscriptionTier[]> => {
    const response = await $fetch<TiersResponse>(`${config.public.apiBaseUrl}/subscription/tiers`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    return response.tiers
  }

  /**
   * Simule le paiement et effectue l'upgrade d'abonnement
   *
   * @param newTier - Le nouveau tier souhaité (ex: "pro")
   */
  const simulateUpgradePayment = async (newTier: string): Promise<SubscriptionInfo> => {
    const response = await $fetch<SubscriptionInfo>(`${config.public.apiBaseUrl}/subscription/payment/simulate-upgrade`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${authStore.token}`
      },
      body: {
        new_tier: newTier
      }
    })
    return response
  }

  /**
   * Simule l'achat de crédits IA
   *
   * @param credits - Nombre de crédits à acheter
   */
  const purchaseCredits = async (credits: number): Promise<SubscriptionInfo> => {
    const response = await $fetch<SubscriptionInfo>(`${config.public.apiBaseUrl}/subscription/credits/purchase`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${authStore.token}`
      },
      body: {
        credits
      }
    })
    return response
  }

  /**
   * Récupère la liste des packs de crédits IA disponibles
   *
   * Endpoint public (pas d'authentification requise)
   * Les prix sont récupérés depuis la base de données
   */
  const getCreditPacks = async (): Promise<CreditPack[]> => {
    const response = await $fetch<CreditPacksResponse>(
      `${config.public.apiBaseUrl}/subscription/credit-packs`
      // PAS de headers Authorization (endpoint public)
    )
    return response.packs
  }

  return {
    getSubscriptionInfo,
    getAvailableTiers,
    simulateUpgradePayment,
    purchaseCredits,
    getCreditPacks
  }
}

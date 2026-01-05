/**
 * Composable for fetching pricing plans from the API.
 *
 * Used on the landing page to display subscription plans dynamically.
 * Data comes from the database, allowing price changes without code deployment.
 *
 * @author Claude
 * @date 2024-12-24
 */

export interface PricingFeature {
  feature_text: string
  display_order: number
}

export interface PricingPlan {
  tier: string
  display_name: string
  description: string | null
  price: number
  annual_discount_percent: number
  is_popular: boolean
  cta_text: string | null
  max_products: number
  max_platforms: number
  ai_credits_monthly: number
  features: PricingFeature[]
}

interface SubscriptionTiersResponse {
  tiers: PricingPlan[]
}

export const usePricing = () => {
  const config = useRuntimeConfig()
  const plans = ref<PricingPlan[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Fetch pricing plans from the API.
   * This is a public endpoint - no authentication required.
   */
  const fetchPricingPlans = async (): Promise<PricingPlan[]> => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<SubscriptionTiersResponse>(
        `${config.public.apiBaseUrl}/subscription/tiers`
      )
      plans.value = response.tiers
      return response.tiers
    } catch (err) {
      console.error('Failed to fetch pricing plans:', err)
      error.value = 'Failed to load pricing plans'
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * Calculate the annual price with discount.
   */
  const getAnnualPrice = (plan: PricingPlan): number => {
    if (plan.annual_discount_percent === 0) {
      return plan.price
    }
    const discount = plan.price * (plan.annual_discount_percent / 100)
    return Math.round(plan.price - discount)
  }

  /**
   * Calculate annual savings.
   */
  const getAnnualSavings = (plan: PricingPlan): number => {
    if (plan.annual_discount_percent === 0) {
      return 0
    }
    const monthlyTotal = plan.price * 12
    const annualPrice = getAnnualPrice(plan) * 12
    return monthlyTotal - annualPrice
  }

  return {
    plans,
    loading,
    error,
    fetchPricingPlans,
    getAnnualPrice,
    getAnnualSavings
  }
}

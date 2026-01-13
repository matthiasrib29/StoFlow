/**
 * Composable for intelligent product pricing calculations
 *
 * Provides API integration with the pricing algorithm endpoint.
 * Handles loading states, error management, and price result caching.
 *
 * Created: 2026-01-12
 * Phase: 06-01 (Pricing Algorithm Feature)
 * Tests: tests/unit/usePricingCalculation.spec.ts (11 tests, full coverage)
 */

export interface PriceInput {
  brand: string
  category: string
  materials: string[]
  model_name?: string
  condition_score: number  // 0-10
  supplements: string[]
  condition_sensitivity: number  // 0.5-1.5
  actual_origin: string
  expected_origins: string[]
  actual_decade: string
  expected_decades: string[]
  actual_trends: string[]
  expected_trends: string[]
  actual_features: string[]
  expected_features: string[]
}

export interface AdjustmentBreakdown {
  condition: number
  origin: number
  decade: number
  trend: number
  feature: number
  total: number
}

export interface PriceOutput {
  quick_price: string
  standard_price: string
  premium_price: string
  base_price: string
  model_coefficient: number
  adjustments: AdjustmentBreakdown
  brand: string
  group: string
  model_name?: string
}

export const usePricingCalculation = () => {
  const api = useApi()
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const priceResult = ref<PriceOutput | null>(null)

  const calculatePrice = async (input: PriceInput) => {
    isLoading.value = true
    error.value = null
    priceResult.value = null

    try {
      const response = await api.post('/pricing/calculate', input)
      priceResult.value = response as PriceOutput
      return response as PriceOutput
    } catch (err: unknown) {
      // Handle different error types
      const error_obj = err as { response?: { status?: number; data?: { detail?: string } } }
      if (error_obj.response?.status === 400) {
        error.value = 'Invalid product data. Please check all fields.'
      } else if (error_obj.response?.status === 504) {
        error.value = 'Pricing calculation timed out. Please try again.'
      } else if (error_obj.response?.status === 500) {
        error.value = 'Failed to generate pricing data. Please try again later.'
      } else {
        error.value = error_obj.response?.data?.detail || 'An error occurred during price calculation'
      }
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const reset = () => {
    priceResult.value = null
    error.value = null
  }

  return {
    isLoading: readonly(isLoading),
    error: readonly(error),
    priceResult: readonly(priceResult),
    calculatePrice,
    reset
  }
}

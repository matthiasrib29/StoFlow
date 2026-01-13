/**
 * Composable for managing AI credits state
 *
 * Provides reactive AI credits remaining count and fetch function.
 * Used by product creation and editing pages.
 */
export const useAiCredits = () => {
  const { get } = useApi()
  const aiCreditsRemaining = ref<number | null>(null)

  const fetchAICredits = async () => {
    try {
      const response = await get<{ ai_credits_remaining: number }>('/subscription/info')
      aiCreditsRemaining.value = response?.ai_credits_remaining ?? null
    } catch (error) {
      console.warn('[useAiCredits] Failed to fetch AI credits', error)
      aiCreditsRemaining.value = null
    }
  }

  return {
    aiCreditsRemaining,
    fetchAICredits
  }
}

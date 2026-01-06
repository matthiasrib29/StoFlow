/**
 * Composable pour gérer les appels API Stripe Checkout
 *
 * Fournit des méthodes pour :
 * - Créer une session Checkout (subscriptions ou crédits)
 * - Créer une session Customer Portal (gérer l'abonnement)
 */
import { subscriptionLogger } from '~/utils/logger'

export interface CheckoutSessionRequest {
  payment_type: 'subscription' | 'credits'
  tier?: string  // Pour subscriptions
  credits?: number  // Pour achats de crédits
}

export interface CheckoutSessionResponse {
  session_id: string
  url: string
}

export interface CustomerPortalResponse {
  url: string
}

export const useStripe = () => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()

  /**
   * Crée une session Stripe Checkout et redirige l'utilisateur
   *
   * @param request - Type de paiement et détails
   * @returns URL de la session Checkout
   */
  const createCheckoutSession = async (request: CheckoutSessionRequest): Promise<CheckoutSessionResponse> => {
    const response = await $fetch<CheckoutSessionResponse>(`${config.public.apiBaseUrl}/stripe/create-checkout-session`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${authStore.token}`
      },
      body: request
    })
    return response
  }

  /**
   * Créer une session Customer Portal pour gérer l'abonnement
   *
   * Le Customer Portal permet à l'utilisateur de:
   * - Mettre à jour son moyen de paiement
   * - Annuler son abonnement
   * - Voir l'historique des factures
   *
   * @returns URL du Customer Portal
   */
  const createCustomerPortalSession = async (): Promise<CustomerPortalResponse> => {
    const response = await $fetch<CustomerPortalResponse>(`${config.public.apiBaseUrl}/stripe/customer-portal`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    return response
  }

  /**
   * Redirige l'utilisateur vers Stripe Checkout
   *
   * @param request - Type de paiement et détails
   */
  const redirectToCheckout = async (request: CheckoutSessionRequest) => {
    try {
      const { url } = await createCheckoutSession(request)
      // Redirection vers Stripe Checkout
      window.location.href = url
    } catch (error) {
      subscriptionLogger.error('Error creating checkout session', { error })
      throw error
    }
  }

  /**
   * Redirige l'utilisateur vers le Customer Portal Stripe
   */
  const redirectToCustomerPortal = async () => {
    try {
      const { url } = await createCustomerPortalSession()
      // Redirection vers le Customer Portal
      window.location.href = url
    } catch (error) {
      subscriptionLogger.error('Error creating customer portal session', { error })
      throw error
    }
  }

  return {
    createCheckoutSession,
    createCustomerPortalSession,
    redirectToCheckout,
    redirectToCustomerPortal
  }
}

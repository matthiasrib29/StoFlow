/**
 * Composable for eBay OAuth authentication
 * Handles OAuth flow, token exchange, and connection status
 *
 * SECURITY: Implements state parameter for CSRF protection
 * - Generates cryptographic nonce before OAuth initiation
 * - Validates state in callback to prevent CSRF attacks
 */

import type { EbayAccount, EbayTokens } from '~/types/ebay'
import { oauthLogger } from '~/utils/logger'

// Session storage key for OAuth state
const OAUTH_STATE_KEY = 'ebay_oauth_state'
const OAUTH_STATE_TIMESTAMP_KEY = 'ebay_oauth_state_ts'
const STATE_MAX_AGE_MS = 10 * 60 * 1000 // 10 minutes

/**
 * Generate a cryptographically secure random state
 */
const generateState = (): string => {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

/**
 * Store OAuth state in sessionStorage
 */
const storeState = (state: string): void => {
  sessionStorage.setItem(OAUTH_STATE_KEY, state)
  sessionStorage.setItem(OAUTH_STATE_TIMESTAMP_KEY, Date.now().toString())
}

/**
 * Retrieve and validate stored OAuth state
 */
const retrieveAndValidateState = (receivedState: string): boolean => {
  const storedState = sessionStorage.getItem(OAUTH_STATE_KEY)
  const storedTimestamp = sessionStorage.getItem(OAUTH_STATE_TIMESTAMP_KEY)

  // Clean up storage
  sessionStorage.removeItem(OAUTH_STATE_KEY)
  sessionStorage.removeItem(OAUTH_STATE_TIMESTAMP_KEY)

  // Validate state exists
  if (!storedState || !storedTimestamp) {
    oauthLogger.warn('No stored OAuth state found')
    return false
  }

  // Validate state hasn't expired
  const timestamp = parseInt(storedTimestamp, 10)
  if (Date.now() - timestamp > STATE_MAX_AGE_MS) {
    oauthLogger.warn('OAuth state expired')
    return false
  }

  // Validate state matches
  if (storedState !== receivedState) {
    oauthLogger.warn('OAuth state mismatch - possible CSRF attack')
    return false
  }

  return true
}

/**
 * Clear any pending OAuth state
 */
const clearState = (): void => {
  sessionStorage.removeItem(OAUTH_STATE_KEY)
  sessionStorage.removeItem(OAUTH_STATE_TIMESTAMP_KEY)
}

interface OAuthCallbackResponse {
  tokens: EbayTokens
  account: EbayAccount
}

interface ConnectionStatus {
  connected: boolean
  account_info?: Record<string, any>
  sandbox_mode?: boolean
  access_token_expires_at?: string
}

export const useEbayOAuth = () => {
  const config = useRuntimeConfig()
  const api = useApi()

  /**
   * Generate eBay OAuth URL
   */
  const getOAuthUrl = (): string => {
    const baseUrl = 'https://auth.ebay.com/oauth2/authorize'
    const params = new URLSearchParams({
      client_id: config.public.ebayClientId || 'YOUR_EBAY_CLIENT_ID',
      response_type: 'code',
      redirect_uri: config.public.ebayRedirectUri || `${window.location.origin}/dashboard/platforms/ebay/callback`,
      scope: [
        'https://api.ebay.com/oauth/api_scope',
        'https://api.ebay.com/oauth/api_scope/sell.marketing.readonly',
        'https://api.ebay.com/oauth/api_scope/sell.marketing',
        'https://api.ebay.com/oauth/api_scope/sell.inventory.readonly',
        'https://api.ebay.com/oauth/api_scope/sell.inventory',
        'https://api.ebay.com/oauth/api_scope/sell.account.readonly',
        'https://api.ebay.com/oauth/api_scope/sell.account',
        'https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly',
        'https://api.ebay.com/oauth/api_scope/sell.fulfillment'
      ].join(' ')
    })

    return `${baseUrl}?${params.toString()}`
  }

  /**
   * Initiate OAuth flow via popup
   * Returns a promise that resolves when auth is complete
   *
   * SECURITY: Generates and stores a state parameter to prevent CSRF attacks
   */
  const initiateOAuth = async (onSuccess: () => void): Promise<boolean> => {
    try {
      // Generate CSRF protection state
      const state = generateState()
      storeState(state)
      oauthLogger.debug('OAuth state generated and stored')

      // Get OAuth URL from backend with state parameter
      const { auth_url } = await api.get<{ auth_url: string }>('/api/integrations/ebay/connect', {
        params: { state }
      })

      // Validate that auth_url is on eBay domain (prevent redirect attacks)
      try {
        const url = new URL(auth_url)
        const validDomains = ['auth.ebay.com', 'signin.ebay.com', 'auth.sandbox.ebay.com']
        if (!validDomains.some(domain => url.hostname === domain || url.hostname.endsWith('.' + domain))) {
          clearState()
          throw new Error('Invalid OAuth URL domain')
        }
      } catch (urlError) {
        clearState()
        throw new Error('Invalid OAuth URL format')
      }

      // Open OAuth popup with security flags
      const popup = window.open(
        auth_url,
        'ebay_oauth',
        'width=600,height=700,scrollbars=yes,noopener'
      )

      if (!popup) {
        clearState()
        throw new Error('Popup bloquée. Veuillez autoriser les popups pour ce site.')
      }

      return new Promise((resolve, reject) => {
        const checkClosed = setInterval(() => {
          if (popup.closed) {
            clearInterval(checkClosed)
            // Check if connection was successful by calling onSuccess
            onSuccess()
            resolve(true)
          }
        }, 500)

        // Timeout after 5 minutes
        setTimeout(() => {
          clearInterval(checkClosed)
          clearState()
          popup.close()
          reject(new Error('Délai d\'authentification expiré'))
        }, 5 * 60 * 1000)
      })
    } catch (error: any) {
      clearState()
      throw new Error(error.message || 'Erreur lors de l\'authentification eBay')
    }
  }

  /**
   * Exchange OAuth code for tokens
   */
  const exchangeCodeForTokens = async (code: string): Promise<OAuthCallbackResponse> => {
    const response = await api.post<OAuthCallbackResponse>('/api/integrations/ebay/callback', { code })
    return response
  }

  /**
   * Check current connection status
   */
  const checkConnectionStatus = async (): Promise<ConnectionStatus> => {
    const status = await api.get<ConnectionStatus>('/api/integrations/ebay/status')
    return status
  }

  /**
   * Parse account info from status response
   */
  const parseAccountFromStatus = (status: ConnectionStatus): EbayAccount | null => {
    if (!status.connected || !status.account_info) {
      return null
    }

    const info = status.account_info
    return {
      userId: info.userId || '',
      username: info.username || '',
      email: info.email || '',
      accountType: info.accountType?.toLowerCase() || 'individual',
      registrationDate: info.registrationDate || '',
      sellerLevel: info.sellerLevel || 'standard',
      feedbackScore: info.feedbackScore || 0,
      feedbackPercentage: info.feedbackPercentage || 0,
      businessName: info.businessName,
      firstName: info.firstName,
      lastName: info.lastName,
      phone: info.phone,
      address: info.address,
      marketplace: info.marketplace,
      sandboxMode: status.sandbox_mode,
      accessTokenExpiresAt: status.access_token_expires_at
    }
  }

  /**
   * Disconnect eBay account
   */
  const disconnect = async (): Promise<void> => {
    await api.post('/api/integrations/ebay/disconnect')
  }

  /**
   * Mock connection for testing
   */
  const connectMock = async (): Promise<{ account: EbayAccount; tokens: EbayTokens }> => {
    await new Promise(resolve => setTimeout(resolve, 1500))

    const account: EbayAccount = {
      userId: 'ebay_user_123',
      username: 'stoflow_seller',
      email: 'seller@stoflow.com',
      accountType: 'business',
      registrationDate: '2020-03-15',
      sellerLevel: 'top_rated',
      feedbackScore: 2847,
      feedbackPercentage: 99.8,
      storeName: 'Stoflow Fashion Store',
      storeUrl: 'https://www.ebay.fr/str/stoflowfashion'
    }

    const tokens: EbayTokens = {
      accessToken: 'mock_access_token',
      refreshToken: 'mock_refresh_token',
      expiresAt: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
      scope: ['sell.inventory', 'sell.account', 'sell.fulfillment']
    }

    return { account, tokens }
  }

  /**
   * Validate OAuth state from callback
   * SECURITY: Must be called before processing OAuth callback
   */
  const validateState = (receivedState: string | null): boolean => {
    if (!receivedState) {
      oauthLogger.warn('No state parameter in callback')
      return false
    }
    return retrieveAndValidateState(receivedState)
  }

  return {
    getOAuthUrl,
    initiateOAuth,
    exchangeCodeForTokens,
    checkConnectionStatus,
    parseAccountFromStatus,
    disconnect,
    connectMock,
    validateState,
    clearState
  }
}

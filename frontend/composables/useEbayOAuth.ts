/**
 * Composable for eBay OAuth authentication
 * Handles OAuth flow, token exchange, and connection status
 */

import type { EbayAccount, EbayTokens } from '~/types/ebay'

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
   */
  const initiateOAuth = async (onSuccess: () => void): Promise<boolean> => {
    try {
      // Get OAuth URL from backend
      const { auth_url } = await api.get<{ auth_url: string }>('/api/integrations/ebay/connect')

      // Open OAuth popup
      const popup = window.open(auth_url, 'ebay_oauth', 'width=600,height=700,scrollbars=yes')

      if (!popup) {
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
          popup.close()
          reject(new Error('Délai d\'authentification expiré'))
        }, 5 * 60 * 1000)
      })
    } catch (error: any) {
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

  return {
    getOAuthUrl,
    initiateOAuth,
    exchangeCodeForTokens,
    checkConnectionStatus,
    parseAccountFromStatus,
    disconnect,
    connectMock
  }
}

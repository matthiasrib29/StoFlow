/**
 * Composable pour gérer les appels API avec authentification JWT
 *
 * Security (2026-01-20):
 * - Uses httpOnly cookies for JWT storage (XSS protection)
 * - Includes CSRF token header for state-changing requests
 * - credentials: 'include' ensures cookies are sent cross-origin
 * - Backward compatible: still supports localStorage during migration
 */

import { useTokenValidator } from '~/composables/useTokenValidator'
import { apiLogger } from '~/utils/logger'

interface ApiError {
  detail: string
  status?: number
}

// HTTP methods that require CSRF protection
const CSRF_PROTECTED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']

/**
 * Get CSRF token from cookie (for double-submit pattern)
 */
const getCsrfToken = (): string | null => {
  if (!import.meta.client) return null

  const match = document.cookie.match(/csrf_token=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : null
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBaseUrl || 'http://localhost:8000/api'
  const { isValidToken, isTokenExpired, willExpireSoon } = useTokenValidator()

  /**
   * Récupère le token d'accès depuis localStorage avec validation
   * NOTE: Kept for backward compatibility during migration
   * TODO (2026-02-01): Remove after cookie migration complete
   */
  const getAccessToken = (): string | null => {
    if (import.meta.client) {
      const token = localStorage.getItem('token')

      // Validate token before returning
      if (token && isValidToken(token) && !isTokenExpired(token)) {
        return token
      }

      // Token invalid or expired
      if (token) {
        apiLogger.debug('Access token invalid/expired, will attempt refresh')
      }
      return null
    }
    return null
  }

  /**
   * Récupère le refresh token depuis localStorage avec validation
   * NOTE: Kept for backward compatibility during migration
   * TODO (2026-02-01): Remove after cookie migration complete
   */
  const getRefreshToken = (): string | null => {
    if (import.meta.client) {
      const token = localStorage.getItem('refresh_token')

      // Validate token structure (don't check expiry for refresh tokens)
      if (token && isValidToken(token)) {
        return token
      }

      return null
    }
    return null
  }

  /**
   * Sauvegarde les tokens dans localStorage
   * NOTE: Kept for backward compatibility during migration
   * TODO (2026-02-01): Remove after cookie migration complete
   */
  const saveTokens = (accessToken: string, refreshToken: string) => {
    if (import.meta.client) {
      localStorage.setItem('token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
    }
  }

  /**
   * Supprime les tokens du localStorage
   * NOTE: Kept for backward compatibility during migration
   * Cookies are cleared by the backend on logout
   */
  const clearTokens = () => {
    if (import.meta.client) {
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    }
  }

  /**
   * Effectue un appel API avec gestion automatique de l'authentification
   *
   * Security (2026-01-20):
   * - credentials: 'include' sends cookies automatically
   * - X-CSRF-Token header for state-changing requests
   * - Authorization header kept for backward compatibility
   */
  const apiCall = async <T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> => {
    const token = getAccessToken()
    const isFormData = options.body instanceof FormData
    const method = options.method?.toUpperCase() || 'GET'

    const headers: Record<string, string> = {
      // Don't set Content-Type for FormData - browser will set it with boundary
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers as Record<string, string>),
    }

    // Add CSRF token for state-changing requests
    if (CSRF_PROTECTED_METHODS.includes(method)) {
      const csrfToken = getCsrfToken()
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken
      }
    }

    // Add Bearer token for backward compatibility
    // NOTE: Cookie auth takes priority on backend, this is fallback
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const url = `${baseURL}${endpoint}`

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include',  // CRITICAL: Send cookies with every request
      })

      // Si le token est expiré (401), essayer de le rafraîchir
      if (response.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          // Retry la requête avec le nouveau token
          const newToken = getAccessToken()
          if (newToken) {
            headers['Authorization'] = `Bearer ${newToken}`
          }

          // Update CSRF token (may have changed after refresh)
          if (CSRF_PROTECTED_METHODS.includes(method)) {
            const newCsrfToken = getCsrfToken()
            if (newCsrfToken) {
              headers['X-CSRF-Token'] = newCsrfToken
            }
          }

          const retryResponse = await fetch(url, {
            ...options,
            headers,
            credentials: 'include',
          })

          if (!retryResponse.ok) {
            const error = await retryResponse.json()
            throw new Error(error.detail || 'Erreur lors de la requête API')
          }

          // Gérer les réponses sans contenu (204 No Content)
          if (retryResponse.status === 204 || retryResponse.headers.get('content-length') === '0') {
            return null as T
          }

          const contentType = retryResponse.headers.get('content-type')
          if (contentType && contentType.includes('application/json')) {
            return await retryResponse.json()
          }

          return null as T
        } else {
          // Le refresh a échoué, déconnecter l'utilisateur
          clearTokens()
          if (import.meta.client) {
            window.location.href = '/login'
          }
          throw new Error('Session expirée, veuillez vous reconnecter')
        }
      }

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Erreur lors de la requête API')
      }

      // Gérer les réponses sans contenu (204 No Content)
      if (response.status === 204 || response.headers.get('content-length') === '0') {
        return null as T
      }

      // Vérifier si la réponse contient du JSON avant de parser
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return await response.json()
      }

      return null as T
    } catch (error: any) {
      apiLogger.error('API Error', { error: error.message })
      throw error
    }
  }

  /**
   * Rafraîchit le token d'accès avec le refresh token
   *
   * Security (2026-01-20):
   * - Uses httpOnly cookie for refresh token (automatic via credentials: include)
   * - Falls back to localStorage body for backward compatibility
   */
  const refreshAccessToken = async (): Promise<boolean> => {
    try {
      // The refresh token will be sent automatically via httpOnly cookie
      // Body is kept for backward compatibility
      const refreshToken = getRefreshToken()

      const response = await fetch(`${baseURL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',  // CRITICAL: Send refresh_token cookie
        // Body for backward compatibility (cookie takes priority on backend)
        body: refreshToken ? JSON.stringify({ refresh_token: refreshToken }) : undefined,
      })

      if (!response.ok) return false

      const data = await response.json()

      // Store in localStorage for backward compatibility
      if (import.meta.client && data.access_token) {
        localStorage.setItem('token', data.access_token)
      }

      return true
    } catch (error) {
      apiLogger.error('Refresh token error', { error })
      return false
    }
  }

  /**
   * Méthodes HTTP simplifiées
   */
  const get = <T>(endpoint: string, options?: RequestInit): Promise<T> => {
    return apiCall<T>(endpoint, { ...options, method: 'GET' })
  }

  const post = <T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> => {
    const isFormData = data instanceof FormData
    return apiCall<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? (isFormData ? data : JSON.stringify(data)) : undefined,
    })
  }

  const put = <T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> => {
    const isFormData = data instanceof FormData
    return apiCall<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? (isFormData ? data : JSON.stringify(data)) : undefined,
    })
  }

  const patch = <T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> => {
    const isFormData = data instanceof FormData
    return apiCall<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? (isFormData ? data : JSON.stringify(data)) : undefined,
    })
  }

  const del = <T>(endpoint: string, options?: RequestInit): Promise<T> => {
    return apiCall<T>(endpoint, { ...options, method: 'DELETE' })
  }

  return {
    baseURL,
    get,
    post,
    put,
    patch,
    delete: del,
    del,  // Alias for delete
    getAccessToken,
    getRefreshToken,
    saveTokens,
    clearTokens,
    getCsrfToken,  // Export for components that need direct access
  }
}

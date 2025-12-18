/**
 * Composable pour gérer les appels API avec authentification JWT
 */

interface ApiError {
  detail: string
  status?: number
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiUrl || 'http://localhost:8000'

  /**
   * Récupère le token d'accès depuis localStorage
   */
  const getAccessToken = (): string | null => {
    if (process.client) {
      return localStorage.getItem('token')
    }
    return null
  }

  /**
   * Récupère le refresh token depuis localStorage
   */
  const getRefreshToken = (): string | null => {
    if (process.client) {
      return localStorage.getItem('refresh_token')
    }
    return null
  }

  /**
   * Sauvegarde les tokens dans localStorage
   */
  const saveTokens = (accessToken: string, refreshToken: string) => {
    if (process.client) {
      localStorage.setItem('token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
    }
  }

  /**
   * Supprime les tokens du localStorage
   */
  const clearTokens = () => {
    if (process.client) {
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    }
  }

  /**
   * Effectue un appel API avec gestion automatique de l'authentification
   */
  const apiCall = async <T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> => {
    const token = getAccessToken()

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    // Ajouter le token Bearer si disponible
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const url = `${baseURL}${endpoint}`

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      // Si le token est expiré (401), essayer de le rafraîchir
      if (response.status === 401 && token) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          // Retry la requête avec le nouveau token
          const newToken = getAccessToken()
          if (newToken) {
            headers['Authorization'] = `Bearer ${newToken}`
            const retryResponse = await fetch(url, {
              ...options,
              headers,
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
          }
        } else {
          // Le refresh a échoué, déconnecter l'utilisateur
          clearTokens()
          if (process.client) {
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
      console.error('API Error:', error)
      throw error
    }
  }

  /**
   * Rafraîchit le token d'accès avec le refresh token
   */
  const refreshAccessToken = async (): Promise<boolean> => {
    const refreshToken = getRefreshToken()
    if (!refreshToken) return false

    try {
      const response = await fetch(`${baseURL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (!response.ok) return false

      const data = await response.json()

      if (process.client) {
        localStorage.setItem('token', data.access_token)
      }

      return true
    } catch (error) {
      console.error('Refresh token error:', error)
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
    return apiCall<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  const put = <T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> => {
    return apiCall<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  const patch = <T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> => {
    return apiCall<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
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
    getAccessToken,
    getRefreshToken,
    saveTokens,
    clearTokens,
  }
}

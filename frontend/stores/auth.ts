/**
 * Auth Store
 *
 * Security (2026-01-20):
 * - JWT tokens stored in httpOnly cookies (XSS protection)
 * - CSRF token set by backend on login
 * - Backward compatible with localStorage during migration
 */
import { defineStore } from 'pinia'
import { useTokenValidator } from '~/composables/useTokenValidator'
import {
  setAuthData,
  getAuthData,
  clearTokens,
  setAccessToken,
  getAccessToken,
  getRefreshToken,
  setStorageConfig,
  recordActivity
} from '~/utils/secureStorage'
import { authLogger } from '~/utils/logger'

// Lazy-loaded WebSocket composable to avoid circular dependencies
// The composable is cached after first import
let wsComposable: ReturnType<typeof import('~/composables/useWebSocket').useWebSocket> | null = null

async function getWebSocket() {
  if (!wsComposable) {
    const { useWebSocket } = await import('~/composables/useWebSocket')
    wsComposable = useWebSocket()
  }
  return wsComposable
}

/**
 * Interface User basée sur le backend FastAPI
 * Correspond au modèle User dans /Stoflow_BackEnd/models/public/user.py
 */
export interface User {
  id: number
  email: string
  full_name: string
  role: 'user' | 'admin'
  subscription_tier: 'starter' | 'standard' | 'premium' | 'business' | 'enterprise'
  tenant_name?: string  // Database schema name for user's tenant
  // Onboarding fields (Added: 2024-12-08)
  business_name?: string
  account_type: 'individual' | 'professional'
  business_type?: 'resale' | 'dropshipping' | 'artisan' | 'retail' | 'other'
  estimated_products?: '0-50' | '50-200' | '200-500' | '500+'
  // Professional fields
  siret?: string
  vat_number?: string
  // Contact
  phone?: string
  country: string
  language: string
}

/**
 * Interface pour les données d'inscription complètes
 * Basée sur RegisterRequest dans /Stoflow_BackEnd/schemas/auth_schemas.py
 */
export interface RegisterData {
  email: string
  password: string
  full_name: string
  // Onboarding fields
  business_name?: string
  account_type?: 'individual' | 'professional'
  business_type?: 'resale' | 'dropshipping' | 'artisan' | 'retail' | 'other'
  estimated_products?: '0-50' | '50-200' | '200-500' | '500+'
  // Professional fields
  siret?: string
  vat_number?: string
  // Contact
  phone?: string
  country?: string
  language?: string
}

/**
 * Réponse du backend lors du login/register
 * Basée sur TokenResponse dans /Stoflow_BackEnd/schemas/auth_schemas.py
 */
interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user_id: number
  role: string
  subscription_tier: string
  csrf_token?: string
}

/**
 * Réponse du backend lors du refresh
 */
interface RefreshResponse {
  access_token: string
  token_type: string
  csrf_token?: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    token: null as string | null,
    refreshToken: null as string | null,
    csrfToken: null as string | null,
    isAuthenticated: false,
    isLoading: false,
    error: null as string | null
  }),

  getters: {
    currentUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated,
    subscriptionTier: (state) => state.user?.subscription_tier || 'starter'
  },

  actions: {
    /**
     * Inscription utilisateur via l'API FastAPI
     * Endpoint: POST /api/auth/register
     *
     * Business rule (backend - Updated: 2025-12-23):
     * - Email doit être unique globalement
     * - Password min 12 caractères avec complexité (1 majuscule, 1 minuscule, 1 chiffre, 1 char spécial)
     * - Full_name min 1 caractère, max 255
     * - Onboarding: business_name, account_type, business_type, estimated_products
     * - Si account_type = 'professional': siret et vat_number peuvent être fournis
     * - Crée automatiquement un schema PostgreSQL user_{id} pour isolation
     * - L'utilisateur doit vérifier son email avant de pouvoir se connecter
     */
    async register(registerData: RegisterData | { email: string, password: string, full_name: string }) {
      this.isLoading = true
      this.error = null

      try {
        const config = useRuntimeConfig()
        const baseURL = config.public.apiBaseUrl

        // Préparer les données en transformant full_name si nécessaire
        const requestData: any = { ...registerData }
        if ('fullName' in requestData) {
          requestData.full_name = requestData.fullName
          delete requestData.fullName
        }

        const response = await fetch(`${baseURL}/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData),
        })

        if (!response.ok) {
          const error = await response.json()
          // Handle Pydantic validation errors (detail is an array of objects)
          let errorMessage = 'Erreur lors de l\'inscription'
          if (error.detail) {
            if (typeof error.detail === 'string') {
              errorMessage = error.detail
            } else if (Array.isArray(error.detail)) {
              // Extract messages from Pydantic validation errors
              errorMessage = error.detail
                .map((err: any) => {
                  // Remove "Value error, " prefix if present
                  const msg = err.msg || err.message || String(err)
                  return msg.replace(/^Value error,\s*/i, '')
                })
                .join('\n')
            }
          }
          throw new Error(errorMessage)
        }

        const data = await response.json()

        // Le backend ne retourne plus de tokens
        // L'utilisateur doit d'abord vérifier son email
        authLogger.info('Registration successful, email verification required')

        return {
          success: true,
          requiresVerification: true,
          email: data.email || requestData.email,
          message: data.message
        }
      } catch (error: any) {
        this.error = error.message || 'Erreur lors de l\'inscription'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Connexion utilisateur via l'API FastAPI
     * Endpoint: POST /api/auth/login?source=web
     *
     * Security (2026-01-20):
     * - Uses credentials: 'include' to receive httpOnly cookies
     * - Tokens stored in cookies by backend (not localStorage)
     * - Backward compatible: still stores in localStorage during migration
     *
     * Business rules (backend):
     * - Rate limiting: 10 tentatives par 5 minutes par IP
     * - Timing attack protection: délai aléatoire 100-300ms
     * - Password min 8 caractères (au login, 12 au register)
     * - Vérifie is_active=True
     * - Met à jour last_login
     */
    async login(email: string, password: string) {
      this.isLoading = true
      this.error = null

      try {
        const config = useRuntimeConfig()
        const baseURL = config.public.apiBaseUrl

        const response = await fetch(`${baseURL}/auth/login?source=web`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',  // CRITICAL: Receive cookies from server
          body: JSON.stringify({
            email,
            password
          }),
        })

        if (!response.ok) {
          const error = await response.json()
          // Gestion du rate limiting
          if (response.status === 429) {
            throw new Error('Trop de tentatives de connexion. Veuillez réessayer dans quelques minutes.')
          }
          throw new Error(error.detail || 'Email ou mot de passe incorrect')
        }

        const data: AuthResponse = await response.json()

        // Note: Le backend ne retourne PAS l'email ni le full_name dans TokenResponse
        // On va devoir fetch les infos de l'utilisateur via un endpoint dédié
        // Pour l'instant, on stocke ce qu'on a
        const user: User = {
          id: data.user_id,
          email: email, // Temporaire - devrait venir d'un endpoint /me
          full_name: '', // À récupérer via un endpoint /me
          role: data.role as 'user' | 'admin',
          subscription_tier: data.subscription_tier as User['subscription_tier'],
          account_type: 'individual', // Default - should be fetched from /me
          country: 'FR', // Default - should be fetched from /me
          language: 'fr' // Default - should be fetched from /me
        }

        this.user = user
        // Tokens are now primarily in cookies, but keep in state for backward compat
        this.token = data.access_token
        this.refreshToken = data.refresh_token
        this.csrfToken = data.csrf_token || null
        this.isAuthenticated = true

        // Store in secure storage for backward compatibility during migration
        // TODO (2026-02-01): Remove localStorage storage after full cookie adoption
        if (import.meta.client) {
          setAuthData({
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            user,
            expiresInSeconds: 900 // 15 minutes (matches backend access token)
          })

          // Connect WebSocket after successful login (2026-01-19)
          authLogger.debug('Connecting WebSocket after login...')
          const ws = await getWebSocket()
          ws.connect(data.access_token, data.user_id)
        }

        return { success: true }
      } catch (error: any) {
        this.error = error.message || 'Erreur de connexion'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Déconnexion
     *
     * Security (2026-01-20):
     * - Calls backend /auth/logout to clear httpOnly cookies
     * - Also clears localStorage for backward compatibility
     */
    async logout() {
      // Disconnect WebSocket BEFORE clearing auth (2026-01-19)
      if (import.meta.client && wsComposable) {
        authLogger.debug('Disconnecting WebSocket on logout...')
        wsComposable.disconnect()
      }

      // Call backend to clear cookies
      if (import.meta.client) {
        try {
          const config = useRuntimeConfig()
          const baseURL = config.public.apiBaseUrl

          await fetch(`${baseURL}/auth/logout`, {
            method: 'POST',
            credentials: 'include',  // Send cookies for revocation
          })
        } catch (error) {
          // Log but don't throw - we still want to clear local state
          authLogger.warn('Logout API call failed:', error)
        }

        // Clear all tokens from secure storage (backward compatibility)
        clearTokens()
      }

      this.user = null
      this.token = null
      this.refreshToken = null
      this.csrfToken = null
      this.isAuthenticated = false
      this.error = null
    },

    /**
     * Charger la session depuis secure storage
     * Appelé au démarrage de l'app pour restaurer la session
     *
     * Security: Validates tokens before restoring session
     */
    loadFromStorage() {
      if (import.meta.client) {
        const { validateStoredTokens, willExpireSoon } = useTokenValidator()

        // Validate stored tokens first
        const { accessValid, refreshValid } = validateStoredTokens()

        if (!refreshValid) {
          // No valid refresh token = cannot restore session
          authLogger.debug('No valid refresh token, session not restored')
          this.logout()
          return
        }

        // Get auth data from secure storage
        const { accessToken, refreshToken, user } = getAuthData()

        if (refreshToken && user) {
          try {
            this.user = user as User
            this.refreshToken = refreshToken

            // CRITICAL: Set token BEFORE isAuthenticated to avoid race condition
            // with WebSocket plugin that watches isAuthenticated (2026-01-19)
            if (accessValid && accessToken) {
              this.token = accessToken

              // Check if token will expire soon (within 5 minutes)
              if (willExpireSoon(accessToken, 5)) {
                authLogger.debug('Token expiring soon, refreshing...')
                // Note: refreshAccessToken is async, but we can proceed
                // The token is still valid for a few minutes
              }
            }

            // Set isAuthenticated LAST
            this.isAuthenticated = true

            // Connect WebSocket after session restore (2026-01-19)
            // Note: loadFromStorage is sync, so we use .then() for async WS connection
            if (accessValid && accessToken) {
              authLogger.debug('Connecting WebSocket after session restore...')
              getWebSocket().then(ws => ws.connect(accessToken, (user as User).id))
            }

            // Handle token refresh after isAuthenticated is set
            if (accessValid && accessToken && willExpireSoon(accessToken, 5)) {
              this.refreshAccessToken()
            } else if (!accessValid || !accessToken) {
              // Access token invalid/expired but refresh token valid
              // Attempt to get a new access token
              authLogger.debug('Access token expired, refreshing...')
              this.refreshAccessToken()
            }
          } catch (error) {
            authLogger.error('Error loading session:', error)
            this.logout()
          }
        }
      }
    },

    /**
     * Rafraîchir le token d'accès avec le refresh token
     * Endpoint: POST /api/auth/refresh
     *
     * Security (2026-01-20):
     * - Uses httpOnly cookie for refresh token (via credentials: include)
     * - Falls back to body for backward compatibility
     *
     * Business rules (backend):
     * - Refresh token valide 7 jours
     * - Access token valide 15 minutes
     * - Vérifie que l'utilisateur est toujours actif
     * - Retourne seulement le nouvel access_token (pas de nouveau refresh_token)
     */
    async refreshAccessToken(): Promise<boolean> {
      // Note: We may not have refreshToken in state if using cookie-only auth
      // The cookie will be sent automatically via credentials: include

      try {
        const config = useRuntimeConfig()
        const baseURL = config.public.apiBaseUrl

        const response = await fetch(`${baseURL}/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',  // CRITICAL: Send refresh_token cookie
          // Body for backward compatibility (cookie takes priority on backend)
          body: this.refreshToken ? JSON.stringify({
            refresh_token: this.refreshToken
          }) : undefined,
        })

        if (!response.ok) {
          // Si le refresh échoue (401), le refresh token est expiré ou invalide
          await this.logout()
          return false
        }

        const data: RefreshResponse = await response.json()

        // Mettre à jour l'access token et le CSRF token
        this.token = data.access_token
        if (data.csrf_token) {
          this.csrfToken = data.csrf_token
        }

        if (import.meta.client) {
          // Update access token in secure storage for backward compatibility
          setAccessToken(data.access_token, 900) // 15 minutes (matches backend)

          // Update WebSocket auth without reconnecting (2026-01-19)
          if (wsComposable && this.user) {
            wsComposable.updateAuth(data.access_token, this.user.id)
          }
        }

        return true
      } catch (error) {
        authLogger.error('Token refresh error:', error)
        await this.logout()
        return false
      }
    },

    /**
     * Check authentication status by calling /users/me endpoint
     *
     * Security (2026-01-20):
     * - Uses httpOnly cookie for auth (via credentials: include)
     * - Useful for checking if user has valid session without localStorage
     * - Returns user data if authenticated, null otherwise
     */
    async checkAuth(): Promise<User | null> {
      try {
        const config = useRuntimeConfig()
        const baseURL = config.public.apiBaseUrl

        const response = await fetch(`${baseURL}/users/me`, {
          method: 'GET',
          credentials: 'include',  // Send access_token cookie
        })

        if (!response.ok) {
          return null
        }

        const userData = await response.json()

        // Update store state
        const user: User = {
          id: userData.id,
          email: userData.email,
          full_name: userData.full_name || '',
          role: userData.role as 'user' | 'admin',
          subscription_tier: userData.subscription_tier as User['subscription_tier'],
          account_type: userData.account_type || 'individual',
          country: userData.country || 'FR',
          language: userData.language || 'fr'
        }

        this.user = user
        this.isAuthenticated = true

        return user
      } catch (error) {
        authLogger.debug('checkAuth failed:', error)
        return null
      }
    }
  }
})

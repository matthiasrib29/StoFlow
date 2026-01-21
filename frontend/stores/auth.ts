import { defineStore } from 'pinia'
import { useTokenValidator } from '~/composables/useTokenValidator'
import {
  setAuthData,
  getAuthData,
  clearTokens,
  getRefreshToken,
  setStorageConfig,
  recordActivity
  // setAccessToken, getAccessToken removed - access token no longer stored
} from '~/utils/secureStorage'
import { authLogger } from '~/utils/logger'

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
}

/**
 * Réponse du backend lors du refresh
 */
interface RefreshResponse {
  access_token: string
  token_type: string
}

// Token refresh interval (55 minutes = 55 * 60 * 1000 ms)
// Security Fix 2026-01-20: Auto-refresh before 60min expiry
const TOKEN_REFRESH_INTERVAL_MS = 55 * 60 * 1000

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    token: null as string | null, // Access token in memory only (not persisted)
    refreshToken: null as string | null,
    isAuthenticated: false,
    isLoading: false,
    error: null as string | null,
    refreshIntervalId: null as ReturnType<typeof setInterval> | null // For auto-refresh
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
        this.token = data.access_token
        this.refreshToken = data.refresh_token
        this.isAuthenticated = true

        // Store in secure storage (refresh token + user only)
        // Security Fix 2026-01-20: Access token stays in memory only (not persisted)
        // This prevents XSS attacks from stealing tokens via sessionStorage
        if (import.meta.client) {
          setAuthData({
            refreshToken: data.refresh_token,
            user
            // accessToken intentionally NOT stored - kept in this.token (memory only)
          })

          // Start automatic token refresh
          this.startAutoRefresh()
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
     */
    logout() {
      // Stop auto-refresh timer
      this.stopAutoRefresh()

      this.user = null
      this.token = null
      this.refreshToken = null
      this.isAuthenticated = false
      this.error = null

      if (import.meta.client) {
        // Clear all tokens from secure storage
        clearTokens()
      }
    },

    /**
     * Start automatic token refresh (every 55 minutes)
     * Security Fix 2026-01-20: Proactive token refresh before expiry
     */
    startAutoRefresh() {
      // Clear any existing interval
      this.stopAutoRefresh()

      // Set up new interval
      this.refreshIntervalId = setInterval(async () => {
        authLogger.debug('Auto-refreshing access token...')
        const success = await this.refreshAccessToken()
        if (!success) {
          authLogger.warn('Auto-refresh failed, user may need to re-login')
          // Don't logout here - let the user continue until next API call fails
        }
      }, TOKEN_REFRESH_INTERVAL_MS)

      authLogger.debug('Auto-refresh timer started (55 min interval)')
    },

    /**
     * Stop automatic token refresh
     */
    stopAutoRefresh() {
      if (this.refreshIntervalId) {
        clearInterval(this.refreshIntervalId)
        this.refreshIntervalId = null
        authLogger.debug('Auto-refresh timer stopped')
      }
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
            this.isAuthenticated = true

            // Security Fix 2026-01-20: Access token is NOT stored anymore
            // Always refresh on page load to get a fresh access token
            // This is more secure: even if XSS occurs, no access token in storage
            authLogger.debug('Restoring session, fetching fresh access token...')
            this.refreshAccessToken()

            // Start auto-refresh timer
            // Security Fix 2026-01-20: Ensure token refresh happens proactively
            this.startAutoRefresh()
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
     * Business rules (backend):
     * - Refresh token valide 7 jours
     * - Access token valide 1 heure
     * - Vérifie que l'utilisateur est toujours actif
     * - Retourne seulement le nouvel access_token (pas de nouveau refresh_token)
     */
    async refreshAccessToken(): Promise<boolean> {
      if (!this.refreshToken) {
        this.logout()
        return false
      }

      try {
        const config = useRuntimeConfig()
        const baseURL = config.public.apiBaseUrl

        const response = await fetch(`${baseURL}/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            refresh_token: this.refreshToken
          }),
        })

        if (!response.ok) {
          // Si le refresh échoue (401), le refresh token est expiré ou invalide
          this.logout()
          return false
        }

        const data: RefreshResponse = await response.json()

        // Mettre à jour seulement l'access token (en mémoire uniquement)
        // Security Fix 2026-01-20: Access token NOT stored in sessionStorage
        this.token = data.access_token

        return true
      } catch (error) {
        authLogger.error('Token refresh error:', error)
        this.logout()
        return false
      }
    }
  }
})

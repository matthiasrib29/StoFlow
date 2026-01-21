/**
 * Secure Token Storage Utility
 *
 * SECURITY CONSIDERATIONS:
 *
 * Current implementation uses localStorage/sessionStorage which are vulnerable to XSS.
 * If an XSS attack occurs, tokens can be stolen.
 *
 * RECOMMENDED IMPROVEMENTS (requires backend changes):
 * 1. Use httpOnly cookies for token storage (best option)
 * 2. Implement token binding to prevent token theft
 * 3. Use short-lived access tokens with refresh via httpOnly cookie
 *
 * This utility provides:
 * - Centralized token storage management
 * - Option to use sessionStorage (tokens cleared on browser close)
 * - Token expiry validation before retrieval
 * - Automatic cleanup of expired tokens
 *
 * NOTE: Client-side storage is inherently less secure than httpOnly cookies.
 * This is a defense-in-depth measure, not a complete solution.
 */

import { authLogger } from '~/utils/logger'

// Storage keys
const TOKEN_KEY = 'token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user'
const TOKEN_EXPIRY_KEY = 'token_expiry'

// Configuration
interface StorageConfig {
  // Use sessionStorage instead of localStorage (more secure but tokens cleared on close)
  useSessionStorage: boolean
  // Automatically clear tokens after this many milliseconds of inactivity
  inactivityTimeout?: number
}

// Default config - can be overridden via setConfig
// Security Fix 2026-01-20: Use sessionStorage by default (tokens cleared on browser close)
// This prevents tokens from persisting if the user forgets to logout
let config: StorageConfig = {
  useSessionStorage: true, // Security: Use sessionStorage by default
  inactivityTimeout: undefined
}

// Get the appropriate storage backend
const getStorage = (): Storage => {
  return config.useSessionStorage ? sessionStorage : localStorage
}

// Activity tracking for inactivity timeout
let lastActivityTime = Date.now()
let inactivityCheckInterval: ReturnType<typeof setInterval> | null = null

/**
 * Configure storage behavior
 */
export const setStorageConfig = (newConfig: Partial<StorageConfig>): void => {
  config = { ...config, ...newConfig }

  // Setup inactivity timeout if configured
  if (config.inactivityTimeout && !inactivityCheckInterval) {
    setupInactivityCheck()
  }
}

/**
 * Record user activity (call on user interactions)
 */
export const recordActivity = (): void => {
  lastActivityTime = Date.now()
}

/**
 * Setup inactivity check
 */
const setupInactivityCheck = (): void => {
  if (typeof window === 'undefined') return

  // Check every minute
  inactivityCheckInterval = setInterval(() => {
    if (config.inactivityTimeout) {
      const inactiveFor = Date.now() - lastActivityTime
      if (inactiveFor > config.inactivityTimeout) {
        // Clear tokens due to inactivity
        clearTokens()
        authLogger.warn('Tokens cleared due to inactivity')
      }
    }
  }, 60000)

  // Track user activity
  const events = ['mousedown', 'keydown', 'scroll', 'touchstart']
  events.forEach(event => {
    window.addEventListener(event, recordActivity, { passive: true })
  })
}

/**
 * Store access token
 */
export const setAccessToken = (token: string, expiresInSeconds?: number): void => {
  const storage = getStorage()
  storage.setItem(TOKEN_KEY, token)

  // Store expiry time if provided
  if (expiresInSeconds) {
    const expiryTime = Date.now() + (expiresInSeconds * 1000)
    storage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString())
  }

  recordActivity()
}

/**
 * Get access token (returns null if expired)
 */
export const getAccessToken = (): string | null => {
  const storage = getStorage()
  const token = storage.getItem(TOKEN_KEY)

  if (!token) return null

  // Check if token is expired based on stored expiry
  const expiryStr = storage.getItem(TOKEN_EXPIRY_KEY)
  if (expiryStr) {
    const expiry = parseInt(expiryStr, 10)
    if (Date.now() > expiry) {
      // Token expired, clear it
      clearAccessToken()
      return null
    }
  }

  recordActivity()
  return token
}

/**
 * Clear access token
 */
export const clearAccessToken = (): void => {
  const storage = getStorage()
  storage.removeItem(TOKEN_KEY)
  storage.removeItem(TOKEN_EXPIRY_KEY)
}

/**
 * Store refresh token
 */
export const setRefreshToken = (token: string): void => {
  const storage = getStorage()
  storage.setItem(REFRESH_TOKEN_KEY, token)
  recordActivity()
}

/**
 * Get refresh token
 */
export const getRefreshToken = (): string | null => {
  const storage = getStorage()
  recordActivity()
  return storage.getItem(REFRESH_TOKEN_KEY)
}

/**
 * Clear refresh token
 */
export const clearRefreshToken = (): void => {
  const storage = getStorage()
  storage.removeItem(REFRESH_TOKEN_KEY)
}

/**
 * Store user data
 * WARNING: Do not store sensitive data in user object
 */
export const setUser = (user: Record<string, any>): void => {
  const storage = getStorage()

  // Sanitize user data - remove potentially sensitive fields
  const sanitizedUser = { ...user }
  delete sanitizedUser.password
  delete sanitizedUser.passwordHash
  delete sanitizedUser.secret
  delete sanitizedUser.apiKey

  storage.setItem(USER_KEY, JSON.stringify(sanitizedUser))
  recordActivity()
}

/**
 * Get user data
 */
export const getUser = (): Record<string, any> | null => {
  const storage = getStorage()
  const userStr = storage.getItem(USER_KEY)

  if (!userStr) return null

  try {
    recordActivity()
    return JSON.parse(userStr)
  } catch {
    // Invalid JSON, clear it
    storage.removeItem(USER_KEY)
    return null
  }
}

/**
 * Clear user data
 */
export const clearUser = (): void => {
  const storage = getStorage()
  storage.removeItem(USER_KEY)
}

/**
 * Clear all auth tokens and user data
 */
export const clearTokens = (): void => {
  clearAccessToken()
  clearRefreshToken()
  clearUser()
}

/**
 * Check if user is authenticated (has valid access token)
 */
export const isAuthenticated = (): boolean => {
  return getAccessToken() !== null
}

/**
 * Get all auth data at once
 */
export const getAuthData = (): {
  accessToken: string | null
  refreshToken: string | null
  user: Record<string, any> | null
} => {
  return {
    accessToken: getAccessToken(),
    refreshToken: getRefreshToken(),
    user: getUser()
  }
}

/**
 * Set all auth data at once
 */
export const setAuthData = (data: {
  accessToken: string
  refreshToken?: string
  user?: Record<string, any>
  expiresInSeconds?: number
}): void => {
  setAccessToken(data.accessToken, data.expiresInSeconds)

  if (data.refreshToken) {
    setRefreshToken(data.refreshToken)
  }

  if (data.user) {
    setUser(data.user)
  }
}

/**
 * Migrate from localStorage to sessionStorage
 * Call this to switch storage backend while preserving tokens
 */
export const migrateToSessionStorage = (): void => {
  if (config.useSessionStorage) return // Already using sessionStorage

  // Read from localStorage
  const accessToken = localStorage.getItem(TOKEN_KEY)
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  const user = localStorage.getItem(USER_KEY)
  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY)

  // Clear localStorage
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(TOKEN_EXPIRY_KEY)

  // Switch config
  config.useSessionStorage = true

  // Write to sessionStorage
  if (accessToken) sessionStorage.setItem(TOKEN_KEY, accessToken)
  if (refreshToken) sessionStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  if (user) sessionStorage.setItem(USER_KEY, user)
  if (expiry) sessionStorage.setItem(TOKEN_EXPIRY_KEY, expiry)
}

// Initialize activity tracking on load
if (typeof window !== 'undefined') {
  recordActivity()
}

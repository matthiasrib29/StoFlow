/**
 * Composable for JWT token validation and security
 *
 * Security improvements:
 * - Validates JWT structure before use
 * - Checks token expiration client-side
 * - Provides secure token cleanup
 */

interface JwtPayload {
  exp?: number
  iat?: number
  sub?: string
  user_id?: number
  [key: string]: unknown
}

export const useTokenValidator = () => {
  /**
   * Decode JWT payload without verification (client-side only)
   * Note: This does NOT verify the signature - that's done server-side
   */
  const decodeToken = (token: string): JwtPayload | null => {
    try {
      const parts = token.split('.')
      if (parts.length !== 3) {
        console.warn('[TokenValidator] Invalid JWT structure')
        return null
      }

      // Decode base64url payload
      const payload = parts[1]
      const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
      return JSON.parse(decoded)
    } catch (error) {
      console.warn('[TokenValidator] Failed to decode token:', error)
      return null
    }
  }

  /**
   * Check if token is expired
   * Adds a 30-second buffer to account for clock drift
   */
  const isTokenExpired = (token: string): boolean => {
    const payload = decodeToken(token)
    if (!payload || !payload.exp) {
      return true // Treat invalid tokens as expired
    }

    const now = Math.floor(Date.now() / 1000)
    const buffer = 30 // 30 seconds buffer
    return payload.exp < (now + buffer)
  }

  /**
   * Check if token will expire soon (within specified minutes)
   * Useful for proactive refresh
   */
  const willExpireSoon = (token: string, minutesThreshold: number = 5): boolean => {
    const payload = decodeToken(token)
    if (!payload || !payload.exp) {
      return true
    }

    const now = Math.floor(Date.now() / 1000)
    const threshold = minutesThreshold * 60
    return payload.exp < (now + threshold)
  }

  /**
   * Validate token structure and basic claims
   */
  const isValidToken = (token: string | null): boolean => {
    if (!token || typeof token !== 'string') {
      return false
    }

    // Check basic JWT structure (3 parts separated by dots)
    const parts = token.split('.')
    if (parts.length !== 3) {
      return false
    }

    // Check each part is valid base64url
    const base64urlRegex = /^[A-Za-z0-9_-]+$/
    for (const part of parts) {
      if (!base64urlRegex.test(part)) {
        return false
      }
    }

    // Decode and validate payload
    const payload = decodeToken(token)
    if (!payload) {
      return false
    }

    // Check required claims exist
    if (!payload.exp) {
      console.warn('[TokenValidator] Token missing exp claim')
      return false
    }

    return true
  }

  /**
   * Get token from localStorage with validation
   * Returns null if token is invalid or expired
   */
  const getValidToken = (key: string = 'token'): string | null => {
    if (!import.meta.client) {
      return null
    }

    const token = localStorage.getItem(key)

    if (!token) {
      return null
    }

    if (!isValidToken(token)) {
      console.warn(`[TokenValidator] Invalid token in localStorage (${key}), removing`)
      localStorage.removeItem(key)
      return null
    }

    if (isTokenExpired(token)) {
      console.warn(`[TokenValidator] Expired token in localStorage (${key}), removing`)
      localStorage.removeItem(key)
      return null
    }

    return token
  }

  /**
   * Get token payload
   */
  const getTokenPayload = (token: string): JwtPayload | null => {
    if (!isValidToken(token)) {
      return null
    }
    return decodeToken(token)
  }

  /**
   * Get remaining time until token expiration (in seconds)
   */
  const getTimeUntilExpiry = (token: string): number => {
    const payload = decodeToken(token)
    if (!payload || !payload.exp) {
      return 0
    }

    const now = Math.floor(Date.now() / 1000)
    return Math.max(0, payload.exp - now)
  }

  /**
   * Clean up all auth tokens from localStorage
   */
  const clearAllTokens = () => {
    if (!import.meta.client) return

    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  /**
   * Validate and clean expired tokens on app startup
   */
  const validateStoredTokens = (): { accessValid: boolean; refreshValid: boolean } => {
    if (!import.meta.client) {
      return { accessValid: false, refreshValid: false }
    }

    const accessToken = localStorage.getItem('token')
    const refreshToken = localStorage.getItem('refresh_token')

    const accessValid = accessToken ? isValidToken(accessToken) && !isTokenExpired(accessToken) : false
    // Refresh tokens typically have longer expiry, just validate structure
    const refreshValid = refreshToken ? isValidToken(refreshToken) : false

    // Clean up invalid access token
    if (accessToken && !accessValid) {
      console.log('[TokenValidator] Cleaning invalid/expired access token')
      localStorage.removeItem('token')
    }

    // Clean up invalid refresh token
    if (refreshToken && !refreshValid) {
      console.log('[TokenValidator] Cleaning invalid refresh token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    }

    return { accessValid, refreshValid }
  }

  return {
    decodeToken,
    isTokenExpired,
    willExpireSoon,
    isValidToken,
    getValidToken,
    getTokenPayload,
    getTimeUntilExpiry,
    clearAllTokens,
    validateStoredTokens
  }
}

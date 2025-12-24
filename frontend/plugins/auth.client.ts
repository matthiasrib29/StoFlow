/**
 * Plugin d'authentification (client-side only)
 *
 * Note: Session loading is now handled by auth.global.ts middleware
 * This plugin is kept for any future client-only auth initialization needs
 * but does NOT call loadFromStorage() to avoid duplicate calls
 */
import { authLogger } from '~/utils/logger'

export default defineNuxtPlugin(() => {
  // Note: loadFromStorage() is called by auth.global.ts middleware
  // Do NOT call it here to avoid duplicate token validation on every navigation

  if (import.meta.dev) {
    const authStore = useAuthStore()
    authLogger.debug('Auth plugin initialized', {
      authenticated: authStore.isAuthenticated
    })
  }
})

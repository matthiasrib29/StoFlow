/**
 * Client-side initialization plugin
 *
 * Handles client-only initialization tasks:
 * - Plugin sync: Initialize secure communication with browser extension
 * - Locale: Restore locale preferences
 *
 * Note: Auth session restoration is handled by auth.global.ts middleware
 * to avoid duplicate loadFromStorage() calls on every navigation
 */
import { initPluginListener } from '~/composables/usePluginSync'

export default defineNuxtPlugin(() => {
  const localeStore = useLocaleStore()

  // Initialize secure plugin communication listener
  // This allows the browser extension to announce itself and establish
  // a secure channel for token synchronization
  initPluginListener()

  // Restore locale preference from localStorage (defaults to French if not set)
  localeStore.initLocale()

  // Dev logging
  if (import.meta.dev) {
    const authStore = useAuthStore()
    console.log('[Init] Client initialized', {
      authenticated: authStore.isAuthenticated,
      locale: localeStore.currentLocale
    })
  }
})

/**
 * Client-side initialization plugin
 *
 * Handles client-only initialization tasks:
 * - Plugin detection: Initialize communication with browser extension (Firefox fallback)
 * - Locale: Restore locale preferences
 *
 * Note: Auth session restoration is handled by auth.global.ts middleware
 * to avoid duplicate loadFromStorage() calls on every navigation
 */
import { initPluginListener } from '~/composables/useVintedBridge'

export default defineNuxtPlugin(() => {
  const localeStore = useLocaleStore()

  // Initialize plugin communication listener (Firefox fallback)
  // This allows the browser extension to announce itself via postMessage
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

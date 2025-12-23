/**
 * Client-side initialization plugin
 *
 * Restores user session and preferences from localStorage on app startup
 * This plugin runs only on client-side (.client.ts suffix) because
 * localStorage is not available during server-side rendering (SSR)
 *
 * Combines functionality from:
 * - auth.client.ts: Restore authentication session
 * - locale.client.ts: Restore locale preferences
 * - Plugin sync: Initialize secure communication with browser extension
 */
import { initPluginListener } from '~/composables/usePluginSync'

export default defineNuxtPlugin(() => {
  const authStore = useAuthStore()
  const localeStore = useLocaleStore()

  // Initialize secure plugin communication listener
  // This allows the browser extension to announce itself and establish
  // a secure channel for token synchronization
  initPluginListener()

  // Restore authentication session from localStorage
  authStore.loadFromStorage()

  // Restore locale preference from localStorage (defaults to French if not set)
  localeStore.initLocale()

  // Dev logging
  if (import.meta.dev) {
    console.log('[Init] Client initialized', {
      authenticated: authStore.isAuthenticated,
      locale: localeStore.currentLocale
    })
  }
})

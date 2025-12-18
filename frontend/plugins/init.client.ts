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
 */
export default defineNuxtPlugin(() => {
  const authStore = useAuthStore()
  const localeStore = useLocaleStore()

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

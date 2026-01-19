/**
 * WebSocket Plugin - Global WebSocket initialization
 *
 * Automatically establishes WebSocket connection to backend when user is authenticated.
 * This enables real-time plugin command execution via backend.
 *
 * Author: Claude
 * Date: 2026-01-08
 * Updated: 2026-01-12 - Watch auth state to reconnect after login
 * Updated: 2026-01-19 - Fix: Prevent multiple watchers on app remount
 */

// Module-level flag to ensure watcher is only created once
let watcherInitialized = false

export default defineNuxtPlugin((nuxtApp) => {
  console.log('%c[WS Plugin] Initializing...', 'color: #f59e0b')

  // Run after app is mounted to ensure Vue context is available
  nuxtApp.hook('app:mounted', () => {
    // Prevent creating multiple watchers on hot-reload or remount
    if (watcherInitialized) {
      console.log('%c[WS Plugin] Watcher already initialized, skipping', 'color: #888')
      return
    }
    watcherInitialized = true

    console.log('%c[WS Plugin] App mounted, setting up auth watcher', 'color: #f59e0b')

    const authStore = useAuthStore()
    const { connect, disconnect, isConnected } = useWebSocket()

    console.log('%c[WS Plugin] Initial auth state:', 'color: #f59e0b', {
      isAuthenticated: authStore.isAuthenticated,
      userId: authStore.user?.id,
      isWsConnected: isConnected.value
    })

    // Watch auth state and connect/disconnect accordingly
    watch(
      () => authStore.isAuthenticated,
      (isAuthenticated, oldValue) => {
        console.log('%c[WS Plugin] Auth state changed:', 'color: #f59e0b', {
          from: oldValue,
          to: isAuthenticated,
          isWsConnected: isConnected.value
        })

        if (isAuthenticated && !isConnected.value) {
          console.log('%c[WS Plugin] → Triggering connect()', 'color: #22c55e; font-weight: bold')
          connect()
        } else if (!isAuthenticated && isConnected.value) {
          console.log('%c[WS Plugin] → Triggering disconnect()', 'color: #ef4444; font-weight: bold')
          disconnect()
        } else {
          console.log('%c[WS Plugin] → No action needed', 'color: #888')
        }
      },
      { immediate: true }
    )

    console.log('%c[WS Plugin] ✓ Initialized', 'color: #22c55e; font-weight: bold')
  })
})

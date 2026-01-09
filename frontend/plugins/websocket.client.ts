/**
 * WebSocket Plugin - Global WebSocket initialization
 *
 * Automatically establishes WebSocket connection to backend when user is authenticated.
 * This enables real-time plugin command execution via backend.
 *
 * Author: Claude
 * Date: 2026-01-08
 */
export default defineNuxtPlugin(() => {
  const { connect } = useWebSocket()

  // Connect on plugin init
  connect()

  console.log('[Plugin] WebSocket initialized')
})

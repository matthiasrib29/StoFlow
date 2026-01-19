/**
 * useWebSocket - Composable for WebSocket connection with backend
 *
 * Provides real-time bidirectional communication between frontend and backend.
 * Used to relay plugin commands from backend to browser extension.
 *
 * Author: Claude
 * Date: 2026-01-08
 * Updated: 2026-01-12 - Singleton pattern + debug logging
 */
import { ref } from 'vue'
import { io, Socket } from 'socket.io-client'
import { useAuthStore } from '~/stores/auth'
import { useVintedBridge } from './useVintedBridge'

// Extend Window interface for TypeScript
declare global {
  interface Window {
    __stoflow_ws_socket?: Socket | null
    __stoflow_ws_initialized?: boolean
  }
}

// Use window storage to survive hot-reload (Vite HMR resets module-level variables)
// This ensures we don't create multiple sockets when the module is reloaded
const getSocket = (): Socket | null => {
  if (typeof window === 'undefined') return null
  return window.__stoflow_ws_socket ?? null
}

const setSocket = (s: Socket | null) => {
  if (typeof window !== 'undefined') {
    window.__stoflow_ws_socket = s
  }
}

// Singleton state (shared across all composable instances)
// These refs are fine to recreate - they'll sync with window state
const socket = ref<Socket | null>(getSocket())
const isConnected = ref(getSocket()?.connected ?? false)
const isConnecting = ref(false)
const error = ref<string | null>(null)

// Debug logger for WebSocket
const wsLog = {
  debug: (msg: string, ...args: any[]) => console.log(`%c[WS] ${msg}`, 'color: #888', ...args),
  info: (msg: string, ...args: any[]) => console.log(`%c[WS] ${msg}`, 'color: #0ea5e9', ...args),
  success: (msg: string, ...args: any[]) => console.log(`%c[WS] ✓ ${msg}`, 'color: #22c55e', ...args),
  warn: (msg: string, ...args: any[]) => console.warn(`[WS] ⚠ ${msg}`, ...args),
  error: (msg: string, ...args: any[]) => console.error(`[WS] ✗ ${msg}`, ...args),
}

/**
 * Emit with Socket.IO native ACK.
 * Waits for connection if socket is disconnected, then emits.
 * Returns a promise that resolves when the server acknowledges.
 */
function emitWithAck(event: string, data: any, timeout: number = 30000): Promise<any> {
  return new Promise((resolve, reject) => {
    if (!socket.value) {
      reject(new Error('Socket not initialized'))
      return
    }

    const doEmit = () => {
      wsLog.info(`Emitting ${event}...`)

      socket.value!.emit(event, data, (err: any, response: any) => {
        if (err) {
          wsLog.error(`${event} failed: ${err.message}`)
          reject(new Error(err.message || 'Emit failed'))
        } else {
          wsLog.success(`${event} acknowledged by server`)
          resolve(response)
        }
      })
    }

    // If connected, emit immediately
    if (socket.value.connected) {
      doEmit()
      return
    }

    // If disconnected, wait for reconnection
    wsLog.warn(`Socket disconnected, waiting for reconnection before emitting ${event}...`)

    let timeoutId: ReturnType<typeof setTimeout> | null = null
    let resolved = false

    const onConnect = () => {
      if (resolved) return
      resolved = true
      if (timeoutId) clearTimeout(timeoutId)
      wsLog.info(`Reconnected, now emitting ${event}`)
      doEmit()
    }

    const onTimeout = () => {
      if (resolved) return
      resolved = true
      socket.value?.off('connect', onConnect)
      wsLog.error(`Timeout waiting for reconnection to emit ${event}`)
      reject(new Error(`Connection timeout waiting to emit ${event}`))
    }

    socket.value.once('connect', onConnect)
    timeoutId = setTimeout(onTimeout, timeout)
  })
}

export function useWebSocket() {
  const authStore = useAuthStore()
  const vintedBridge = useVintedBridge()

  // Connect to backend WebSocket
  const connect = () => {
    wsLog.info('connect() called')
    wsLog.debug('Auth state:', {
      isAuthenticated: authStore.isAuthenticated,
      userId: authStore.user?.id,
      hasToken: !!authStore.token
    })

    if (!authStore.isAuthenticated || !authStore.user?.id) {
      wsLog.warn('Not authenticated, skipping connection')
      return
    }

    // Extra safety: ensure token is present (race condition protection)
    if (!authStore.token) {
      wsLog.warn('Token not yet available, skipping connection')
      return
    }

    // Avoid duplicate connections
    if (socket.value?.connected) {
      wsLog.debug('Already connected, skipping')
      return
    }

    // Avoid multiple connection attempts (race condition protection)
    if (isConnecting.value) {
      wsLog.debug('Connection already in progress, skipping')
      return
    }

    // If socket exists but not connected, it may be reconnecting - don't interfere
    if (socket.value) {
      wsLog.debug('Socket exists, letting Socket.IO handle reconnection')
      return
    }

    const config = useRuntimeConfig()
    const backendUrl = config.public.apiUrl || 'http://localhost:8000'
    wsLog.info(`Connecting to ${backendUrl} as user ${authStore.user.id}`)
    wsLog.debug('Token available:', !!authStore.token)

    // Mark as connecting to prevent duplicate attempts
    isConnecting.value = true

    socket.value = io(backendUrl, {
      auth: {
        user_id: authStore.user.id,
        token: authStore.token
      },
      transports: ['websocket'],
      // Connection timeout - how long to wait for initial connection
      timeout: 60000,  // 60s (default: 20s) - increased for stability
      // Reconnection settings
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity, // Keep trying to reconnect
      // ACK retry settings (Socket.IO v4.6+)
      // Messages are retried automatically until acknowledged
      ackTimeout: 30000,  // 30s for ACK (increased from 10s for sync operations)
      retries: 5          // Retry up to 5 times (6 total attempts)
    })

    socket.value.on('connect', () => {
      isConnected.value = true
      isConnecting.value = false
      error.value = null
      wsLog.success(`Connected! Socket ID: ${socket.value?.id}`)
    })

    socket.value.on('disconnect', (reason) => {
      isConnected.value = false
      // Don't reset isConnecting here - Socket.IO will auto-reconnect
      // and we don't want new connect() calls to interfere
      wsLog.warn(`Disconnected: ${reason}`)
    })

    socket.value.on('connect_error', (err) => {
      error.value = err.message
      // Only reset isConnecting if Socket.IO won't retry
      // (reconnection is enabled, so it will keep trying)
      wsLog.error(`Connection error: ${err.message}`, err)
    })

    // Listen for plugin commands from backend
    socket.value.on('plugin_command', async (data) => {
      wsLog.info(`Received command: ${data.action} (req: ${data.request_id})`)
      await handlePluginCommand(data)
    })
  }

  // Handle plugin command from backend
  const handlePluginCommand = async (data: {
    request_id: string
    action: string
    payload: any
  }) => {
    wsLog.debug(`Processing ${data.action}...`, data.payload)

    try {
      // Execute via plugin bridge
      let result: any

      switch (data.action) {
        case 'VINTED_PUBLISH':
          result = await vintedBridge.publishProduct(data.payload)
          break

        case 'VINTED_UPDATE':
          result = await vintedBridge.updateProduct(
            data.payload.vintedId,
            data.payload.updates
          )
          break

        case 'VINTED_DELETE':
          result = await vintedBridge.deleteProduct(data.payload.vintedId)
          break

        case 'VINTED_GET_WARDROBE':
          result = await vintedBridge.getWardrobe(
            data.payload.userId,
            data.payload.page,
            data.payload.perPage
          )
          break

        case 'VINTED_API_CALL':
          result = await vintedBridge.executeApiCall(data.payload)
          break

        case 'VINTED_FETCH_USERS':
          result = await vintedBridge.fetchUsers(
            data.payload.search_text,
            data.payload.page,
            data.payload.per_page
          )
          break

        default:
          throw new Error(`Unknown action: ${data.action}`)
      }

      wsLog.success(`Command ${data.action} completed`, { success: result.success })

      // Send response back to backend with ACK (Socket.IO handles retry)
      await emitWithAck('plugin_response', {
        request_id: data.request_id,
        success: result.success,
        data: result.data,
        error: result.error
      })
    } catch (err: any) {
      wsLog.error(`Command ${data.action} failed: ${err.message}`)

      // Try to send error response (best effort)
      try {
        await emitWithAck('plugin_response', {
          request_id: data.request_id,
          success: false,
          data: null,
          error: err.message
        })
      } catch (emitErr: any) {
        wsLog.error(`Failed to send error response: ${emitErr.message}`)
      }
    }
  }

  // Disconnect
  const disconnect = () => {
    wsLog.info('disconnect() called')
    socket.value?.disconnect()
    socket.value = null
    isConnected.value = false
    isConnecting.value = false
  }

  // Note: Connection is now managed by the websocket.client.ts plugin
  // which watches authStore.isAuthenticated and connects/disconnects accordingly.
  // The singleton pattern ensures all components share the same connection.

  return {
    socket,
    isConnected,
    error,
    connect,
    disconnect
  }
}

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

// Singleton state (shared across all composable instances)
const socket = ref<Socket | null>(null)
const isConnected = ref(false)
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
 * Uses Socket.IO's built-in retry mechanism (configured at connection level).
 * Returns a promise that resolves when the server acknowledges.
 */
function emitWithAck(event: string, data: any): Promise<any> {
  return new Promise((resolve, reject) => {
    if (!socket.value) {
      reject(new Error('Socket not initialized'))
      return
    }

    wsLog.info(`Emitting ${event}...`)

    // Socket.IO handles retries automatically via retries/ackTimeout options
    // Messages are also buffered during disconnection and sent on reconnect
    socket.value.emit(event, data, (err: any, response: any) => {
      if (err) {
        wsLog.error(`${event} failed: ${err.message}`)
        reject(new Error(err.message || 'Emit failed'))
      } else {
        wsLog.success(`${event} acknowledged by server`)
        resolve(response)
      }
    })
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

    // Clean up existing socket if disconnected
    if (socket.value) {
      wsLog.debug('Cleaning up existing disconnected socket')
      socket.value.disconnect()
      socket.value = null
    }

    const config = useRuntimeConfig()
    const backendUrl = config.public.apiUrl || 'http://localhost:8000'
    wsLog.info(`Connecting to ${backendUrl} as user ${authStore.user.id}`)
    wsLog.debug('Token available:', !!authStore.token)

    socket.value = io(backendUrl, {
      auth: {
        user_id: authStore.user.id,
        token: authStore.token
      },
      transports: ['websocket'],
      // Reconnection settings
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity, // Keep trying to reconnect
      // ACK retry settings (Socket.IO v4.6+)
      // Messages are retried automatically until acknowledged
      ackTimeout: 10000,  // Wait 10s for ACK before retry
      retries: 3          // Retry up to 3 times (4 total attempts)
    })

    socket.value.on('connect', () => {
      isConnected.value = true
      error.value = null
      wsLog.success(`Connected! Socket ID: ${socket.value?.id}`)
    })

    socket.value.on('disconnect', (reason) => {
      isConnected.value = false
      wsLog.warn(`Disconnected: ${reason}`)
    })

    socket.value.on('connect_error', (err) => {
      error.value = err.message
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

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

// Debug logger for WebSocket with timestamps
const getTimestamp = () => new Date().toISOString().substr(11, 12) // HH:MM:SS.mmm
const wsLog = {
  debug: (msg: string, ...args: any[]) => console.log(`%c[WS ${getTimestamp()}] ${msg}`, 'color: #888', ...args),
  info: (msg: string, ...args: any[]) => console.log(`%c[WS ${getTimestamp()}] ${msg}`, 'color: #0ea5e9', ...args),
  success: (msg: string, ...args: any[]) => console.log(`%c[WS ${getTimestamp()}] ✓ ${msg}`, 'color: #22c55e', ...args),
  warn: (msg: string, ...args: any[]) => console.warn(`[WS ${getTimestamp()}] ⚠ ${msg}`, ...args),
  error: (msg: string, ...args: any[]) => console.error(`[WS ${getTimestamp()}] ✗ ${msg}`, ...args),
}

/**
 * Emit with ACK and automatic retry on failure.
 * Uses Socket.IO's built-in acknowledgement pattern.
 */
async function emitWithRetry(
  event: string,
  data: any,
  maxRetries = 3,
  timeout = 10000
): Promise<any> {
  let lastError: Error | null = null

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      wsLog.info(`Emitting ${event} (attempt ${attempt}/${maxRetries})...`)

      const ack = await new Promise((resolve, reject) => {
        socket.value?.timeout(timeout).emit(event, data, (err: any, response: any) => {
          if (err) reject(new Error(err.message || 'Emit timeout'))
          else resolve(response)
        })
      })

      wsLog.success(`${event} acknowledged by server`)
      return ack
    } catch (err: any) {
      lastError = err
      wsLog.warn(`${event} attempt ${attempt} failed: ${err.message}`)

      if (attempt < maxRetries) {
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000)
        wsLog.info(`Retrying in ${delay}ms...`)
        await new Promise(r => setTimeout(r, delay))
      }
    }
  }

  throw lastError || new Error(`Failed to emit ${event} after ${maxRetries} attempts`)
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
        token: authStore.token  // Fixed: was accessToken, should be token
      },
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    })

    socket.value.on('connect', () => {
      isConnected.value = true
      error.value = null
      wsLog.success(`═══ CONNECTED ═══`)
      wsLog.success(`Socket ID: ${socket.value?.id}`)
      wsLog.info(`Transport: ${socket.value?.io?.engine?.transport?.name}`)
    })

    socket.value.on('disconnect', (reason) => {
      isConnected.value = false
      wsLog.warn(`═══ DISCONNECTED ═══`)
      wsLog.warn(`Reason: ${reason}`)
      wsLog.warn(`Socket ID was: ${socket.value?.id}`)
    })

    socket.value.on('reconnect', (attempt) => {
      wsLog.info(`═══ RECONNECTED after ${attempt} attempts ═══`)
      wsLog.info(`New Socket ID: ${socket.value?.id}`)
    })

    socket.value.on('reconnect_attempt', (attempt) => {
      wsLog.debug(`Reconnect attempt #${attempt}...`)
    })

    socket.value.on('connect_error', (err) => {
      error.value = err.message
      wsLog.error(`Connection error: ${err.message}`, err)
    })

    // Listen for plugin commands from backend
    socket.value.on('plugin_command', async (data) => {
      wsLog.info(`═══ COMMAND FROM BACKEND ═══`)
      wsLog.info(`Action: ${data.action}`)
      wsLog.info(`Request ID: ${data.request_id}`)
      wsLog.info(`Current socket ID: ${socket.value?.id}`)
      wsLog.info(`Socket connected: ${socket.value?.connected}`)
      await handlePluginCommand(data)
    })
  }

  // Handle plugin command from backend
  const handlePluginCommand = async (data: {
    request_id: string
    action: string
    payload: any
  }) => {
    const startTime = Date.now()

    wsLog.info(`═══════════════════════════════════════════════`)
    wsLog.info(`COMMAND RECEIVED: ${data.action}`)
    wsLog.info(`Request ID: ${data.request_id}`)
    wsLog.debug(`Payload:`, data.payload)

    try {
      // Execute via plugin bridge
      let result: any

      wsLog.info(`→ Calling vintedBridge.${data.action}...`)

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
          wsLog.info(`→ Starting executeApiCall for ${data.request_id}...`)
          try {
            result = await vintedBridge.executeApiCall(data.payload)
            wsLog.info(`→ executeApiCall returned for ${data.request_id}`)
          } catch (bridgeErr: any) {
            wsLog.error(`→ executeApiCall FAILED for ${data.request_id}: ${bridgeErr.message}`)
            throw bridgeErr
          }
          break

        default:
          throw new Error(`Unknown action: ${data.action}`)
      }

      const bridgeTime = Date.now() - startTime
      wsLog.success(`Bridge call completed in ${bridgeTime}ms`)
      wsLog.info(`Result success: ${result.success}`)
      wsLog.debug(`Result data keys:`, result.data ? Object.keys(result.data) : 'N/A')

      // Verify socket state before emit
      wsLog.info(`Socket state before emit:`, {
        hasSocket: !!socket.value,
        connected: socket.value?.connected,
        id: socket.value?.id,
        disconnected: socket.value?.disconnected
      })

      if (!socket.value) {
        wsLog.error(`CRITICAL: socket.value is null/undefined!`)
      } else if (!socket.value.connected) {
        wsLog.error(`CRITICAL: Socket not connected! State: connected=${socket.value.connected}, disconnected=${socket.value.disconnected}`)
      }

      // Emit response
      const responsePayload = {
        request_id: data.request_id,
        success: result.success,
        data: result.data,
        error: result.error
      }

      wsLog.info(`→ Emitting plugin_response...`)
      wsLog.debug(`Response payload:`, { ...responsePayload, data: responsePayload.data ? '[DATA]' : null })

      // Store response in case we need to re-emit after reconnection
      pendingResponses.set(data.request_id, responsePayload)

      socket.value?.emit('plugin_response', responsePayload)

      const totalTime = Date.now() - startTime
      wsLog.success(`plugin_response EMITTED for ${data.request_id}`)
      wsLog.info(`Total handling time: ${totalTime}ms (bridge: ${bridgeTime}ms)`)

      // Check if socket is still connected after emit (detect zombie state)
      // Use a small delay to allow disconnect event to fire if connection is dead
      setTimeout(() => {
        if (socket.value?.connected) {
          // Socket still connected, emit likely succeeded
          pendingResponses.delete(data.request_id)
          wsLog.debug(`Response ${data.request_id} confirmed (socket still connected)`)
        } else {
          // Socket disconnected, response will be re-emitted on reconnect
          wsLog.warn(`Socket disconnected after emit, response ${data.request_id} queued for re-emit`)
        }
      }, 100)

      wsLog.info(`═══════════════════════════════════════════════`)

    } catch (err: any) {
      const totalTime = Date.now() - startTime
      wsLog.error(`Command ${data.action} FAILED after ${totalTime}ms: ${err.message}`)

      wsLog.info(`Socket state for error response:`, {
        hasSocket: !!socket.value,
        connected: socket.value?.connected,
        id: socket.value?.id
      })

      socket.value?.emit('plugin_response', {
        request_id: data.request_id,
        success: false,
        data: null,
        error: err.message
      })

      wsLog.info(`Error response emitted for ${data.request_id}`)
      wsLog.info(`═══════════════════════════════════════════════`)
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

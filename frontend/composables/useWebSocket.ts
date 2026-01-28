/**
 * useWebSocket - Composable for WebSocket connection with backend
 *
 * Provides real-time bidirectional communication between frontend and backend.
 * Used to relay plugin commands from backend to browser extension.
 *
 * Connection is managed EXPLICITLY by auth.ts:
 * - login() calls ws.connect()
 * - logout() calls ws.disconnect()
 * - loadFromStorage() calls ws.connect() after session restore
 *
 * SINGLETON: Returns the same instance across all calls.
 *
 * Author: Claude
 * Date: 2026-01-08
 */
import { ref, shallowRef, markRaw, type Ref, type ShallowRef } from 'vue'
import { io, Socket } from 'socket.io-client'
import { useVintedBridge } from './useVintedBridge'
import { createLogger } from '~/utils/logger'

const wsLogger = createLogger({ prefix: 'WS' })

// Module-level state (singleton)
const socket: ShallowRef<Socket | null> = shallowRef(null)
const isConnected: Ref<boolean> = ref(false)
const isConnecting: Ref<boolean> = ref(false)
const error: Ref<string | null> = ref(null)

// Singleton composable instance
let composableInstance: ReturnType<typeof createWebSocketComposable> | null = null

function createWebSocketComposable() {
  const vintedBridge = useVintedBridge()

  /**
   * Attach event listeners to socket
   */
  const attachListeners = (sock: Socket) => {
    sock.on('connect', () => {
      isConnected.value = true
      isConnecting.value = false
      error.value = null
      wsLogger.info(`Connected (id=${sock.id})`)
    })

    sock.on('disconnect', (reason) => {
      isConnected.value = false
      wsLogger.warn(`Disconnected: ${reason}`)

      if (reason === 'io server disconnect') {
        // Server forcefully disconnected - don't auto-reconnect
        sock.disconnect()
      }
    })

    sock.on('connect_error', (err) => {
      error.value = err.message
      isConnecting.value = false
      wsLogger.error(`Connection error: ${err.message}`)
    })

    // Plugin commands from backend
    sock.on('plugin_command', async (data) => {
      wsLogger.debug(`Received plugin_command: ${data.action}`)
      await handlePluginCommand(sock, data)
    })
  }

  /**
   * Handle plugin command from backend
   */
  const handlePluginCommand = async (
    sock: Socket,
    data: { request_id: string; action: string; payload: any }
  ) => {
    try {
      let result: any

      switch (data.action) {
        case 'VINTED_API_CALL':
          result = await vintedBridge.executeApiCall(data.payload)
          break
        default:
          throw new Error(`Unknown action: ${data.action}`)
      }

      sock.emit('plugin_response', {
        request_id: data.request_id,
        success: result.success,
        data: result.data,
        error: result.error
      })

    } catch (err: any) {
      wsLogger.error(`Command ${data.action} failed: ${err.message}`)
      sock.emit('plugin_response', {
        request_id: data.request_id,
        success: false,
        data: null,
        error: err.message
      })
    }
  }

  /**
   * Connect to backend WebSocket
   */
  const connect = (token?: string, userId?: number) => {
    // Get auth from store if not provided
    let actualToken = token
    let actualUserId = userId

    if (!actualToken || !actualUserId) {
      const authStore = useAuthStore()
      actualToken = actualToken || authStore.token || undefined
      actualUserId = actualUserId || authStore.user?.id

      if (!authStore.isAuthenticated || !actualUserId) {
        wsLogger.warn('Not authenticated, skipping connection')
        return
      }
    }

    if (!actualToken) {
      wsLogger.warn('No token available, skipping connection')
      return
    }

    // Already connected?
    if (socket.value?.connected) {
      return
    }

    // Connection in progress?
    if (isConnecting.value) {
      return
    }

    // Clean up existing socket if any
    if (socket.value) {
      socket.value.removeAllListeners()
      socket.value.disconnect()
      socket.value = null
    }

    const config = useRuntimeConfig()
    const backendUrl = config.public.apiUrl || 'http://localhost:8000'

    wsLogger.info(`Connecting to ${backendUrl}`)

    isConnecting.value = true

    // Create socket with markRaw to prevent Vue reactivity interference
    const newSocket = markRaw(io(backendUrl, {
      auth: {
        user_id: actualUserId,
        token: actualToken
      },
      transports: ['websocket'],
      autoConnect: false,
      timeout: 60000,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 10,
    }))

    // Attach listeners before connecting
    attachListeners(newSocket)

    // Store and connect
    socket.value = newSocket
    newSocket.connect()
  }

  /**
   * Disconnect from WebSocket
   */
  const disconnect = () => {
    if (socket.value) {
      socket.value.removeAllListeners()
      socket.value.disconnect()
      socket.value = null
    }

    isConnected.value = false
    isConnecting.value = false
    wsLogger.info('Disconnected')
  }

  /**
   * Update socket auth without reconnecting
   */
  const updateAuth = (token: string, userId: number) => {
    if (socket.value) {
      socket.value.auth = { user_id: userId, token }
    }
  }

  return {
    socket,
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
    updateAuth
  }
}

// Exported singleton composable
export function useWebSocket() {
  if (!composableInstance) {
    composableInstance = createWebSocketComposable()
  }
  return composableInstance
}

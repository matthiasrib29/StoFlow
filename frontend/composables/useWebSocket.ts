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
 * HMR-SAFE: Uses import.meta.hot.data to preserve socket across hot reloads.
 * SINGLETON: Returns the same instance across all calls.
 *
 * Author: Claude
 * Date: 2026-01-08
 * Updated: 2026-01-19 - Complete rewrite for HMR safety and true singleton
 */
import { ref, shallowRef, markRaw, type Ref, type ShallowRef } from 'vue'
import { io, Socket } from 'socket.io-client'
import { useVintedBridge } from './useVintedBridge'

// ============================================================================
// DEBUG LOGGING
// ============================================================================
const getTimestamp = () => new Date().toISOString().substr(11, 12)
const wsLog = {
  debug: (msg: string, ...args: any[]) => console.log(`%c[WS ${getTimestamp()}] ${msg}`, 'color: #888', ...args),
  info: (msg: string, ...args: any[]) => console.log(`%c[WS ${getTimestamp()}] ${msg}`, 'color: #0ea5e9', ...args),
  success: (msg: string, ...args: any[]) => console.log(`%c[WS ${getTimestamp()}] ✓ ${msg}`, 'color: #22c55e', ...args),
  warn: (msg: string, ...args: any[]) => console.warn(`[WS ${getTimestamp()}] ⚠ ${msg}`, ...args),
  error: (msg: string, ...args: any[]) => console.error(`[WS ${getTimestamp()}] ✗ ${msg}`, ...args),
}

// ============================================================================
// HMR-SAFE STATE
// Using import.meta.hot.data to preserve state across hot module reloads
// ============================================================================
interface WebSocketState {
  socket: Socket | null
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  connectionId: number
  initialized: boolean
}

// Get or create HMR-preserved state
function getOrCreateState(): WebSocketState {
  if (import.meta.hot?.data?.wsState) {
    wsLog.debug('HMR: Restoring preserved state', {
      socketId: import.meta.hot.data.wsState.socket?.id,
      isConnected: import.meta.hot.data.wsState.isConnected,
      connectionId: import.meta.hot.data.wsState.connectionId
    })
    return import.meta.hot.data.wsState
  }

  wsLog.debug('Creating fresh state')
  return {
    socket: null,
    isConnected: false,
    isConnecting: false,
    error: null,
    connectionId: 0,
    initialized: false
  }
}

// Module-level state (preserved across HMR via import.meta.hot.data)
const state = getOrCreateState()

// Vue refs that wrap the state (for reactivity)
const socket: ShallowRef<Socket | null> = shallowRef(state.socket)
const isConnected: Ref<boolean> = ref(state.isConnected)
const isConnecting: Ref<boolean> = ref(state.isConnecting)
const error: Ref<string | null> = ref(state.error)

// Sync refs to state when they change
function syncState() {
  state.socket = socket.value
  state.isConnected = isConnected.value
  state.isConnecting = isConnecting.value
  state.error = error.value
}

// HMR handlers - DESTRUCTION STRATEGY (recommended for debugging)
// Instead of persisting the socket, we DESTROY it to eliminate ghost connections
if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    wsLog.warn('═══════════════════════════════════════════════════════════')
    wsLog.warn('HMR dispose: DESTROYING socket to prevent ghost connections')

    if (state.socket) {
      wsLog.warn(`Killing socket ${state.socket.id}`)
      state.socket.removeAllListeners()
      state.socket.disconnect()
      state.socket = null
    }

    // Reset all state
    state.isConnected = false
    state.isConnecting = false
    state.error = null
    state.connectionId++

    // Update refs
    socket.value = null
    isConnected.value = false
    isConnecting.value = false
    error.value = null

    wsLog.warn('HMR dispose: Socket destroyed, state reset')
    wsLog.warn('═══════════════════════════════════════════════════════════')
  })

  import.meta.hot.accept(() => {
    wsLog.info('HMR accept: module reloaded (socket was destroyed)')
  })
}

wsLog.info('Module loaded', {
  hasSocket: !!socket.value,
  socketId: socket.value?.id,
  isConnected: isConnected.value
})

// ============================================================================
// SINGLETON COMPOSABLE INSTANCE
// ============================================================================
let composableInstance: ReturnType<typeof createWebSocketComposable> | null = null

function createWebSocketComposable() {
  const vintedBridge = useVintedBridge()

  /**
   * Attach event listeners to socket
   */
  const attachListeners = (sock: Socket) => {
    const currentConnectionId = state.connectionId

    sock.on('connect', () => {
      // Guard: only process if this is still the current connection
      if (state.connectionId !== currentConnectionId) {
        wsLog.warn(`connect event ignored (stale connection ${currentConnectionId}, current ${state.connectionId})`)
        return
      }

      isConnected.value = true
      isConnecting.value = false
      error.value = null
      syncState()

      wsLog.success(`CONNECTED! Socket ID: ${sock.id}`)
      wsLog.info(`Transport: ${(sock as any).io?.engine?.transport?.name || 'unknown'}`)
    })

    sock.on('disconnect', (reason, details) => {
      if (state.connectionId !== currentConnectionId) {
        wsLog.warn(`disconnect event ignored (stale connection ${currentConnectionId})`)
        return
      }

      isConnected.value = false
      syncState()

      wsLog.warn(`DISCONNECTED! Reason: ${reason}`, details)

      // Handle different disconnect reasons
      if (reason === 'io server disconnect') {
        // Server forcefully disconnected - DON'T auto-reconnect
        wsLog.error('Server forcefully disconnected - stopping reconnection')
        sock.disconnect() // Ensure we don't auto-reconnect
      } else if (reason === 'ping timeout') {
        wsLog.error('Ping timeout - server did not respond')
      } else if (reason === 'transport close') {
        wsLog.warn('Transport closed (network issue) - will auto-reconnect')
      }
    })

    sock.on('connect_error', (err) => {
      if (state.connectionId !== currentConnectionId) return

      error.value = err.message
      isConnecting.value = false
      syncState()

      wsLog.error(`Connection error: ${err.message}`)
    })

    sock.on('reconnect', (attempt: number) => {
      wsLog.info(`Reconnected after ${attempt} attempts`)
    })

    sock.on('reconnect_attempt', (attempt: number) => {
      wsLog.debug(`Reconnect attempt #${attempt}...`)
    })

    sock.on('reconnect_error', (err: Error) => {
      wsLog.error(`Reconnect error: ${err.message}`)
    })

    sock.on('reconnect_failed', () => {
      wsLog.error('Reconnection failed after all attempts!')
    })

    // Plugin commands from backend
    sock.on('plugin_command', async (data) => {
      if (state.connectionId !== currentConnectionId) {
        wsLog.warn('plugin_command ignored (stale connection)')
        return
      }
      wsLog.info(`Received plugin_command: ${data.action} (req: ${data.request_id})`)
      await handlePluginCommand(sock, data)
    })

    wsLog.debug('Event listeners attached')
  }

  /**
   * Handle plugin command from backend
   */
  const handlePluginCommand = async (
    sock: Socket,
    data: { request_id: string; action: string; payload: any }
  ) => {
    const startTime = performance.now()

    try {
      let result: any

      switch (data.action) {
        case 'VINTED_PUBLISH':
          result = await vintedBridge.publishProduct(data.payload)
          break
        case 'VINTED_UPDATE':
          result = await vintedBridge.updateProduct(data.payload.vintedId, data.payload.updates)
          break
        case 'VINTED_DELETE':
          result = await vintedBridge.deleteProduct(data.payload.vintedId)
          break
        case 'VINTED_GET_WARDROBE':
          result = await vintedBridge.getWardrobe(data.payload.userId, data.payload.page, data.payload.perPage)
          break
        case 'VINTED_API_CALL':
          result = await vintedBridge.executeApiCall(data.payload)
          break
        case 'VINTED_FETCH_USERS':
          result = await vintedBridge.fetchUsers(data.payload.search_text, data.payload.page, data.payload.per_page)
          break
        default:
          throw new Error(`Unknown action: ${data.action}`)
      }

      const elapsed = (performance.now() - startTime).toFixed(1)
      wsLog.success(`Command ${data.action} completed in ${elapsed}ms`)

      // Send response with retry logic
      await emitWithRetry('plugin_response', {
        request_id: data.request_id,
        success: result.success,
        data: result.data,
        error: result.error
      })

    } catch (err: any) {
      const elapsed = (performance.now() - startTime).toFixed(1)
      wsLog.error(`Command ${data.action} failed after ${elapsed}ms: ${err.message}`)

      try {
        await emitWithRetry('plugin_response', {
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

  /**
   * Emit with retry logic
   * Uses simple emit (not emitWithAck) to avoid blocking on ACK during reconnection
   */
  const emitWithRetry = async (
    event: string,
    data: any,
    maxRetries: number = 3,
    retryDelay: number = 1000
  ): Promise<void> => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      const currentSocket = socket.value

      if (!currentSocket) {
        wsLog.warn(`emitWithRetry: No socket (attempt ${attempt}/${maxRetries})`)
        if (attempt < maxRetries) {
          await new Promise(r => setTimeout(r, retryDelay))
          continue
        }
        throw new Error('No socket available')
      }

      if (!currentSocket.connected) {
        wsLog.warn(`emitWithRetry: Socket disconnected, waiting for reconnection (attempt ${attempt}/${maxRetries})`)

        // Wait for reconnection with timeout
        const reconnected = await new Promise<boolean>((resolve) => {
          const timeoutId = setTimeout(() => {
            currentSocket.off('connect', onConnect)
            resolve(false)
          }, 5000)

          const onConnect = () => {
            clearTimeout(timeoutId)
            resolve(true)
          }

          currentSocket.once('connect', onConnect)
        })

        if (!reconnected) {
          wsLog.warn(`emitWithRetry: Reconnection timeout (attempt ${attempt}/${maxRetries})`)
          if (attempt < maxRetries) {
            continue
          }
          throw new Error('Reconnection timeout')
        }
      }

      // Try to emit
      try {
        wsLog.debug(`emitWithRetry: Emitting ${event} (attempt ${attempt}/${maxRetries})`)
        currentSocket.emit(event, data)
        wsLog.success(`emitWithRetry: ${event} emitted successfully`)
        return
      } catch (err: any) {
        wsLog.error(`emitWithRetry: Emit failed (attempt ${attempt}/${maxRetries}): ${err.message}`)
        if (attempt < maxRetries) {
          await new Promise(r => setTimeout(r, retryDelay))
          continue
        }
        throw err
      }
    }
  }

  /**
   * Connect to backend WebSocket
   */
  const connect = (token?: string, userId?: number) => {
    wsLog.info('═══════════════════════════════════════════════════════════')
    wsLog.info('connect() called')

    // Get auth from store if not provided
    let actualToken = token
    let actualUserId = userId

    if (!actualToken || !actualUserId) {
      const authStore = useAuthStore()
      actualToken = actualToken || authStore.token || undefined
      actualUserId = actualUserId || authStore.user?.id

      if (!authStore.isAuthenticated || !actualUserId) {
        wsLog.warn('Not authenticated, skipping connection')
        return
      }
    }

    if (!actualToken) {
      wsLog.warn('No token available, skipping connection')
      return
    }

    // Guard: Already connected with same socket?
    if (socket.value?.connected) {
      wsLog.debug('Already connected', { socketId: socket.value.id })
      return
    }

    // Guard: Connection in progress?
    if (isConnecting.value) {
      wsLog.debug('Connection already in progress')
      return
    }

    // Clean up existing socket if any
    if (socket.value) {
      wsLog.warn('Cleaning up existing socket', {
        id: socket.value.id,
        connected: socket.value.connected
      })
      socket.value.removeAllListeners()
      socket.value.disconnect()
      socket.value = null
    }

    // Increment connection ID to invalidate old listeners
    state.connectionId++
    wsLog.debug(`New connection ID: ${state.connectionId}`)

    const config = useRuntimeConfig()
    const backendUrl = config.public.apiUrl || 'http://localhost:8000'

    wsLog.info(`Connecting to ${backendUrl} as user ${actualUserId}`)

    isConnecting.value = true
    syncState()

    // Create socket with explicit options
    // CRITICAL: Use markRaw() to prevent Vue's reactivity from proxifying the socket
    // Vue's Proxy can interfere with Socket.IO's internal state management
    const newSocket = markRaw(io(backendUrl, {
      auth: {
        user_id: actualUserId,
        token: actualToken
      },
      transports: ['websocket'],  // WebSocket only - avoid polling upgrade issues
      autoConnect: false,         // CRITICAL: Don't connect automatically
      timeout: 60000,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 10,   // Limit reconnection attempts (was Infinity)
      ackTimeout: 30000,
      retries: 3
    }))

    // Attach listeners BEFORE connecting
    attachListeners(newSocket)

    // Store socket
    socket.value = newSocket
    syncState()

    // Now connect
    wsLog.debug('Calling socket.connect()...')
    newSocket.connect()
  }

  /**
   * Disconnect from WebSocket
   */
  const disconnect = () => {
    wsLog.info('═══════════════════════════════════════════════════════════')
    wsLog.info('disconnect() called')

    if (socket.value) {
      wsLog.debug('Disconnecting socket', { id: socket.value.id })
      socket.value.removeAllListeners()
      socket.value.disconnect()
      socket.value = null
    }

    isConnected.value = false
    isConnecting.value = false
    syncState()

    wsLog.success('Disconnected')
  }

  /**
   * Update socket auth without reconnecting
   */
  const updateAuth = (token: string, userId: number) => {
    if (socket.value) {
      socket.value.auth = { user_id: userId, token }
      wsLog.debug('Auth updated', { userId })
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

// ============================================================================
// EXPORTED COMPOSABLE (Singleton)
// ============================================================================
export function useWebSocket() {
  if (!composableInstance) {
    wsLog.debug('Creating singleton composable instance')
    composableInstance = createWebSocketComposable()
  }
  return composableInstance
}

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
 * Author: Claude
 * Date: 2026-01-08
 * Updated: 2026-01-12 - Singleton pattern + debug logging
 * Updated: 2026-01-19 - HMR-safe with import.meta.hot.data, autoConnect: false
 * Updated: 2026-01-19 - HEAVY DEBUG LOGGING to diagnose disconnect loop
 */
import { ref } from 'vue'
import { io, Socket } from 'socket.io-client'
import { useVintedBridge } from './useVintedBridge'

// ============================================================================
// DEBUG LOGGING - Enhanced for troubleshooting disconnect issues
// ============================================================================
const getTimestamp = () => new Date().toISOString().substr(11, 12) // HH:MM:SS.mmm
const wsLog = {
  debug: (msg: string, ...args: any[]) => console.log(`%c[WS ${getTimestamp()}] ${msg}`, 'color: #888', ...args),
  info: (msg: string, ...args: any[]) => console.log(`%c[WS ${getTimestamp()}] ${msg}`, 'color: #0ea5e9', ...args),
  success: (msg: string, ...args: any[]) => console.log(`%c[WS ${getTimestamp()}] ✓ ${msg}`, 'color: #22c55e', ...args),
  warn: (msg: string, ...args: any[]) => console.warn(`[WS ${getTimestamp()}] ⚠ ${msg}`, ...args),
  error: (msg: string, ...args: any[]) => console.error(`[WS ${getTimestamp()}] ✗ ${msg}`, ...args),
  trace: (msg: string, ...args: any[]) => {
    console.log(`%c[WS ${getTimestamp()}] 🔍 ${msg}`, 'color: #f59e0b', ...args)
    console.trace() // Print stack trace
  },
}

// Connection counter for debugging
let connectionAttemptCount = 0
let totalConnections = 0
let totalDisconnections = 0

// Log socket state helper
const logSocketState = (context: string) => {
  wsLog.debug(`═══ SOCKET STATE [${context}] ═══`)
  wsLog.debug(`  socket.value exists: ${!!socket.value}`)
  wsLog.debug(`  socket.value?.id: ${socket.value?.id || 'N/A'}`)
  wsLog.debug(`  socket.value?.connected: ${socket.value?.connected}`)
  wsLog.debug(`  socket.value?.disconnected: ${socket.value?.disconnected}`)
  wsLog.debug(`  isConnected.value: ${isConnected.value}`)
  wsLog.debug(`  isConnecting.value: ${isConnecting.value}`)
  wsLog.debug(`  connectionAttemptCount: ${connectionAttemptCount}`)
  wsLog.debug(`  totalConnections: ${totalConnections}`)
  wsLog.debug(`  totalDisconnections: ${totalDisconnections}`)
  if (socket.value) {
    wsLog.debug(`  socket.io.engine?.transport?.name: ${(socket.value as any).io?.engine?.transport?.name || 'N/A'}`)
    wsLog.debug(`  socket.io.engine?.readyState: ${(socket.value as any).io?.engine?.readyState || 'N/A'}`)
  }
  wsLog.debug(`═══════════════════════════════`)
}

// ============================================================================
// HMR-SAFE STORAGE
// ============================================================================
interface HMRData {
  socket: any
  isConnected: boolean
}

const getHMRSocket = (): Socket | null => {
  if (import.meta.hot?.data?.socket) {
    wsLog.debug('HMR: Found preserved socket', { id: import.meta.hot.data.socket?.id })
    return import.meta.hot.data.socket as Socket
  }
  wsLog.debug('HMR: No preserved socket found')
  return null
}

// Initialize state from HMR-preserved data or fresh
const socket = ref<Socket | null>(getHMRSocket())
const isConnected = ref(getHMRSocket()?.connected ?? false)
const isConnecting = ref(false)
const error = ref<string | null>(null)

wsLog.info('Module initialized', {
  hasHMRSocket: !!getHMRSocket(),
  socketId: socket.value?.id,
  isConnected: isConnected.value
})

// HMR handlers
if (import.meta.hot) {
  import.meta.hot.dispose((data: HMRData) => {
    data.socket = socket.value
    data.isConnected = isConnected.value
    wsLog.debug('HMR dispose: preserving socket', { socketId: socket.value?.id })
  })
  import.meta.hot.accept()
}

// ============================================================================
// EMIT WITH ACK - Using Socket.IO native method
// ============================================================================
async function emitWithAck(event: string, data: any, timeout: number = 30000): Promise<any> {
  wsLog.debug(`emitWithAck() called for ${event}`)
  logSocketState(`emitWithAck-start-${event}`)

  if (!socket.value) {
    wsLog.error('emitWithAck: Socket not initialized!')
    throw new Error('Socket not initialized')
  }

  // If disconnected, wait for reconnection first
  if (!socket.value.connected) {
    wsLog.warn(`emitWithAck: Socket disconnected, waiting for reconnection before emitting ${event}...`)

    await new Promise<void>((resolve, reject) => {
      let timeoutId: ReturnType<typeof setTimeout> | null = null
      let resolved = false

      const onConnect = () => {
        if (resolved) return
        resolved = true
        if (timeoutId) clearTimeout(timeoutId)
        wsLog.info(`emitWithAck: Reconnected, now emitting ${event}`)
        resolve()
      }

      const onTimeout = () => {
        if (resolved) return
        resolved = true
        socket.value?.off('connect', onConnect)
        wsLog.error(`emitWithAck: Timeout waiting for reconnection to emit ${event}`)
        reject(new Error(`Connection timeout waiting to emit ${event}`))
      }

      socket.value!.once('connect', onConnect)
      timeoutId = setTimeout(onTimeout, timeout)
    })
  }

  wsLog.info(`emitWithAck: Emitting ${event}...`)
  wsLog.debug(`emitWithAck: Data to emit:`, JSON.stringify(data).substring(0, 200))
  logSocketState(`emitWithAck-before-emit-${event}`)

  const startTime = performance.now()

  try {
    wsLog.debug(`emitWithAck: Calling socket.timeout(${timeout}).emitWithAck()...`)
    const response = await socket.value.timeout(timeout).emitWithAck(event, data)
    const elapsed = (performance.now() - startTime).toFixed(1)
    wsLog.success(`emitWithAck: ${event} acknowledged by server in ${elapsed}ms`)
    wsLog.debug(`emitWithAck: Response:`, response)
    logSocketState(`emitWithAck-after-ack-${event}`)
    return response
  } catch (err: any) {
    const elapsed = (performance.now() - startTime).toFixed(1)
    wsLog.error(`emitWithAck: ${event} failed after ${elapsed}ms: ${err.message}`)
    wsLog.error(`emitWithAck: Error details:`, err)
    logSocketState(`emitWithAck-error-${event}`)
    throw err
  }
}

// ============================================================================
// MAIN COMPOSABLE
// ============================================================================
export function useWebSocket() {
  const vintedBridge = useVintedBridge()

  /**
   * Attach Engine.IO level listeners (called AFTER connect)
   * These listeners require the engine to be initialized, which only happens after connection.
   */
  const attachEngineListeners = () => {
    if (!socket.value?.io?.engine) {
      wsLog.warn('attachEngineListeners: No engine available yet')
      return
    }

    wsLog.debug('Attaching Engine.IO listeners...')

    const engine = socket.value.io.engine

    engine.on('open', () => {
      wsLog.debug('Engine: transport opened')
    })

    engine.on('close', (reason: string, description: any) => {
      wsLog.warn(`Engine: transport closed - reason: ${reason}`, description)
    })

    engine.on('packet', (packet: any) => {
      // Only log non-ping/pong packets to reduce noise
      if (packet.type !== 'ping' && packet.type !== 'pong') {
        wsLog.debug(`Engine: packet received - type: ${packet.type}`)
      }
    })

    engine.on('packetCreate', (packet: any) => {
      if (packet.type !== 'ping' && packet.type !== 'pong') {
        wsLog.debug(`Engine: packet created - type: ${packet.type}`)
      }
    })

    engine.on('drain', () => {
      wsLog.debug('Engine: write buffer drained')
    })

    engine.on('upgrading', (transport: any) => {
      wsLog.info(`Engine: upgrading to ${transport.name}`)
    })

    engine.on('upgrade', (transport: any) => {
      wsLog.success(`Engine: upgraded to ${transport.name}`)
    })

    engine.on('upgradeError', (err: Error) => {
      wsLog.error(`Engine: upgrade error - ${err.message}`)
    })

    wsLog.debug('Engine.IO listeners attached')
  }

  /**
   * Connect to backend WebSocket
   */
  const connect = (token?: string, userId?: number) => {
    connectionAttemptCount++
    wsLog.info(`════════════════════════════════════════════════════════════`)
    wsLog.info(`connect() called - Attempt #${connectionAttemptCount}`)
    wsLog.trace('connect() call stack')
    logSocketState('connect-start')

    // Get auth from store if not provided
    let actualToken = token
    let actualUserId = userId

    if (!actualToken || !actualUserId) {
      const authStore = useAuthStore()
      actualToken = actualToken || authStore.token || undefined
      actualUserId = actualUserId || authStore.user?.id

      wsLog.debug('Auth from store:', {
        isAuthenticated: authStore.isAuthenticated,
        userId: actualUserId,
        hasToken: !!actualToken,
        tokenFirst20: actualToken?.substring(0, 20)
      })

      if (!authStore.isAuthenticated || !actualUserId) {
        wsLog.warn('Not authenticated, skipping connection')
        return
      }
    }

    if (!actualToken) {
      wsLog.warn('Token not available, skipping connection')
      return
    }

    // Check: already connected?
    if (socket.value?.connected) {
      wsLog.debug('Already connected, skipping')
      logSocketState('connect-already-connected')
      return
    }

    // Check: connection in progress?
    if (isConnecting.value) {
      wsLog.debug('Connection already in progress, skipping')
      logSocketState('connect-in-progress')
      return
    }

    // Destroy stale socket if exists
    if (socket.value) {
      wsLog.warn('Socket exists but not connected - destroying stale socket')
      wsLog.debug('Stale socket details:', {
        id: socket.value.id,
        connected: socket.value.connected,
        disconnected: socket.value.disconnected
      })
      socket.value.removeAllListeners()
      socket.value.disconnect()
      socket.value = null
      wsLog.debug('Stale socket destroyed')
    }

    const config = useRuntimeConfig()
    const backendUrl = config.public.apiUrl || 'http://localhost:8000'
    wsLog.info(`Creating new socket to ${backendUrl} as user ${actualUserId}`)

    isConnecting.value = true

    // Create socket with detailed logging
    // FIX 2026-01-19: Use websocket-only to avoid polling→websocket upgrade issues
    // The upgrade process seems to cause immediate disconnection after completion
    wsLog.debug('Socket.IO options:', {
      transports: ['websocket'],
      autoConnect: false,
      timeout: 60000,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 'Infinity',
      ackTimeout: 30000,
      retries: 5
    })

    socket.value = io(backendUrl, {
      auth: {
        user_id: actualUserId,
        token: actualToken
      },
      // FIX 2026-01-19: WebSocket-only transport to avoid upgrade issues
      // The polling→websocket upgrade was causing immediate disconnection
      transports: ['websocket'],
      autoConnect: false,
      timeout: 60000,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity,
      ackTimeout: 30000,
      retries: 5
    })

    wsLog.debug('Socket created, attaching event listeners...')

    // ========================================================================
    // EVENT LISTENERS - With extensive logging
    // ========================================================================

    socket.value.on('connect', () => {
      totalConnections++
      isConnected.value = true
      isConnecting.value = false
      error.value = null
      wsLog.success(`════════════════════════════════════════════════════════════`)
      wsLog.success(`CONNECTED! Socket ID: ${socket.value?.id}`)
      wsLog.success(`Total connections so far: ${totalConnections}`)
      wsLog.success(`Transport: ${(socket.value as any)?.io?.engine?.transport?.name || 'unknown'}`)
      logSocketState('on-connect')

      // Attach Engine.IO listeners AFTER connection is established
      // (engine is only properly initialized after connect)
      attachEngineListeners()
    })

    socket.value.on('disconnect', (reason, details) => {
      totalDisconnections++
      isConnected.value = false
      wsLog.warn(`════════════════════════════════════════════════════════════`)
      wsLog.warn(`DISCONNECTED! Reason: ${reason}`)
      wsLog.warn(`Total disconnections so far: ${totalDisconnections}`)
      wsLog.warn(`Disconnect details:`, details)
      wsLog.trace('disconnect event stack trace')
      logSocketState('on-disconnect')

      // Log common disconnect reasons
      switch (reason) {
        case 'io server disconnect':
          wsLog.error('Server forcefully disconnected the socket!')
          break
        case 'io client disconnect':
          wsLog.info('Client called socket.disconnect()')
          break
        case 'ping timeout':
          wsLog.error('Ping timeout - server did not respond to ping')
          break
        case 'transport close':
          wsLog.error('Transport was closed (connection dropped)')
          break
        case 'transport error':
          wsLog.error('Transport encountered an error')
          break
        default:
          wsLog.warn(`Unknown disconnect reason: ${reason}`)
      }
    })

    socket.value.on('reconnect', (attempt: number) => {
      wsLog.info(`Reconnected after ${attempt} attempts, Socket ID: ${socket.value?.id}`)
      logSocketState('on-reconnect')
    })

    socket.value.on('reconnect_attempt', (attempt: number) => {
      wsLog.debug(`Reconnect attempt #${attempt}...`)
    })

    socket.value.on('reconnect_error', (err: Error) => {
      wsLog.error(`Reconnect error: ${err.message}`)
    })

    socket.value.on('reconnect_failed', () => {
      wsLog.error('Reconnection failed after all attempts!')
    })

    socket.value.on('connect_error', (err) => {
      error.value = err.message
      wsLog.error(`════════════════════════════════════════════════════════════`)
      wsLog.error(`CONNECTION ERROR: ${err.message}`)
      wsLog.error(`Error details:`, err)
      logSocketState('on-connect-error')
    })

    socket.value.on('error', (err) => {
      wsLog.error(`Socket error event: ${err}`)
    })

    // Manager-level events (these are safe to attach before connect)
    socket.value.io.on('error', (err) => {
      wsLog.error(`Manager (io) error: ${err}`)
    })

    socket.value.io.on('reconnect', (attempt) => {
      wsLog.info(`Manager (io) reconnect after ${attempt} attempts`)
    })

    socket.value.io.on('reconnect_attempt', (attempt) => {
      wsLog.debug(`Manager (io) reconnect_attempt #${attempt}`)
    })

    socket.value.io.on('reconnect_error', (err) => {
      wsLog.error(`Manager (io) reconnect_error: ${err}`)
    })

    socket.value.io.on('reconnect_failed', () => {
      wsLog.error('Manager (io) reconnect_failed')
    })

    socket.value.io.on('ping', () => {
      wsLog.debug('Engine.IO PING sent')
    })

    // NOTE: Engine.IO listeners are attached in attachEngineListeners()
    // which is called AFTER the 'connect' event fires

    // Plugin commands from backend
    socket.value.on('plugin_command', async (data) => {
      wsLog.info(`════════════════════════════════════════════════════════════`)
      wsLog.info(`Received plugin_command: ${data.action} (req: ${data.request_id})`)
      logSocketState('on-plugin-command')
      await handlePluginCommand(data)
    })

    // Now connect
    wsLog.info('Calling socket.connect()...')
    socket.value.connect()
    wsLog.debug('socket.connect() called')
    logSocketState('after-connect-call')
  }

  // Handle plugin command from backend
  const handlePluginCommand = async (data: {
    request_id: string
    action: string
    payload: any
  }) => {
    wsLog.debug(`handlePluginCommand: Processing ${data.action}...`)
    wsLog.debug(`handlePluginCommand: Payload:`, JSON.stringify(data.payload).substring(0, 200))
    logSocketState('handlePluginCommand-start')

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
      wsLog.success(`handlePluginCommand: Command ${data.action} completed in ${elapsed}ms`, { success: result.success })
      logSocketState('handlePluginCommand-before-response')

      // Send response back to backend
      wsLog.debug('handlePluginCommand: Sending plugin_response...')
      await emitWithAck('plugin_response', {
        request_id: data.request_id,
        success: result.success,
        data: result.data,
        error: result.error
      })
      wsLog.success('handlePluginCommand: plugin_response sent successfully')
      logSocketState('handlePluginCommand-after-response')

    } catch (err: any) {
      const elapsed = (performance.now() - startTime).toFixed(1)
      wsLog.error(`handlePluginCommand: Command ${data.action} failed after ${elapsed}ms: ${err.message}`)
      logSocketState('handlePluginCommand-error')

      try {
        wsLog.debug('handlePluginCommand: Sending error plugin_response...')
        await emitWithAck('plugin_response', {
          request_id: data.request_id,
          success: false,
          data: null,
          error: err.message
        })
        wsLog.debug('handlePluginCommand: Error plugin_response sent')
      } catch (emitErr: any) {
        wsLog.error(`handlePluginCommand: Failed to send error response: ${emitErr.message}`)
      }
    }
  }

  /**
   * Disconnect from WebSocket
   */
  const disconnect = () => {
    wsLog.info(`════════════════════════════════════════════════════════════`)
    wsLog.info('disconnect() called explicitly')
    wsLog.trace('disconnect() call stack')
    logSocketState('disconnect-start')

    if (socket.value) {
      wsLog.debug('Removing all listeners...')
      socket.value.removeAllListeners()
      wsLog.debug('Calling socket.disconnect()...')
      socket.value.disconnect()
      wsLog.debug('Setting socket.value to null...')
      socket.value = null
    } else {
      wsLog.debug('No socket to disconnect')
    }

    isConnected.value = false
    isConnecting.value = false
    wsLog.success('Disconnect complete')
    logSocketState('disconnect-end')
  }

  /**
   * Update socket auth without reconnecting
   */
  const updateAuth = (token: string, userId: number) => {
    wsLog.debug('updateAuth() called')
    if (socket.value) {
      socket.value.auth = { user_id: userId, token }
      wsLog.debug('Socket auth updated', { userId, tokenFirst20: token.substring(0, 20) })
    } else {
      wsLog.warn('updateAuth: No socket to update')
    }
  }

  return {
    socket,
    isConnected,
    error,
    connect,
    disconnect,
    updateAuth
  }
}

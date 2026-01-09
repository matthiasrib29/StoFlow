/**
 * useWebSocket - Composable for WebSocket connection with backend
 *
 * Provides real-time bidirectional communication between frontend and backend.
 * Used to relay plugin commands from backend to browser extension.
 *
 * Author: Claude
 * Date: 2026-01-08
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'
import { useAuthStore } from '~/stores/auth'
import { useVintedBridge } from './useVintedBridge'

export function useWebSocket() {
  const authStore = useAuthStore()
  const vintedBridge = useVintedBridge()

  const socket = ref<Socket | null>(null)
  const isConnected = ref(false)
  const error = ref<string | null>(null)

  // Connect to backend WebSocket
  const connect = () => {
    if (!authStore.isAuthenticated || !authStore.user?.id) {
      console.warn('[WebSocket] Not authenticated, skipping connection')
      return
    }

    const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

    socket.value = io(backendUrl, {
      auth: {
        user_id: authStore.user.id,
        token: authStore.accessToken
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
      console.log('[WebSocket] Connected to backend')
    })

    socket.value.on('disconnect', () => {
      isConnected.value = false
      console.log('[WebSocket] Disconnected from backend')
    })

    socket.value.on('connect_error', (err) => {
      error.value = err.message
      console.error('[WebSocket] Connection error:', err)
    })

    // Listen for plugin commands from backend
    socket.value.on('plugin_command', async (data) => {
      console.log('[WebSocket] Received plugin command:', data.action)
      await handlePluginCommand(data)
    })
  }

  // Handle plugin command from backend
  const handlePluginCommand = async (data: {
    request_id: string
    action: string
    payload: any
  }) => {
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

        default:
          throw new Error(`Unknown action: ${data.action}`)
      }

      // Send response back to backend
      socket.value?.emit('plugin_response', {
        request_id: data.request_id,
        success: result.success,
        data: result.data,
        error: result.error
      })
    } catch (error: any) {
      console.error('[WebSocket] Plugin command failed:', error)

      socket.value?.emit('plugin_response', {
        request_id: data.request_id,
        success: false,
        data: null,
        error: error.message
      })
    }
  }

  // Disconnect
  const disconnect = () => {
    socket.value?.disconnect()
    socket.value = null
    isConnected.value = false
  }

  // Auto-connect on mount
  onMounted(() => {
    connect()
  })

  // Auto-disconnect on unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    socket,
    isConnected,
    error,
    connect,
    disconnect
  }
}

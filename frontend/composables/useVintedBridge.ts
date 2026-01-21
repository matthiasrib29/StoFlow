/**
 * useVintedBridge - Unified bridge for plugin communication
 *
 * This composable handles ALL communication with the StoFlow browser extension:
 * 1. Authentication sync (SSO tokens)
 * 2. Vinted actions (getUserInfo, getWardrobe, publish, update, delete, etc.)
 *
 * Architecture:
 * - Chrome: Uses chrome.runtime.sendMessage (externally_connectable)
 * - Firefox: Falls back to postMessage via content script (Firefox doesn't support externally_connectable)
 *
 * @author Claude
 * @date 2026-01-06
 */

import { ref, computed, onMounted, onUnmounted, getCurrentInstance } from 'vue'

// ============================================================
// TYPES
// ============================================================

export interface BridgeResponse {
  success: boolean
  requestId?: string
  data?: any
  error?: string
  errorCode?: string
}

export interface VintedUserInfo {
  id: string
  login: string
  avatar?: string
  country?: string
}

export interface VintedProduct {
  id: number
  title: string
  price: number
  [key: string]: any
}

export interface VintedApiCallOptions {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  endpoint: string
  data?: any
  params?: Record<string, any>
}

// ============================================================
// CONFIGURATION
// ============================================================

// Extension ID (from manifest.json browser_specific_settings.gecko.id)
const EXTENSION_ID = 'stoflow@stoflow.com'

// Chrome extension ID (can be overridden via env variable for different builds)
const CHROME_EXTENSION_ID = import.meta.env?.VITE_CHROME_EXTENSION_ID || EXTENSION_ID

// Allowed extension origin prefixes
const ALLOWED_EXTENSION_PREFIXES = [
  'moz-extension://',   // Firefox
  'chrome-extension://' // Chrome/Edge
]

// Default timeout for plugin operations (30 seconds)
const DEFAULT_TIMEOUT = 30000

// ============================================================
// ERRORS
// ============================================================

export class PluginNotInstalledError extends Error {
  constructor(message = 'StoFlow plugin is not installed') {
    super(message)
    this.name = 'PluginNotInstalledError'
  }
}

export class PluginTimeoutError extends Error {
  constructor(message = 'Plugin operation timed out') {
    super(message)
    this.name = 'PluginTimeoutError'
  }
}

export class NoVintedTabError extends Error {
  constructor(message = 'No Vinted tab found. Please open www.vinted.fr in a browser tab.') {
    super(message)
    this.name = 'NoVintedTabError'
  }
}

// ============================================================
// SINGLETON STATE (shared across all composable instances)
// ============================================================

// These must be outside the function to be shared across all instances
const isInstalled = ref<boolean | null>(null)
const hasVintedTab = ref(false)
const isLoading = ref(false)
const error = ref<string | null>(null)
const lastError = ref<BridgeResponse | null>(null)

// Firefox fallback: plugin origin for postMessage (SINGLETON)
let pluginOrigin: string | null = null

// Pending requests for Firefox fallback (SINGLETON)
const pendingRequests = new Map<string, { resolve: (value: any) => void; reject: (error: any) => void; timeout: NodeJS.Timeout }>()

// Track if global listener is already installed
let listenerInstalled = false

// ============================================================
// COMPOSABLE
// ============================================================

export function useVintedBridge() {
  // No local state - using singleton state above

  // Flag for logs (enabled only in development)
  const DEBUG_ENABLED = import.meta.env.DEV

  // ============================================================
  // INTERNAL HELPERS
  // ============================================================

  // Timestamp helper
  const getTimestamp = () => new Date().toISOString().substr(11, 12)

  const log = {
    debug: (...args: any[]) => DEBUG_ENABLED && console.log(`[VintedBridge ${getTimestamp()}]`, ...args),
    info: (...args: any[]) => DEBUG_ENABLED && console.info(`[VintedBridge ${getTimestamp()}]`, ...args),
    warn: (...args: any[]) => console.warn(`[VintedBridge ${getTimestamp()}]`, ...args),
    error: (...args: any[]) => console.error(`[VintedBridge ${getTimestamp()}]`, ...args)
  }

  /**
   * Generate a unique request ID
   */
  function generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Check if an origin is a valid extension origin
   */
  function isValidExtensionOrigin(origin: string): boolean {
    return ALLOWED_EXTENSION_PREFIXES.some(prefix => origin.startsWith(prefix))
  }

  /**
   * Check if we're running in Firefox (no externally_connectable support)
   */
  function isFirefox(): boolean {
    return typeof navigator !== 'undefined' && navigator.userAgent.includes('Firefox')
  }

  /**
   * Check if chrome.runtime is available
   */
  function hasChromeRuntime(): boolean {
    return typeof window !== 'undefined' &&
           typeof window.chrome !== 'undefined' &&
           typeof window.chrome.runtime !== 'undefined' &&
           typeof window.chrome.runtime.sendMessage === 'function'
  }

  // ============================================================
  // CORE MESSAGING
  // ============================================================

  /**
   * Send a message to the plugin via chrome.runtime.sendMessage (Chrome)
   * or via postMessage (Firefox fallback)
   */
  async function sendMessage(message: any, timeout = DEFAULT_TIMEOUT): Promise<BridgeResponse> {
    const requestId = generateRequestId()
    const messageWithId = { ...message, requestId }

    log.info('🚀 Sending message:', {
      action: message.action,
      requestId,
      hasChromeRuntime: hasChromeRuntime(),
      isFirefox: isFirefox(),
      hasPluginOrigin: !!pluginOrigin,
      pluginOrigin,
      listenerInstalled
    })

    // Try chrome.runtime.sendMessage first (works on Chrome)
    if (hasChromeRuntime() && !isFirefox()) {
      log.info('📡 Using chrome.runtime.sendMessage')
      try {
        return await sendViaChromeRuntime(messageWithId, timeout)
      } catch (err: any) {
        log.error('❌ chrome.runtime error:', err.message)
        // If chrome.runtime fails, check if it's because plugin is not installed
        if (err.message?.includes('Could not establish connection') ||
            err.message?.includes('Extension not found') ||
            err.message?.includes('Receiving end does not exist')) {
          throw new PluginNotInstalledError()
        }
        throw err
      }
    }

    // Firefox fallback: use postMessage via content script
    if (pluginOrigin) {
      log.info('📬 Using postMessage fallback (Firefox)')
      return await sendViaPostMessage(messageWithId, timeout)
    }

    // No communication method available
    log.error('❌ Aucune méthode de communication disponible!')
    throw new PluginNotInstalledError('Plugin not detected. Please install the StoFlow extension.')
  }

  /**
   * Send message via chrome.runtime.sendMessage (externally_connectable)
   */
  function sendViaChromeRuntime(message: any, timeout: number): Promise<BridgeResponse> {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new PluginTimeoutError())
      }, timeout)

      try {
        const chrome = window.chrome as any
        chrome.runtime.sendMessage(CHROME_EXTENSION_ID, message, (response: any) => {
          clearTimeout(timeoutId)

          // Check for chrome.runtime errors
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message))
            return
          }

          // Check for error response from plugin
          if (response?.errorCode === 'NO_VINTED_TAB') {
            reject(new NoVintedTabError(response.error))
            return
          }

          log.debug('Response received:', message.action, response?.success)
          resolve(response || { success: false, error: 'No response from plugin' })
        })
      } catch (err) {
        clearTimeout(timeoutId)
        reject(err)
      }
    })
  }

  /**
   * Send message via postMessage (Firefox fallback)
   */
  function sendViaPostMessage(message: any, timeout: number): Promise<BridgeResponse> {
    return new Promise((resolve, reject) => {
      const requestId = message.requestId

      log.info('📤 Envoi postMessage vers plugin:', {
        requestId,
        action: message.action,
        pluginOrigin,
        message
      })

      const timeoutId = setTimeout(() => {
        log.error('⏱️ Timeout - aucune réponse du plugin après', timeout, 'ms')
        pendingRequests.delete(requestId)
        reject(new PluginTimeoutError())
      }, timeout)

      // Store pending request
      pendingRequests.set(requestId, { resolve, reject, timeout: timeoutId })

      // Send message to content script
      window.postMessage({
        type: 'VINTED_ACTION',
        ...message
      }, pluginOrigin!)

      log.debug('✅ postMessage envoyé')
    })
  }

  // ============================================================
  // DETECTION
  // ============================================================

  /**
   * Send a ping to content script to trigger STOFLOW_PLUGIN_READY response
   * This helps Firefox detect the plugin after injection
   */
  function pingContentScript(): void {
    log.debug('🏓 Sending STOFLOW_PING to content script...')
    window.postMessage({ type: 'STOFLOW_PING' }, window.location.origin)
  }

  /**
   * Check if the plugin is installed and responsive
   */
  async function checkInstalled(): Promise<boolean> {
    if (!import.meta.client) {
      isInstalled.value = false
      return false
    }

    try {
      // Already detected via postMessage?
      if (pluginOrigin) {
        isInstalled.value = true
        return true
      }

      // Try chrome.runtime PING
      if (hasChromeRuntime() && !isFirefox()) {
        const response = await sendMessage({ action: 'PING' }, 5000)
        isInstalled.value = response?.success === true
        return isInstalled.value
      }

      // Firefox: send ping to content script and wait for response
      if (isFirefox()) {
        log.info('🦊 Firefox detected - pinging content script...')
        pingContentScript()

        // Wait a bit for response
        await new Promise(resolve => setTimeout(resolve, 500))

        if (pluginOrigin) {
          isInstalled.value = true
          return true
        }

        // Retry a few times
        for (let i = 0; i < 3; i++) {
          log.debug(`🔄 Retry ping ${i + 1}/3...`)
          pingContentScript()
          await new Promise(resolve => setTimeout(resolve, 500))
          if (pluginOrigin) {
            isInstalled.value = true
            return true
          }
        }
      }

      // Firefox: wait for plugin announcement
      isInstalled.value = false
      return false
    } catch (err) {
      log.debug('Plugin not installed:', err)
      isInstalled.value = false
      return false
    }
  }

  /**
   * Check if a Vinted tab is open
   */
  async function checkVintedTab(): Promise<boolean> {
    try {
      const response = await sendMessage({ action: 'CHECK_VINTED_TAB' })
      hasVintedTab.value = response?.data?.hasVintedTab === true
      return hasVintedTab.value
    } catch (err) {
      hasVintedTab.value = false
      return false
    }
  }

  /**
   * Open a Vinted tab
   */
  async function openVintedTab(url?: string): Promise<BridgeResponse> {
    return sendMessage({ action: 'OPEN_VINTED_TAB', payload: { url } })
  }


  // ============================================================
  // VINTED ACTIONS
  // ============================================================

  /**
   * Get Vinted user info
   */
  async function getUserInfo(): Promise<BridgeResponse> {
    isLoading.value = true
    error.value = null

    try {
      const response = await sendMessage({ action: 'VINTED_GET_USER_INFO' })

      if (!response.success) {
        error.value = response.error || 'Failed to get user info'
        lastError.value = response
      }

      return response
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get Vinted user profile (more detailed)
   */
  async function getUserProfile(): Promise<BridgeResponse> {
    isLoading.value = true
    error.value = null

    try {
      const response = await sendMessage({ action: 'VINTED_GET_USER_PROFILE' })

      if (!response.success) {
        error.value = response.error || 'Failed to get user profile'
        lastError.value = response
      }

      return response
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get user's wardrobe items from Vinted
   */
  async function getWardrobe(userId: string, page = 1, perPage = 96): Promise<BridgeResponse> {
    isLoading.value = true
    error.value = null

    try {
      const response = await sendMessage({
        action: 'VINTED_GET_WARDROBE',
        payload: { userId, page, perPage }
      })

      if (!response.success) {
        error.value = response.error || 'Failed to get wardrobe'
        lastError.value = response
      }

      return response
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Execute a generic Vinted API call
   */
  async function executeApiCall(options: VintedApiCallOptions): Promise<BridgeResponse> {
    isLoading.value = true
    error.value = null

    try {
      const response = await sendMessage({
        action: 'VINTED_API_CALL',
        payload: options
      })

      if (!response.success) {
        error.value = response.error || 'API call failed'
        lastError.value = response
      }

      return response
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch Vinted users for prospection
   */
  async function fetchUsers(searchText: string, page = 1, perPage = 100): Promise<BridgeResponse> {
    isLoading.value = true
    error.value = null

    try {
      const response = await sendMessage({
        action: 'VINTED_FETCH_USERS',
        search_text: searchText,
        page,
        per_page: perPage
      }, 60000) // 60s timeout for user searches

      if (!response.success) {
        error.value = response.error || 'Failed to fetch users'
        lastError.value = response
      }

      return response
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Publish a product to Vinted
   */
  async function publishProduct(productData: any): Promise<BridgeResponse> {
    isLoading.value = true
    error.value = null

    try {
      const response = await sendMessage({
        action: 'VINTED_PUBLISH',
        payload: productData
      })

      if (!response.success) {
        error.value = response.error || 'Failed to publish product'
        lastError.value = response
      }

      return response
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update a product on Vinted
   */
  async function updateProduct(vintedId: string, updates: any): Promise<BridgeResponse> {
    isLoading.value = true
    error.value = null

    try {
      const response = await sendMessage({
        action: 'VINTED_UPDATE',
        payload: { vintedId, updates }
      })

      if (!response.success) {
        error.value = response.error || 'Failed to update product'
        lastError.value = response
      }

      return response
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a product from Vinted
   */
  async function deleteProduct(vintedId: string): Promise<BridgeResponse> {
    isLoading.value = true
    error.value = null

    try {
      const response = await sendMessage({
        action: 'VINTED_DELETE',
        payload: { vintedId }
      })

      if (!response.success) {
        error.value = response.error || 'Failed to delete product'
        lastError.value = response
      }

      return response
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // ============================================================
  // FIREFOX FALLBACK: MESSAGE LISTENER
  // ============================================================

  /**
   * Handle messages from the plugin (Firefox postMessage fallback)
   */
  function handlePluginMessage(event: MessageEvent) {
    const data = event.data

    // Only accept messages from same origin (content script runs in page context)
    // or from extension origins (for future Chrome support)
    const isFromSameOrigin = event.origin === window.location.origin
    const isFromExtension = isValidExtensionOrigin(event.origin)

    if (!isFromSameOrigin && !isFromExtension) {
      return
    }

    // Plugin announcement (from content script injected in same origin)
    if (data?.type === 'STOFLOW_PLUGIN_READY') {
      // Store the origin for future postMessage communication
      pluginOrigin = event.origin
      isInstalled.value = true
      log.info('✅ Plugin detected via postMessage, origin:', pluginOrigin)

      // Send ACK
      window.postMessage({ type: 'STOFLOW_FRONTEND_ACK' }, pluginOrigin)
      return
    }

    // Response to a Vinted action (Firefox fallback)
    if (data?.type === 'VINTED_ACTION_RESPONSE' && data.requestId) {
      try {
        log.info('═══════════════════════════════════════════════')
        log.info('📥 VINTED_ACTION_RESPONSE received')
        log.info('Request ID:', data.requestId)
        log.info('Success:', data.success)
        log.info('Has data:', !!data.data)
        log.info('Has error:', !!data.error)
        log.info('Pending requests count:', pendingRequests.size)
        log.info('Pending request IDs:', Array.from(pendingRequests.keys()))

        const pending = pendingRequests.get(data.requestId)
        if (pending) {
          log.info('✓ Found pending request, resolving...')
          clearTimeout(pending.timeout)
          pendingRequests.delete(data.requestId)

          // Check for error
          if (data.errorCode === 'NO_VINTED_TAB') {
            log.warn('Rejecting with NoVintedTabError')
            pending.reject(new NoVintedTabError(data.error))
          } else {
            log.info('✅ Resolving promise for:', data.requestId)
            log.info('Data to resolve:', { success: data.success, hasData: !!data.data, dataKeys: data.data ? Object.keys(data.data) : [] })
            pending.resolve(data)
            log.info('✅ Promise resolved successfully')
          }
          log.info('═══════════════════════════════════════════════')
        } else {
          log.warn('⚠️ No pending request found for:', data.requestId)
          log.warn('This response will be IGNORED!')
          log.warn('Available pending requests:', Array.from(pendingRequests.keys()))
          log.info('═══════════════════════════════════════════════')
        }
      } catch (err: any) {
        log.error('❌ CRITICAL ERROR in handlePluginMessage:', err.message)
        log.error('Error stack:', err.stack)
        log.error('Data that caused error:', JSON.stringify(data).substring(0, 500))
      }
    }
  }

  // ============================================================
  // LIFECYCLE
  // ============================================================

  /**
   * Initialize the bridge (call once on app mount)
   */
  function init() {
    if (!import.meta.client) return

    // Only install listener once (singleton pattern)
    if (listenerInstalled) {
      log.debug('VintedBridge already initialized (singleton)')
      return
    }

    log.debug('Initializing VintedBridge (singleton)...')

    // Listen for plugin messages (Firefox fallback + plugin announcement)
    window.addEventListener('message', handlePluginMessage)
    listenerInstalled = true

    // Check if plugin is installed
    checkInstalled()

    log.debug('VintedBridge initialized')
  }

  /**
   * Cleanup (call on app unmount)
   * Note: With singleton pattern, we don't cleanup to keep the listener active
   */
  function cleanup() {
    // Don't cleanup - we want to keep the listener active for the singleton
    // The listener will be removed when the page is closed
    log.debug('VintedBridge cleanup skipped (singleton)')
  }

  // Auto-init on mount if used in component context
  // Only register lifecycle hooks if there's an active component instance
  // This prevents warnings when composable is used in stores or other composables
  if (import.meta.client && getCurrentInstance()) {
    onMounted(init)
    // Note: cleanup is now a no-op for singleton pattern
    onUnmounted(cleanup)
  } else if (import.meta.client) {
    // If no component instance, init immediately (for stores/other composables)
    init()
  }

  // ============================================================
  // RETURN
  // ============================================================

  return {
    // State
    isInstalled: computed(() => isInstalled.value),
    hasVintedTab: computed(() => hasVintedTab.value),
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    lastError: computed(() => lastError.value),

    // Detection
    checkInstalled,
    checkVintedTab,
    openVintedTab,

    // Vinted actions
    getUserInfo,
    getUserProfile,
    getWardrobe,
    executeApiCall,
    fetchUsers,
    publishProduct,
    updateProduct,
    deleteProduct,

    // Lifecycle (for manual control if needed)
    init,
    cleanup
  }
}

// ============================================================
// STANDALONE FUNCTIONS (for use outside components, e.g., in stores)
// ============================================================

// Singleton instance for non-component usage
let bridgeInstance: ReturnType<typeof useVintedBridge> | null = null

/**
 * Get the bridge instance (creates one if needed)
 * Use this in stores or other non-component code
 */
export function getVintedBridge() {
  if (!bridgeInstance && import.meta.client) {
    bridgeInstance = useVintedBridge()
    bridgeInstance.init()
  }
  return bridgeInstance
}

/**
 * Initialize the plugin listener (for app-level initialization)
 */
export function initPluginListener() {
  getVintedBridge()
}

/**
 * Generic composable for managing platform connection status
 *
 * Provides connection status checking and disconnect functionality
 * for any marketplace platform (Vinted, eBay, Etsy)
 */
import { platformLogger } from '~/utils/logger'
import type { PlatformCode } from './useWorkflows'

interface PlatformConnectionConfig {
  name: string
  apiPrefix: string
  settingsPath: string
}

const PLATFORM_CONNECTION_CONFIGS: Record<PlatformCode, PlatformConnectionConfig> = {
  vinted: {
    name: 'Vinted',
    apiPrefix: '/vinted',
    settingsPath: '/dashboard/platforms/vinted/settings',
  },
  ebay: {
    name: 'eBay',
    apiPrefix: '/ebay',
    settingsPath: '/dashboard/platforms/ebay/settings',
  },
  etsy: {
    name: 'Etsy',
    apiPrefix: '/etsy',
    settingsPath: '/dashboard/platforms/etsy/settings',
  },
}

export const usePlatformConnection = (platformCode: PlatformCode) => {
  const { get, post } = useApi()
  const router = useRouter()
  const config = PLATFORM_CONNECTION_CONFIGS[platformCode]

  // State
  const isConnected = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Fetch platform connection status
   */
  const fetchStatus = async (): Promise<void> => {
    if (!import.meta.client) return

    try {
      isLoading.value = true
      error.value = null
      const response = await get<{ is_connected: boolean }>(`${config.apiPrefix}/status`)
      isConnected.value = response.is_connected
    } catch (err: any) {
      isConnected.value = false
      error.value = err.message || `Failed to fetch ${config.name} status`
      platformLogger.error(`[${platformCode}] fetchStatus error`, { error: err.message })
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Navigate to platform settings for connection
   */
  const connect = (): void => {
    router.push(config.settingsPath)
  }

  /**
   * Disconnect from platform
   */
  const disconnect = async (): Promise<boolean> => {
    try {
      isLoading.value = true
      error.value = null
      await post(`${config.apiPrefix}/disconnect`)
      isConnected.value = false
      return true
    } catch (err: any) {
      error.value = err.message || `Failed to disconnect ${config.name}`
      platformLogger.error(`[${platformCode}] disconnect error`, { error: err.message })
      return false
    } finally {
      isLoading.value = false
    }
  }

  return {
    // Platform info
    platformName: config.name,
    platformCode,
    settingsPath: config.settingsPath,

    // State
    isConnected,
    isLoading,
    error,

    // Methods
    fetchStatus,
    connect,
    disconnect,
  }
}

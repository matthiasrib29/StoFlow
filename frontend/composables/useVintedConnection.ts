/**
 * Composable for Vinted connection management.
 * Handles connection status, user info, and disconnect flow.
 *
 * Updated: 2026-01-21 - Simplified to use MarketplaceJob + WebSocket flow
 */

export interface VintedConnectionInfo {
  userId: number | null
  username: string | null
  lastSync: string | null
}

export interface VintedStats {
  activePublications: number
  totalViews: number
  totalFavourites: number
  potentialRevenue: number
  totalProducts: number
}

export function useVintedConnection() {
  const { get, post } = useApi()
  const { showSuccess, showError, showInfo, showWarn } = useAppToast()
  const publicationsStore = usePublicationsStore()

  // State
  const isConnected = ref(false)
  const loading = ref(false)
  const connectionInfo = ref<VintedConnectionInfo>({
    userId: null,
    username: null,
    lastSync: null
  })

  const stats = ref<VintedStats>({
    activePublications: 0,
    totalViews: 0,
    totalFavourites: 0,
    potentialRevenue: 0,
    totalProducts: 0
  })

  // Computed
  const platformData = computed(() => {
    return publicationsStore.integrations.find((i: any) => i.platform === 'vinted')
  })

  // Watch platform data for connection status
  watch(() => platformData.value?.is_connected, (connected) => {
    if (connected !== undefined) {
      isConnected.value = connected
    }
  }, { immediate: true })

  /**
   * Check and establish connection with Vinted via MarketplaceJob + WebSocket.
   *
   * New simplified flow (2026-01-21):
   * 1. Frontend calls POST /check-connection
   * 2. Backend creates MarketplaceJob and executes via WebSocket → Plugin
   * 3. Backend returns connection result directly
   */
  const connect = async (): Promise<boolean> => {
    try {
      loading.value = true

      showInfo('Connexion en cours', 'Vérification de la connexion Vinted via le plugin...', 10000)

      // Single API call - backend handles everything via WebSocket → Plugin
      const response = await post<{
        job_id: number
        connected: boolean
        vinted_user_id: number | null
        login: string | null
        error: string | null
      }>('/vinted/check-connection')

      // Handle the response
      if (response.connected) {
        connectionInfo.value.userId = response.vinted_user_id
        connectionInfo.value.username = response.login
        connectionInfo.value.lastSync = 'À l\'instant'
        isConnected.value = true

        await publicationsStore.connectIntegration('vinted')

        showSuccess('Connecté', `Connecté en tant que ${response.login}`, 5000)
        return true
      } else {
        // Parse error message for user-friendly display
        const errorMsg = response.error || 'Échec de la connexion Vinted'

        if (errorMsg.includes('Plugin not installed') || errorMsg.includes('not available')) {
          showWarn(
            'Plugin non installé',
            'Installez le plugin Stoflow pour vous connecter à Vinted',
            8000
          )
        } else if (errorMsg.includes('timeout')) {
          showWarn(
            'Plugin non répondu',
            'Vérifiez que le plugin Stoflow est actif et qu\'un onglet Vinted.fr est ouvert',
            8000
          )
        } else if (errorMsg.includes('No Vinted tab')) {
          showWarn(
            'Aucun onglet Vinted',
            'Ouvrez www.vinted.fr dans un onglet et connectez-vous, puis réessayez',
            8000
          )
        } else {
          showWarn('Non connecté', errorMsg, 5000)
        }
        return false
      }

    } catch (error: any) {
      showError('Erreur de connexion', error.message || 'Impossible de vérifier la connexion à Vinted', 5000)
      return false

    } finally {
      loading.value = false
    }
  }

  /**
   * Disconnect from Vinted.
   */
  const disconnect = async (): Promise<boolean> => {
    try {
      await publicationsStore.disconnectIntegration('vinted')
      isConnected.value = false
      connectionInfo.value = { userId: null, username: null, lastSync: null }
      showInfo('Déconnecté', 'Votre compte Vinted a été déconnecté', 3000)
      return true
    } catch {
      showError('Erreur', 'Impossible de déconnecter le compte', 5000)
      return false
    }
  }

  /**
   * Fetch connection status from API.
   */
  const fetchConnectionStatus = async (): Promise<void> => {
    try {
      const response = await get<{
        is_connected: boolean
        vinted_user_id?: number
        login?: string
        last_sync?: string
        disconnected_at?: string
      }>('/vinted/status')

      isConnected.value = response.is_connected
      if (response.is_connected) {
        connectionInfo.value.userId = response.vinted_user_id || null
        connectionInfo.value.username = response.login || null
        connectionInfo.value.lastSync = response.last_sync || null
      }
    } catch {
      // Silent fail - connection status will be checked on next action
    }
  }

  /**
   * Fetch Vinted stats from API.
   */
  const fetchStats = async (): Promise<void> => {
    try {
      const response = await get<VintedStats>('/vinted/stats')
      stats.value = {
        activePublications: response.activePublications || 0,
        totalViews: response.totalViews || 0,
        totalFavourites: response.totalFavourites || 0,
        potentialRevenue: response.potentialRevenue || 0,
        totalProducts: response.totalProducts || 0
      }
    } catch {
      // Silent fail - stats will show 0
    }
  }

  /**
   * Update last sync timestamp.
   */
  const updateLastSync = () => {
    connectionInfo.value.lastSync = 'À l\'instant'
  }

  return {
    // State
    isConnected: readonly(isConnected),
    loading: readonly(loading),
    connectionInfo: readonly(connectionInfo),
    stats,
    platformData,

    // Methods
    connect,
    disconnect,
    fetchConnectionStatus,
    fetchStats,
    updateLastSync
  }
}

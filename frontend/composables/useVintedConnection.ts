/**
 * Composable for Vinted connection management.
 * Handles connection status, user info, and disconnect flow.
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
   * Check and establish connection with Vinted via plugin.
   */
  const connect = async (): Promise<boolean> => {
    try {
      loading.value = true

      showInfo('Vérification en cours', 'Connexion au plugin... Assurez-vous qu\'un onglet Vinted est ouvert.', 10000)

      const response = await post<{
        connected: boolean
        vinted_user_id: number | null
        login: string | null
        message: string
      }>('/api/vinted/check-connection')

      if (response.connected) {
        connectionInfo.value.userId = response.vinted_user_id
        connectionInfo.value.username = response.login || 'user@vinted.com'
        connectionInfo.value.lastSync = 'À l\'instant'
        isConnected.value = true

        await publicationsStore.connectIntegration('vinted')

        showSuccess('Connecté', response.message || `Connecté en tant que ${response.login}`, 5000)

        return true
      } else {
        showWarn('Non connecté', response.message || 'Connectez-vous à Vinted et réessayez', 5000)
        return false
      }

    } catch (error: any) {
      if (error.statusCode === 408 || error.message?.includes('timeout')) {
        showWarn(
          'Plugin non répondu',
          'Vérifiez que le plugin Stoflow est actif et qu\'un onglet Vinted.fr est ouvert',
          8000
        )
      } else {
        showError('Erreur de connexion', error.message || 'Impossible de vérifier la connexion à Vinted', 5000)
      }
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
        connected: boolean
        vinted_user_id?: number
        username?: string
        last_sync?: string
      }>('/api/vinted/status')

      isConnected.value = response.connected
      if (response.connected) {
        connectionInfo.value.userId = response.vinted_user_id || null
        connectionInfo.value.username = response.username || null
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
      const response = await get<VintedStats>('/api/vinted/stats')
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

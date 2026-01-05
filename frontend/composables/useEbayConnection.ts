/**
 * Composable for eBay connection management.
 * Handles OAuth flow, connection status, and settings.
 */

export function useEbayConnection() {
  const ebayStore = useEbayStore()
  const { showSuccess, showError, showInfo } = useAppToast()
  const confirm = import.meta.client ? useConfirm() : null

  // Connection state
  const loading = ref(false)
  const isConnected = computed(() => ebayStore.isConnected)
  const isConnecting = computed(() => ebayStore.isConnecting)
  const account = computed(() => ebayStore.account)
  const stats = computed(() => ebayStore.stats)
  const policies = computed(() => ({
    shipping: ebayStore.shippingPolicies,
    return: ebayStore.returnPolicies,
    payment: ebayStore.paymentPolicies
  }))

  // Sync settings (local copy for editing)
  const syncSettings = reactive({
    autoSync: true,
    syncInterval: 30,
    syncStock: true,
    syncPrices: true,
    syncDescriptions: false
  })

  // Listing settings
  const listingSettings = reactive({
    defaultListingType: 'FixedPrice',
    defaultDuration: 'GTC',
    defaultShippingPolicy: '',
    defaultReturnPolicy: ''
  })

  /**
   * Initiate OAuth connection flow.
   */
  const connect = async (): Promise<void> => {
    try {
      await ebayStore.initiateOAuth()
      showSuccess('Connexion réussie', 'Votre compte eBay a été connecté avec succès', 3000)
    } catch (error: any) {
      showError('Erreur de connexion', error.message || 'Impossible de connecter à eBay', 5000)
    }
  }

  /**
   * Disconnect from eBay with confirmation.
   */
  const disconnect = (): void => {
    confirm?.require({
      message: 'Voulez-vous vraiment déconnecter votre compte eBay ? Vos publications resteront actives sur eBay.',
      header: 'Confirmation',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Oui, déconnecter',
      rejectLabel: 'Annuler',
      accept: async () => {
        try {
          await ebayStore.disconnect()
          showInfo('Déconnecté', 'Votre compte eBay a été déconnecté', 3000)
        } catch (error) {
          showError('Erreur', 'Impossible de déconnecter le compte', 5000)
        }
      }
    })
  }

  /**
   * Sync data from eBay (stats and policies).
   */
  const syncData = async (): Promise<void> => {
    try {
      await ebayStore.fetchStats()
      await ebayStore.fetchPolicies()
      showSuccess('Synchronisation terminée', 'Vos données eBay sont à jour', 3000)
    } catch (error) {
      showError('Erreur', 'Échec de la synchronisation', 5000)
    }
  }

  /**
   * Check connection status on initialization.
   */
  const checkStatus = async (): Promise<void> => {
    try {
      await ebayStore.checkConnectionStatus()
    } catch (error) {
      console.error('Erreur vérification statut eBay:', error)
    }
  }

  /**
   * Save sync settings.
   */
  const saveSettings = async (): Promise<void> => {
    await ebayStore.saveSyncSettings(syncSettings)
    showSuccess('Paramètres sauvegardés', 'Vos préférences ont été enregistrées', 3000)
  }

  /**
   * Load initial data when connected.
   */
  const loadInitialData = async (): Promise<void> => {
    loading.value = true
    try {
      await Promise.all([
        ebayStore.fetchPolicies(),
        ebayStore.fetchStats()
      ])

      // Sync local settings
      Object.assign(syncSettings, ebayStore.syncSettings)

      // Set default policies
      if (ebayStore.defaultShippingPolicy) {
        listingSettings.defaultShippingPolicy = ebayStore.defaultShippingPolicy.id
      }
      if (ebayStore.defaultReturnPolicy) {
        listingSettings.defaultReturnPolicy = ebayStore.defaultReturnPolicy.id
      }
    } catch (error) {
      console.error('Erreur chargement données:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * Open external eBay pages.
   */
  const openStore = (): void => {
    if (account.value?.storeUrl) {
      window.open(account.value.storeUrl, '_blank')
    }
  }

  const openSettings = (): void => {
    window.open('https://www.ebay.fr/sh/ovw', '_blank')
  }

  return {
    // State
    loading: readonly(loading),
    isConnected,
    isConnecting,
    account,
    stats,
    policies,
    syncSettings,
    listingSettings,

    // Methods
    connect,
    disconnect,
    syncData,
    checkStatus,
    saveSettings,
    loadInitialData,
    openStore,
    openSettings
  }
}

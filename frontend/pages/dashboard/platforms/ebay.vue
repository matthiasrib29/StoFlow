<template>
  <div class="page-container">
    <!-- Not Connected: Connection CTA -->
    <EbayNotConnectedCard
      v-if="!ebayStore.isConnected"
      :loading="ebayStore.isConnecting"
      @connect="handleConnect"
    />

    <!-- Connected: Main Content -->
    <template v-else>
      <!-- Stats Overview -->
      <EbayStatsCards :stats="ebayStore.stats" :monthly-change="5" />
    </template>

    <!-- Modal: Edit Price -->
    <EbayPriceModal
      v-model:visible="priceModalVisible"
      :publication="selectedPublication"
      @save="updatePrice"
    />

    <!-- Modal: New Shipping Policy -->
    <EbayShippingPolicyModal
      v-model:visible="shippingPolicyModal"
      @create="handleCreateShippingPolicy"
    />

    <!-- Modal: New Return Policy -->
    <EbayReturnPolicyModal
      v-model:visible="returnPolicyModal"
      @create="handleCreateReturnPolicy"
    />

    <!-- Confirm Dialog -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { formatCurrency, formatNumber } from '~/utils/formatters'

definePageMeta({
  layout: 'dashboard'
})

// SSR-safe initialization: Only call PrimeVue hooks on client-side
const confirm = import.meta.client ? useConfirm() : null
const ebayStore = useEbayStore()
const publicationsStore = usePublicationsStore()
const { showSuccess, showError, showInfo, showWarn } = useAppToast()

// Composables
const ebayProducts = useEbayProducts()
const ebayHelpers = useEbayHelpers()

// State
const loading = ref(false)
const priceModalVisible = ref(false)
const shippingPolicyModal = ref(false)
const returnPolicyModal = ref(false)
const selectedPublication = ref<any>(null)

// Options for settings
const syncIntervals = [
  { label: 'Toutes les 15 minutes', value: 15 },
  { label: 'Toutes les 30 minutes', value: 30 },
  { label: 'Toutes les heures', value: 60 },
  { label: 'Toutes les 2 heures', value: 120 },
  { label: 'Toutes les 6 heures', value: 360 }
]

const listingTypes = [
  { label: 'Prix fixe', value: 'FixedPrice' },
  { label: 'Enchère', value: 'Auction' },
  { label: 'Meilleure offre', value: 'BestOffer' }
]

const durations = [
  { label: '3 jours', value: '3' },
  { label: '5 jours', value: '5' },
  { label: '7 jours', value: '7' },
  { label: '10 jours', value: '10' },
  { label: '30 jours', value: '30' },
  { label: 'Bonne affaire jusqu\'à annulation', value: 'GTC' }
]

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

// Computed
const publications = computed(() => {
  return publicationsStore.publications
    .filter((p: any) => p.platform === 'ebay')
    .map((p: any) => ({
      ...p,
      product: { id: p.product_id, title: p.product_title },
      views: Math.floor(Math.random() * 150)
    }))
})

// Connection Methods
const handleConnect = async () => {
  try {
    await ebayStore.initiateOAuth()
    showSuccess('Connexion réussie', 'Votre compte eBay a été connecté avec succès', 3000)
  } catch (error: any) {
    showError('Erreur de connexion', error.message || 'Impossible de connecter à eBay', 5000)
  }
}

const handleDisconnect = () => {
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

const handleSync = async () => {
  try {
    await ebayStore.fetchStats()
    await ebayStore.fetchPolicies()
    showSuccess('Synchronisation terminée', 'Vos données eBay sont à jour', 3000)
  } catch (error) {
    showError('Erreur', 'Échec de la synchronisation', 5000)
  }
}

// Price Modal Methods
const editPrice = (publication: any) => {
  selectedPublication.value = publication
  priceModalVisible.value = true
}

const updatePrice = async (newPrice: number) => {
  if (!selectedPublication.value) return

  try {
    selectedPublication.value.price = newPrice
    showSuccess('Prix modifié', 'Le prix a été mis à jour sur eBay', 3000)
    priceModalVisible.value = false
  } catch (error) {
    showError('Erreur', 'Impossible de modifier le prix', 5000)
  }
}

// Publication Methods
const openPublication = (publication: any) => {
  const url = `https://www.ebay.fr/itm/${publication.id}`
  window.open(url, '_blank')
}

const confirmDelete = (publication: any) => {
  confirm?.require({
    message: `Voulez-vous vraiment supprimer "${publication.product?.title}" de eBay ?`,
    header: 'Confirmation de suppression',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    acceptLabel: 'Supprimer',
    rejectLabel: 'Annuler',
    accept: async () => {
      showSuccess('Publication supprimée', 'La publication a été retirée de eBay', 3000)
    }
  })
}

// Policy Methods
const handleCreateShippingPolicy = async (policy: any) => {
  if (!policy.name) {
    showWarn('Validation', 'Le nom est requis', 3000)
    return
  }

  try {
    await ebayStore.createShippingPolicy({
      name: policy.name,
      description: policy.description,
      type: policy.type,
      domesticShipping: {
        service: 'FR_ColipostColissimo',
        cost: policy.type === 'free_shipping' ? 0 : policy.cost,
        handlingTime: policy.handlingTime
      },
      isDefault: policy.isDefault
    })
    showSuccess('Politique créée', 'La politique d\'expédition a été créée', 3000)
    shippingPolicyModal.value = false
  } catch (error) {
    showError('Erreur', 'Impossible de créer la politique', 5000)
  }
}

const handleCreateReturnPolicy = async (policy: any) => {
  if (!policy.name) {
    showWarn('Validation', 'Le nom est requis', 3000)
    return
  }

  try {
    await ebayStore.createReturnPolicy({
      name: policy.name,
      returnsAccepted: policy.returnsAccepted,
      returnPeriod: policy.returnsAccepted ? policy.returnPeriod : 0,
      refundMethod: 'money_back',
      shippingCostPaidBy: policy.shippingCostPaidBy,
      isDefault: policy.isDefault
    })
    showSuccess('Politique créée', 'La politique de retour a été créée', 3000)
    returnPolicyModal.value = false
  } catch (error) {
    showError('Erreur', 'Impossible de créer la politique', 5000)
  }
}

const deletePolicy = async (type: 'shipping' | 'return' | 'payment', policyId: string) => {
  confirm?.require({
    message: 'Voulez-vous vraiment supprimer cette politique ?',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Supprimer',
    rejectLabel: 'Annuler',
    accept: async () => {
      try {
        await ebayStore.deletePolicy(type, policyId)
        showSuccess('Politique supprimée', 'La politique a été supprimée', 3000)
      } catch (error) {
        showError('Erreur', 'Impossible de supprimer la politique', 5000)
      }
    }
  })
}

// External Links
const openStore = () => {
  if (ebayStore.account?.storeUrl) {
    window.open(ebayStore.account.storeUrl, '_blank')
  }
}

const openEbaySettings = () => {
  window.open('https://www.ebay.fr/sh/ovw', '_blank')
}

// Settings Methods
const saveSettings = async () => {
  await ebayStore.saveSyncSettings(syncSettings)
  showSuccess('Paramètres sauvegardés', 'Vos préférences ont été enregistrées', 3000)
}

// Initialize on mount
onMounted(async () => {
  try {
    await ebayStore.checkConnectionStatus()
  } catch (error) {
    console.error('Erreur vérification statut eBay:', error)
  }

  if (ebayStore.isConnected) {
    loading.value = true
    try {
      await Promise.all([
        publicationsStore.fetchPublications(),
        ebayStore.fetchPolicies(),
        ebayStore.fetchStats(),
        ebayProducts.loadProducts()
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
})
</script>

<style scoped>
.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #2563eb);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover::before {
  opacity: 1;
}

.modern-table {
  border-radius: 16px;
  overflow: hidden;
}

.ebay-tabs :deep(.p-tabview-nav) {
  background: transparent;
  border: none;
}

.ebay-tabs :deep(.p-tabview-nav-link) {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: #6b7280;
  transition: all 0.2s ease;
}

.ebay-tabs :deep(.p-tabview-nav-link:not(.p-disabled):focus) {
  box-shadow: none;
}

.ebay-tabs :deep(.p-highlight .p-tabview-nav-link) {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.ebay-tabs :deep(.p-tabview-panels) {
  background: transparent;
  padding: 1.5rem 0;
}
</style>

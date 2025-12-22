<template>
  <div class="p-8">
    <!-- Non connecté: Message de connexion -->
    <Card v-if="!ebayStore.isConnected" class="shadow-lg modern-rounded border-0">
      <template #content>
        <div class="text-center py-12">
          <div class="w-24 h-24 mx-auto mb-6 rounded-full bg-blue-100 flex items-center justify-center">
            <i class="pi pi-link text-blue-500 text-5xl"/>
          </div>
          <h2 class="text-2xl font-bold text-secondary-900 mb-3">Connectez votre compte eBay</h2>
          <p class="text-gray-600 mb-6 max-w-md mx-auto">
            Liez votre compte eBay pour publier vos produits, gérer votre boutique et synchroniser vos ventes automatiquement.
          </p>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto mb-8">
            <div class="p-4 rounded-xl bg-gray-50">
              <i class="pi pi-send text-blue-500 text-2xl mb-2"/>
              <h4 class="font-semibold text-secondary-900 mb-1">Publication facile</h4>
              <p class="text-sm text-gray-600">Publiez vos produits en un clic</p>
            </div>
            <div class="p-4 rounded-xl bg-gray-50">
              <i class="pi pi-sync text-blue-500 text-2xl mb-2"/>
              <h4 class="font-semibold text-secondary-900 mb-1">Sync automatique</h4>
              <p class="text-sm text-gray-600">Stock et prix toujours à jour</p>
            </div>
            <div class="p-4 rounded-xl bg-gray-50">
              <i class="pi pi-chart-line text-blue-500 text-2xl mb-2"/>
              <h4 class="font-semibold text-secondary-900 mb-1">Statistiques</h4>
              <p class="text-sm text-gray-600">Analysez vos performances</p>
            </div>
          </div>

          <Button
            label="Connecter avec eBay"
            icon="pi pi-external-link"
            class="bg-blue-500 hover:bg-blue-600 text-white border-0 font-semibold px-8 py-3"
            :loading="ebayStore.isConnecting"
            @click="handleConnect"
          />

          <p class="text-xs text-gray-500 mt-4">
            En connectant votre compte, vous acceptez les conditions d'utilisation d'eBay
          </p>
        </div>
      </template>
    </Card>

    <!-- Connecté: Contenu principal -->
    <template v-else>
      <!-- Stats Overview -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
              <i class="pi pi-send text-blue-600 text-lg"/>
            </div>
            <span class="text-xs text-green-600 font-medium">+5 ce mois</span>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ ebayStore.stats.activeLis }}</h3>
          <p class="text-xs text-gray-600">Annonces actives</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
              <i class="pi pi-eye text-purple-600 text-lg"/>
            </div>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ formatNumber(ebayStore.stats.totalViews) }}</h3>
          <p class="text-xs text-gray-600">Vues totales</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
              <i class="pi pi-check-circle text-green-600 text-lg"/>
            </div>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ ebayStore.stats.totalSales }}</h3>
          <p class="text-xs text-gray-600">Ventes</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center">
              <i class="pi pi-euro text-primary-600 text-lg"/>
            </div>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ formatCurrency(ebayStore.stats.totalRevenue) }}</h3>
          <p class="text-xs text-gray-600">Chiffre d'affaires</p>
        </div>
      </div>

    </template>

    <!-- Modal: Modifier le prix -->
    <Dialog
      v-model:visible="priceModalVisible"
      modal
      header="Modifier le prix"
      :style="{ width: '400px' }"
    >
      <div v-if="selectedPublication" class="space-y-4">
        <div>
          <p class="font-semibold text-secondary-900 mb-2">{{ selectedPublication.product?.title }}</p>
          <p class="text-sm text-gray-600 mb-4">Prix actuel: {{ formatCurrency(selectedPublication.price) }}</p>
        </div>

        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Nouveau prix</label>
          <InputNumber
            v-model="newPrice"
            mode="currency"
            currency="EUR"
            locale="fr-FR"
            class="w-full"
            :min="0"
            :max-fraction-digits="2"
          />
        </div>
      </div>

      <template #footer>
        <Button
          label="Annuler"
          icon="pi pi-times"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="priceModalVisible = false"
        />
        <Button
          label="Sauvegarder"
          icon="pi pi-check"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          @click="updatePrice"
        />
      </template>
    </Dialog>

    <!-- Modal: Nouvelle politique d'expédition -->
    <Dialog
      v-model:visible="shippingPolicyModal"
      modal
      header="Nouvelle politique d'expédition"
      :style="{ width: '500px' }"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Nom de la politique *</label>
          <InputText v-model="newShippingPolicy.name" class="w-full" placeholder="Ex: Livraison Standard" />
        </div>

        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Description</label>
          <Textarea v-model="newShippingPolicy.description" class="w-full" rows="2" placeholder="Description optionnelle" />
        </div>

        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Type d'expédition</label>
          <Select
            v-model="newShippingPolicy.type"
            :options="shippingTypes"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>

        <div v-if="newShippingPolicy.type !== 'free_shipping'">
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Coût d'expédition (EUR)</label>
          <InputNumber
            v-model="newShippingPolicy.cost"
            mode="currency"
            currency="EUR"
            locale="fr-FR"
            class="w-full"
            :min="0"
          />
        </div>

        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Délai de traitement (jours)</label>
          <InputNumber v-model="newShippingPolicy.handlingTime" class="w-full" :min="0" :max="30" />
        </div>

        <div class="flex items-center gap-2">
          <Checkbox v-model="newShippingPolicy.isDefault" :binary="true" />
          <label class="text-sm text-secondary-900">Définir comme politique par défaut</label>
        </div>
      </div>

      <template #footer>
        <Button
          label="Annuler"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="shippingPolicyModal = false"
        />
        <Button
          label="Créer"
          icon="pi pi-check"
          class="bg-blue-500 hover:bg-blue-600 text-white border-0 font-semibold"
          @click="createShippingPolicy"
        />
      </template>
    </Dialog>

    <!-- Modal: Nouvelle politique de retour -->
    <Dialog
      v-model:visible="returnPolicyModal"
      modal
      header="Nouvelle politique de retour"
      :style="{ width: '500px' }"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Nom de la politique *</label>
          <InputText v-model="newReturnPolicy.name" class="w-full" placeholder="Ex: Retours 30 jours" />
        </div>

        <div class="flex items-center gap-2">
          <Checkbox v-model="newReturnPolicy.returnsAccepted" :binary="true" />
          <label class="text-sm text-secondary-900">Accepter les retours</label>
        </div>

        <div v-if="newReturnPolicy.returnsAccepted">
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Période de retour (jours)</label>
          <InputNumber v-model="newReturnPolicy.returnPeriod" class="w-full" :min="1" :max="60" />
        </div>

        <div v-if="newReturnPolicy.returnsAccepted">
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Frais de retour payés par</label>
          <Select
            v-model="newReturnPolicy.shippingCostPaidBy"
            :options="[{ label: 'Acheteur', value: 'buyer' }, { label: 'Vendeur', value: 'seller' }]"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>

        <div class="flex items-center gap-2">
          <Checkbox v-model="newReturnPolicy.isDefault" :binary="true" />
          <label class="text-sm text-secondary-900">Définir comme politique par défaut</label>
        </div>
      </div>

      <template #footer>
        <Button
          label="Annuler"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="returnPolicyModal = false"
        />
        <Button
          label="Créer"
          icon="pi pi-check"
          class="bg-orange-500 hover:bg-orange-600 text-white border-0 font-semibold"
          @click="createReturnPolicy"
        />
      </template>
    </Dialog>

    <!-- Confirm Dialog -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'

definePageMeta({
  layout: 'dashboard'
})

// SSR-safe initialization: Only call PrimeVue hooks on client-side
const confirm = import.meta.client ? useConfirm() : null
const ebayStore = useEbayStore()
const publicationsStore = usePublicationsStore()
const { showSuccess, showError, showInfo, showWarn } = useAppToast()

// State
const loading = ref(false)
const priceModalVisible = ref(false)
const shippingPolicyModal = ref(false)
const returnPolicyModal = ref(false)
const selectedPublication = ref<any>(null)
const newPrice = ref(0)
const selectedCategoryKeys = ref<Record<string, boolean>>({})

// eBay Products state
const ebayProducts = ref<any[]>([])
const isLoadingProducts = ref(false)
const isImportingProducts = ref(false)
const isEnrichingProducts = ref(false)
const isRefreshingAspects = ref(false)
const syncingProductId = ref<number | null>(null)
const totalProducts = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const totalPages = ref(0)
const productStats = computed(() => {
  return {
    total: totalProducts.value,
    published: ebayProducts.value.filter((p: any) => p.status === 'active').length,
    draft: ebayProducts.value.filter((p: any) => p.status === 'inactive' || !p.status).length,
    outOfStock: ebayProducts.value.filter((p: any) => (p.quantity || 0) === 0).length
  }
})

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

// New policy forms
const newShippingPolicy = reactive({
  name: '',
  description: '',
  type: 'flat_rate' as 'flat_rate' | 'calculated' | 'free_shipping',
  cost: 5.99,
  handlingTime: 1,
  isDefault: false
})

const newReturnPolicy = reactive({
  name: '',
  returnsAccepted: true,
  returnPeriod: 30,
  shippingCostPaidBy: 'buyer' as 'buyer' | 'seller',
  isDefault: false
})

// Options
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

const shippingTypes = [
  { label: 'Forfait', value: 'flat_rate' },
  { label: 'Calculé', value: 'calculated' },
  { label: 'Gratuit', value: 'free_shipping' }
]

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

// Methods
const handleConnect = async () => {
  try {
    // Utiliser l'OAuth réel
    await ebayStore.initiateOAuth()

    showSuccess(
      'Connexion réussie',
      'Votre compte eBay a été connecté avec succès',
      3000
    )
  } catch (error: any) {
    showError(
      'Erreur de connexion',
      error.message || 'Impossible de connecter à eBay',
      5000
    )
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

        showInfo(
          'Déconnecté',
          'Votre compte eBay a été déconnecté',
          3000
        )
      } catch (error) {
        showError(
          'Erreur',
          'Impossible de déconnecter le compte',
          5000
        )
      }
    }
  })
}

const handleSync = async () => {
  try {
    await ebayStore.fetchStats()
    await ebayStore.fetchPolicies()

    showSuccess(
      'Synchronisation terminée',
      'Vos données eBay sont à jour',
      3000
    )
  } catch (error) {
    showError(
      'Erreur',
      'Échec de la synchronisation',
      5000
    )
  }
}

// eBay Products methods
const loadEbayProducts = async (page: number = 1) => {
  isLoadingProducts.value = true
  try {
    const api = useApi()
    const response = await api.get<{
      items: any[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }>(`/api/ebay/products?page=${page}&page_size=${pageSize.value}`)

    ebayProducts.value = response?.items || []
    totalProducts.value = response?.total || 0
    currentPage.value = response?.page || 1
    totalPages.value = response?.total_pages || 0
  } catch (error: any) {
    console.error('Error loading eBay products:', error)
    showError('Erreur', 'Impossible de charger les produits eBay', 5000)
  } finally {
    isLoadingProducts.value = false
  }
}

const onPageChange = (event: any) => {
  // PrimeVue DataTable pagination event
  const newPage = Math.floor(event.first / event.rows) + 1
  pageSize.value = event.rows
  loadEbayProducts(newPage)
}

const importEbayProducts = async () => {
  isImportingProducts.value = true
  try {
    const api = useApi()
    const response = await api.post<{ imported_count: number }>('/api/ebay/products/import')

    showSuccess(
      'Import terminé',
      `${response?.imported_count || 0} produit(s) importé(s)`,
      3000
    )

    // Reload products list
    await loadEbayProducts()
  } catch (error: any) {
    console.error('Error importing eBay products:', error)
    showError('Erreur', error.message || 'Impossible d\'importer les produits', 5000)
  } finally {
    isImportingProducts.value = false
  }
}

const enrichEbayProducts = async () => {
  isEnrichingProducts.value = true
  try {
    const api = useApi()
    const response = await api.post<{
      enriched: number
      errors: number
      remaining: number
    }>('/api/ebay/products/enrich')

    const { enriched, errors, remaining } = response || { enriched: 0, errors: 0, remaining: 0 }

    if (enriched > 0) {
      showSuccess(
        'Enrichissement terminé',
        `${enriched} produit(s) enrichi(s). ${remaining} restant(s).`,
        5000
      )
    } else if (remaining === 0) {
      showInfo('Terminé', 'Tous les produits ont déjà leurs prix', 3000)
    } else {
      showWarn('Avertissement', `${errors} erreur(s). Réessayez pour les ${remaining} restant(s).`, 5000)
    }

    await loadEbayProducts()
  } catch (error: any) {
    console.error('Error enriching eBay products:', error)
    showError('Erreur', error.message || 'Impossible d\'enrichir les produits', 5000)
  } finally {
    isEnrichingProducts.value = false
  }
}

const refreshAspects = async () => {
  isRefreshingAspects.value = true
  try {
    const api = useApi()
    const response = await api.post<{
      updated: number
      errors: number
      remaining: number
    }>('/api/ebay/products/refresh-aspects?batch_size=500')

    const { updated, errors, remaining } = response || { updated: 0, errors: 0, remaining: 0 }

    if (updated > 0) {
      showSuccess(
        'Marques corrigées',
        `${updated} produit(s) mis à jour. ${remaining} restant(s).`,
        5000
      )
    } else if (remaining === 0) {
      showInfo('Terminé', 'Toutes les marques sont déjà renseignées', 3000)
    } else {
      showWarn('Avertissement', `Aucun produit à corriger`, 3000)
    }

    await loadEbayProducts(currentPage.value)
  } catch (error: any) {
    console.error('Error refreshing aspects:', error)
    showError('Erreur', error.message || 'Impossible de corriger les marques', 5000)
  } finally {
    isRefreshingAspects.value = false
  }
}

const syncEbayProduct = async (sku: string) => {
  const product = ebayProducts.value.find((p: any) => p.ebay_sku === sku)
  if (product) {
    syncingProductId.value = product.id
  }

  try {
    const api = useApi()
    await api.post(`/api/ebay/products/${sku}/sync`)

    showSuccess('Synchronisé', 'Produit mis à jour', 3000)
    await loadEbayProducts()
  } catch (error: any) {
    showError('Erreur', 'Impossible de synchroniser le produit', 5000)
  } finally {
    syncingProductId.value = null
  }
}

const openEbayListing = (url: string) => {
  window.open(url, '_blank')
}

const getConditionLabel = (condition: string): string => {
  const labels: Record<string, string> = {
    NEW: 'Neuf',
    LIKE_NEW: 'Comme neuf',
    NEW_OTHER: 'Neuf autre',
    NEW_WITH_DEFECTS: 'Neuf avec défauts',
    MANUFACTURER_REFURBISHED: 'Reconditionné fabricant',
    CERTIFIED_REFURBISHED: 'Certifié reconditionné',
    EXCELLENT_REFURBISHED: 'Excellent reconditionné',
    VERY_GOOD_REFURBISHED: 'Très bon reconditionné',
    GOOD_REFURBISHED: 'Bon reconditionné',
    SELLER_REFURBISHED: 'Reconditionné vendeur',
    USED_EXCELLENT: 'Occasion excellent',
    USED_VERY_GOOD: 'Occasion très bon',
    USED_GOOD: 'Occasion bon',
    USED_ACCEPTABLE: 'Occasion acceptable',
    FOR_PARTS_OR_NOT_WORKING: 'Pour pièces'
  }
  return labels[condition] || condition || 'Non spécifié'
}

const getListingStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    active: 'Actif',
    inactive: 'Inactif',
    ended: 'Terminé',
    sold: 'Vendu',
    ACTIVE: 'Actif',
    DRAFT: 'Brouillon',
    ENDED: 'Terminé',
    OUT_OF_STOCK: 'Hors stock'
  }
  return labels[status] || status || 'Inconnu'
}

const getListingStatusSeverity = (status: string): string => {
  const severities: Record<string, string> = {
    active: 'success',
    inactive: 'warning',
    ended: 'secondary',
    sold: 'info',
    ACTIVE: 'success',
    DRAFT: 'warning',
    ENDED: 'secondary',
    OUT_OF_STOCK: 'danger'
  }
  return severities[status] || 'info'
}

const openStore = () => {
  if (ebayStore.account?.storeUrl) {
    window.open(ebayStore.account.storeUrl, '_blank')
  }
}

const openEbaySettings = () => {
  window.open('https://www.ebay.fr/sh/ovw', '_blank')
}

const openPublication = (publication: any) => {
  const url = `https://www.ebay.fr/itm/${publication.id}`
  window.open(url, '_blank')
}

const editPrice = (publication: any) => {
  selectedPublication.value = publication
  newPrice.value = publication.price
  priceModalVisible.value = true
}

const updatePrice = async () => {
  if (!selectedPublication.value) return

  try {
    selectedPublication.value.price = newPrice.value

    showSuccess(
      'Prix modifié',
      'Le prix a été mis à jour sur eBay',
      3000
    )

    priceModalVisible.value = false
  } catch (error) {
    showError(
      'Erreur',
      'Impossible de modifier le prix',
      5000
    )
  }
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
      showSuccess(
        'Publication supprimée',
        'La publication a été retirée de eBay',
        3000
      )
    }
  })
}

const openPolicyModal = (type: 'shipping' | 'return') => {
  if (type === 'shipping') {
    Object.assign(newShippingPolicy, {
      name: '',
      description: '',
      type: 'flat_rate',
      cost: 5.99,
      handlingTime: 1,
      isDefault: false
    })
    shippingPolicyModal.value = true
  } else {
    Object.assign(newReturnPolicy, {
      name: '',
      returnsAccepted: true,
      returnPeriod: 30,
      shippingCostPaidBy: 'buyer',
      isDefault: false
    })
    returnPolicyModal.value = true
  }
}

const createShippingPolicy = async () => {
  if (!newShippingPolicy.name) {
    showWarn('Validation', 'Le nom est requis', 3000)
    return
  }

  try {
    await ebayStore.createShippingPolicy({
      name: newShippingPolicy.name,
      description: newShippingPolicy.description,
      type: newShippingPolicy.type,
      domesticShipping: {
        service: 'FR_ColipostColissimo',
        cost: newShippingPolicy.type === 'free_shipping' ? 0 : newShippingPolicy.cost,
        handlingTime: newShippingPolicy.handlingTime
      },
      isDefault: newShippingPolicy.isDefault
    })

    showSuccess(
      'Politique créée',
      'La politique d\'expédition a été créée',
      3000
    )

    shippingPolicyModal.value = false
  } catch (error) {
    showError(
      'Erreur',
      'Impossible de créer la politique',
      5000
    )
  }
}

const createReturnPolicy = async () => {
  if (!newReturnPolicy.name) {
    showWarn('Validation', 'Le nom est requis', 3000)
    return
  }

  try {
    await ebayStore.createReturnPolicy({
      name: newReturnPolicy.name,
      returnsAccepted: newReturnPolicy.returnsAccepted,
      returnPeriod: newReturnPolicy.returnsAccepted ? newReturnPolicy.returnPeriod : 0,
      refundMethod: 'money_back',
      shippingCostPaidBy: newReturnPolicy.shippingCostPaidBy,
      isDefault: newReturnPolicy.isDefault
    })

    showSuccess(
      'Politique créée',
      'La politique de retour a été créée',
      3000
    )

    returnPolicyModal.value = false
  } catch (error) {
    showError(
      'Erreur',
      'Impossible de créer la politique',
      5000
    )
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
        showSuccess(
          'Politique supprimée',
          'La politique a été supprimée',
          3000
        )
      } catch (error) {
        showError(
          'Erreur',
          'Impossible de supprimer la politique',
          5000
        )
      }
    }
  })
}

const loadCategories = async () => {
  // TODO: Implémenter fetchCategories() dans le store quand l'API sera prête
  showInfo('Information', 'La synchronisation des catégories sera disponible prochainement', 3000)
}

const saveCategories = () => {
  showSuccess(
    'Catégories sauvegardées',
    'Vos catégories préférées ont été enregistrées',
    3000
  )
}

const saveSettings = async () => {
  await ebayStore.saveSyncSettings(syncSettings)

  showSuccess(
    'Paramètres sauvegardés',
    'Vos préférences ont été enregistrées',
    3000
  )
}

// Helper functions
const getSellerLevelSeverity = () => {
  const level = ebayStore.account?.sellerLevel
  if (level === 'top_rated') return 'success'
  if (level === 'above_standard') return 'info'
  if (level === 'standard') return 'warning'
  return 'danger'
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    active: 'Actif',
    published: 'Publié',
    sold: 'Vendu',
    paused: 'En pause',
    expired: 'Expiré',
    draft: 'Brouillon'
  }
  return labels[status] || status
}

const getStatusSeverity = (status: string): string => {
  const severities: Record<string, string> = {
    active: 'success',
    published: 'success',
    sold: 'info',
    paused: 'warning',
    expired: 'danger',
    draft: 'secondary'
  }
  return severities[status] || 'secondary'
}

const getShippingTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    flat_rate: 'Forfait',
    calculated: 'Calculé',
    free_shipping: 'Gratuit',
    FLAT_RATE: 'Forfait',
    CALCULATED: 'Calculé',
    FREE: 'Gratuit'
  }
  return labels[type] || type || 'Standard'
}

const getShippingCost = (policy: any): string => {
  // Check shippingOptions array (eBay API format)
  if (policy.shippingOptions && policy.shippingOptions.length > 0) {
    const option = policy.shippingOptions[0]
    if (option.costType === 'FREE' || option.shippingCost?.value === '0') {
      return 'Gratuit'
    }
    if (option.shippingCost?.value) {
      return formatCurrency(parseFloat(option.shippingCost.value))
    }
  }
  // Fallback to domesticShipping (old format)
  if (policy.domesticShipping?.cost) {
    return formatCurrency(policy.domesticShipping.cost)
  }
  return '-'
}

const getShippingTypeFromPolicy = (policy: any): string => {
  if (policy.shippingOptions && policy.shippingOptions.length > 0) {
    const option = policy.shippingOptions[0]
    if (option.costType === 'FREE') return 'Gratuit'
    if (option.costType === 'FLAT_RATE') return 'Forfait'
    if (option.costType === 'CALCULATED') return 'Calculé'
    return option.costType || 'Standard'
  }
  return policy.type ? getShippingTypeLabel(policy.type) : 'Standard'
}

const isFreeshipping = (policy: any): boolean => {
  if (policy.shippingOptions && policy.shippingOptions.length > 0) {
    return policy.shippingOptions[0].costType === 'FREE'
  }
  return policy.type === 'free_shipping'
}

const getPaymentMethodLabel = (method: string): string => {
  const labels: Record<string, string> = {
    paypal: 'PayPal',
    credit_card: 'Carte',
    bank_transfer: 'Virement'
  }
  return labels[method] || method
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(value || 0)
}

const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('fr-FR').format(value || 0)
}

const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

const formatRelativeTime = (dateStr: string): string => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return 'À l\'instant'
  if (minutes < 60) return `Il y a ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `Il y a ${hours}h`
  const days = Math.floor(hours / 24)
  return `Il y a ${days}j`
}

const formatDateTime = (dateStr: string): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatProgramName = (programType: string): string => {
  const names: Record<string, string> = {
    'SELLING_POLICY_MANAGEMENT': 'Gestion Politiques',
    'PROMOTED_LISTINGS_STANDARD': 'Annonces sponsorisées',
    'OFFSITE_ADS': 'Publicités hors site',
    'OUT_OF_STOCK_CONTROL': 'Contrôle stock'
  }
  return names[programType] || programType.replace(/_/g, ' ')
}

// Initialize on mount
onMounted(async () => {
  // Vérifier le statut de connexion au chargement
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
        loadEbayProducts()
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

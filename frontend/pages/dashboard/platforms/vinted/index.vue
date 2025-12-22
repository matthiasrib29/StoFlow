<template>
  <div class="p-8">
    <!-- Contenu Vue d'ensemble -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <!-- Stat Cards -->
          <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-xl bg-cyan-100 flex items-center justify-center">
                <i class="pi pi-send text-cyan-600 text-xl"/>
              </div>
            </div>
            <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ stats.activePublications }}</h3>
            <p class="text-sm text-gray-600">Publications actives</p>
          </div>

          <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
                <i class="pi pi-eye text-primary-600 text-xl"/>
              </div>
            </div>
            <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ stats.totalViews }}</h3>
            <p class="text-sm text-gray-600">Vues totales</p>
          </div>

          <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-xl bg-red-100 flex items-center justify-center">
                <i class="pi pi-heart-fill text-red-500 text-xl"/>
              </div>
            </div>
            <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ stats.totalFavourites }}</h3>
            <p class="text-sm text-gray-600">Favoris</p>
          </div>

          <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center">
                <i class="pi pi-euro text-green-600 text-xl"/>
              </div>
            </div>
            <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ formatCurrency(stats.potentialRevenue) }}</h3>
            <p class="text-sm text-gray-600">CA potentiel</p>
          </div>
        </div>

        <!-- Infos Connexion -->
        <Card v-if="isConnected" class="shadow-sm modern-rounded border border-gray-100 mb-6">
          <template #content>
            <h3 class="text-lg font-bold text-secondary-900 mb-4">Informations de connexion</h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-gray-600">User ID</span>
                <span class="font-semibold text-secondary-900">{{ connectionInfo.userId || '-' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-600">Username</span>
                <span class="font-semibold text-secondary-900">{{ connectionInfo.username || '-' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-gray-600">Dernière synchronisation</span>
                <span class="font-semibold text-secondary-900">{{ connectionInfo.lastSync }}</span>
              </div>
            </div>

            <!-- Bouton Sync Produits -->
            <div class="mt-6 pt-4 border-t border-gray-200">
              <Button
                label="Synchroniser les produits Vinted"
                icon="pi pi-sync"
                class="w-full bg-cyan-500 hover:bg-cyan-600 text-white border-0 font-semibold"
                :loading="syncLoading"
                :disabled="syncLoading"
                @click="handleSyncProducts"
              />
              <p class="text-xs text-gray-500 mt-2 text-center">
                Récupère tous vos produits depuis votre garde-robe Vinted
              </p>
            </div>
          </template>
        </Card>

        <!-- Résultat de la sync (JSON brut) -->
        <Card v-if="rawSyncResult" class="shadow-sm modern-rounded border border-gray-100 mb-6">
          <template #content>
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-bold text-secondary-900">
                <i class="pi pi-code mr-2"/>
                Résultat brut de la synchronisation
              </h3>
              <div class="flex gap-2">
                <Button
                  label="Copier"
                  icon="pi pi-copy"
                  class="bg-gray-100 hover:bg-gray-200 text-secondary-900 border-0"
                  size="small"
                  @click="copyRawResult"
                />
                <Button
                  label="Fermer"
                  icon="pi pi-times"
                  class="bg-red-100 hover:bg-red-200 text-red-700 border-0"
                  size="small"
                  @click="rawSyncResult = null"
                />
              </div>
            </div>

            <!-- Statistiques -->
            <div v-if="rawSyncResult.stats" class="grid grid-cols-5 gap-3 mb-4">
              <div class="bg-blue-50 rounded-lg p-3 text-center">
                <div class="text-2xl font-bold text-blue-600">{{ rawSyncResult.stats.created || 0 }}</div>
                <div class="text-xs text-blue-700">Créés</div>
              </div>
              <div class="bg-green-50 rounded-lg p-3 text-center">
                <div class="text-2xl font-bold text-green-600">{{ rawSyncResult.stats.updated || rawSyncResult.stats.synced || 0 }}</div>
                <div class="text-xs text-green-700">Mis à jour</div>
              </div>
              <div class="bg-purple-50 rounded-lg p-3 text-center">
                <div class="text-2xl font-bold text-purple-600">{{ rawSyncResult.stats.enriched || 0 }}</div>
                <div class="text-xs text-purple-700">Enrichis</div>
              </div>
              <div class="bg-red-50 rounded-lg p-3 text-center">
                <div class="text-2xl font-bold text-red-600">{{ rawSyncResult.stats.deleted || 0 }}</div>
                <div class="text-xs text-red-700">Supprimés</div>
              </div>
              <div class="bg-yellow-50 rounded-lg p-3 text-center">
                <div class="text-2xl font-bold text-yellow-600">{{ (rawSyncResult.stats.errors || 0) + (rawSyncResult.stats.enrichment_errors || 0) }}</div>
                <div class="text-xs text-yellow-700">Erreurs</div>
              </div>
            </div>

            <!-- JSON brut -->
            <div class="bg-gray-900 rounded-lg p-4 max-h-[500px] overflow-auto">
              <pre class="text-xs text-green-400 whitespace-pre-wrap break-words font-mono">{{ JSON.stringify(rawSyncResult, null, 2) }}</pre>
            </div>
          </template>
        </Card>

        <!-- Section JSON Brut des Produits Synchronisés -->
        <Card v-if="isConnected && syncedProducts.length > 0" class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-bold text-secondary-900">Produits Synchronisés (JSON Brut)</h3>
              <div class="flex gap-2">
                <Button
                  label="Copier JSON"
                  icon="pi pi-copy"
                  class="bg-gray-100 hover:bg-gray-200 text-secondary-900 border-0"
                  size="small"
                  @click="copyJsonToClipboard"
                />
                <Button
                  label="Effacer"
                  icon="pi pi-times"
                  class="bg-red-100 hover:bg-red-200 text-red-700 border-0"
                  size="small"
                  @click="syncedProducts = []"
                />
              </div>
            </div>
            <div class="bg-gray-50 rounded-lg p-4 max-h-96 overflow-auto">
              <pre class="text-xs text-gray-800 whitespace-pre-wrap break-words">{{ JSON.stringify(syncedProducts, null, 2) }}</pre>
            </div>
            <div class="mt-3 text-sm text-gray-600">
              <i class="pi pi-info-circle mr-2"/>
              {{ syncedProducts.length }} produit(s) récupéré(s) depuis Vinted
            </div>
          </template>
        </Card>

        <!-- Message si non connecté -->
        <Card v-else class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="text-center py-8">
              <i class="pi pi-link text-gray-300 text-6xl mb-4"/>
              <h3 class="text-xl font-bold text-secondary-900 mb-2">Connectez votre compte Vinted</h3>
              <p class="text-gray-600 mb-6">Commencez à publier vos produits sur Vinted en un clic</p>
              <Button
                label="Connecter maintenant"
                icon="pi pi-link"
                class="bg-cyan-500 hover:bg-cyan-600 text-white border-0 font-semibold"
                @click="handleConnect"
              />
            </div>
          </template>
        </Card>
    <!-- Fin Vue d'ensemble - Le reste des onglets est maintenant sur des pages séparées -->

    <!-- Modal: Modifier le prix -->
    <Dialog
      v-model:visible="priceModalVisible"
      modal
      header="Modifier le prix"
      :style="{ width: '400px' }"
    >
      <div v-if="selectedPublication" class="space-y-4">
        <div>
          <p class="font-semibold text-secondary-900 mb-2">{{ selectedPublication.product.title }}</p>
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

    <!-- Modal: Produits synchronisés -->
    <Dialog
      v-model:visible="syncModalVisible"
      modal
      header="Produits synchronisés depuis Vinted"
      :style="{ width: '900px' }"
      :maximizable="true"
    >
      <div v-if="syncedProducts.length > 0">
        <p class="text-gray-600 mb-4">
          {{ syncedProducts.length }} produit(s) trouvé(s) sur votre compte Vinted
        </p>

        <DataTable
          :value="syncedProducts"
          :paginator="true"
          :rows="5"
          class="modern-table"
          striped-rows
        >
          <Column field="title" header="Titre" sortable>
            <template #body="{ data }">
              <div class="flex items-center gap-3">
                <img
                  v-if="data.photo?.url"
                  :src="data.photo.url"
                  :alt="data.title"
                  class="w-12 h-12 rounded-lg object-cover"
                >
                <div v-else class="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center">
                  <i class="pi pi-image text-gray-400"/>
                </div>
                <div>
                  <p class="font-semibold text-secondary-900">{{ data.title }}</p>
                  <p class="text-xs text-gray-500">ID: {{ data.id }}</p>
                </div>
              </div>
            </template>
          </Column>

          <Column field="price" header="Prix" sortable>
            <template #body="{ data }">
              <span class="font-bold text-secondary-900">{{ formatCurrency(data.price || 0) }}</span>
            </template>
          </Column>

          <Column field="brand" header="Marque" sortable>
            <template #body="{ data }">
              <span class="text-sm">{{ data.brand || '-' }}</span>
            </template>
          </Column>

          <Column field="size" header="Taille" sortable>
            <template #body="{ data }">
              <span class="text-sm">{{ data.size || '-' }}</span>
            </template>
          </Column>

          <Column field="view_count" header="Vues" sortable>
            <template #body="{ data }">
              <div class="flex items-center gap-2">
                <i class="pi pi-eye text-gray-400 text-sm"/>
                <span>{{ data.view_count || 0 }}</span>
              </div>
            </template>
          </Column>

          <Column field="favourite_count" header="Favoris" sortable>
            <template #body="{ data }">
              <div class="flex items-center gap-2">
                <i class="pi pi-heart text-gray-400 text-sm"/>
                <span>{{ data.favourite_count || 0 }}</span>
              </div>
            </template>
          </Column>
        </DataTable>
      </div>

      <div v-else class="text-center py-8">
        <i class="pi pi-inbox text-gray-300 text-5xl mb-3"/>
        <p class="text-gray-600">Aucun produit trouvé</p>
      </div>

      <template #footer>
        <Button
          label="Fermer"
          icon="pi pi-times"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="syncModalVisible = false"
        />
      </template>
    </Dialog>

    <!-- Confirm Dialog -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { useVintedMessagesStore } from '~/stores/vintedMessages'

definePageMeta({
  layout: 'dashboard'
})

// SSR-safe initialization: Only call PrimeVue hooks on client-side
const confirm = import.meta.client ? useConfirm() : null
const toast = import.meta.client ? useToast() : null
const publicationsStore = usePublicationsStore()
const messagesStore = useVintedMessagesStore()
const { get, post, put, del } = useApi()

// Messages unread count (reactive)
const messagesUnreadCount = computed(() => messagesStore.unreadCount)

// State
const activeTab = ref('0')
const isConnected = ref(false)
const loading = ref(false)
const priceModalVisible = ref(false)
const selectedPublication = ref<any>(null)
const newPrice = ref(0)

// Sync states
const syncModalVisible = ref(false)
const syncLoading = ref(false)
const syncedProducts = ref<any[]>([])
const rawSyncResult = ref<any>(null)

// Vinted products from DB
const vintedProducts = ref<any[]>([])
const vintedProductsLoading = ref(false)
const vintedProductsTotal = ref(0)

// Vinted orders/sales
const orders = ref<any[]>([])
const ordersLoading = ref(false)

// Month-specific sync (default to previous month)
const initMonth = () => {
  const now = new Date()
  const month = now.getMonth() // 0-indexed, so this is previous month
  const year = month === 0 ? now.getFullYear() - 1 : now.getFullYear()
  return { month: month === 0 ? 12 : month, year }
}
const { month: initSelectedMonth, year: initSelectedYear } = initMonth()
const selectedYear = ref(initSelectedYear)
const selectedMonth = ref(initSelectedMonth)
const monthSyncResult = ref<any>(null)

// Stats (loaded from API)
const stats = ref({
  activePublications: 0,
  totalViews: 0,
  totalFavourites: 0,
  potentialRevenue: 0,
  totalProducts: 0
})

// Connection info
const connectionInfo = ref({
  userId: null as number | null,
  username: null as string | null,
  lastSync: null as string | null
})

// Settings
const settings = ref({
  autoSync: true,
  saleNotifications: true,
  autoPricing: false
})

// Publications (mock data - à remplacer par vraies données du store)
const publications = computed(() => {
  return publicationsStore.publications
    .filter((p: any) => p.platform === 'vinted')
    .map((p: any) => ({
      ...p,
      product: {
        id: p.product_id || p.id,
        title: p.product_title || p.title || 'Produit sans titre',
        image_url: p.image_url || p.photo?.url || null
      },
      views: Math.floor(Math.random() * 100),
      published_at: p.published_at || new Date().toISOString()
    }))
})

// Computed
const platformData = computed(() => {
  return publicationsStore.integrations.find((i: any) => i.platform === 'vinted')
})

// Month/Year options for sync selector
const currentDate = new Date()
const currentYear = currentDate.getFullYear()
const currentMonth = currentDate.getMonth() + 1

const allMonths = [
  { label: 'Janvier', value: 1 },
  { label: 'Février', value: 2 },
  { label: 'Mars', value: 3 },
  { label: 'Avril', value: 4 },
  { label: 'Mai', value: 5 },
  { label: 'Juin', value: 6 },
  { label: 'Juillet', value: 7 },
  { label: 'Août', value: 8 },
  { label: 'Septembre', value: 9 },
  { label: 'Octobre', value: 10 },
  { label: 'Novembre', value: 11 },
  { label: 'Décembre', value: 12 }
]

// Disable current month if current year is selected
const monthOptions = computed(() => {
  return allMonths.map(month => ({
    ...month,
    disabled: selectedYear.value === currentYear && month.value >= currentMonth
  }))
})

const yearOptions = computed(() => {
  const years = []
  for (let y = currentYear; y >= 2020; y--) {
    years.push({ label: y.toString(), value: y })
  }
  return years
})

// Auto-adjust month if user selects current year and current/future month is selected
watch(selectedYear, (newYear) => {
  if (newYear === currentYear && selectedMonth.value >= currentMonth) {
    // Select previous month
    selectedMonth.value = currentMonth - 1 > 0 ? currentMonth - 1 : 12
    if (selectedMonth.value === 12 && newYear === currentYear) {
      selectedYear.value = currentYear - 1
    }
  }
})

// Computed for orders
const totalOrdersRevenue = computed(() => {
  return orders.value.reduce((sum, order) => sum + (order.price_numeric || 0), 0)
})

const averageOrderValue = computed(() => {
  if (orders.value.length === 0) return 0
  return totalOrdersRevenue.value / orders.value.length
})

// Computed for Expéditions tab
const pendingShipments = computed(() => {
  return orders.value.filter(order => order.status === 'pending' || order.status === 'awaiting_shipment')
})

const shippedOrders = computed(() => {
  return orders.value.filter(order => order.status === 'shipped' || order.status === 'in_transit')
})

const deliveredOrders = computed(() => {
  return orders.value.filter(order => order.status === 'completed' || order.status === 'delivered')
})

// Computed for Analytiques tab
const soldProductsCount = computed(() => {
  return vintedProducts.value.filter(p => p.status === 'sold').length
})

const conversionRate = computed(() => {
  if (stats.value.totalProducts === 0) return 0
  return ((soldProductsCount.value / stats.value.totalProducts) * 100).toFixed(1)
})

const viewToFavRate = computed(() => {
  if (stats.value.totalViews === 0) return 0
  return ((stats.value.totalFavourites / stats.value.totalViews) * 100).toFixed(1)
})

const averagePrice = computed(() => {
  if (vintedProducts.value.length === 0) return 0
  const total = vintedProducts.value.reduce((sum, p) => sum + (p.price || 0), 0)
  return total / vintedProducts.value.length
})

const averageViewsPerProduct = computed(() => {
  if (vintedProducts.value.length === 0) return 0
  return Math.round(stats.value.totalViews / vintedProducts.value.length)
})

const topViewedProducts = computed(() => {
  return [...vintedProducts.value]
    .sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
    .slice(0, 5)
})

const topFavoritedProducts = computed(() => {
  return [...vintedProducts.value]
    .sort((a, b) => (b.favourite_count || 0) - (a.favourite_count || 0))
    .slice(0, 5)
})

const inactiveProducts = computed(() => {
  return vintedProducts.value.filter(p => (p.view_count || 0) === 0 && p.status === 'published')
})

// Watch platform data
watch(() => platformData.value?.is_connected, (connected) => {
  if (connected !== undefined) {
    isConnected.value = connected
  }
}, { immediate: true })

// Stats are now fetched directly from /api/vinted/stats (no watch needed)

// Methods
const handleConnect = async () => {
  try {
    loading.value = true

    toast?.add({
      severity: 'info',
      summary: 'Vérification en cours',
      detail: 'Connexion au plugin... Assurez-vous qu\'un onglet Vinted est ouvert.',
      life: 10000
    })

    // Appeler le nouvel endpoint qui crée une task et attend le résultat du plugin
    const response = await post<{
      connected: boolean;
      vinted_user_id: number | null;
      login: string | null;
      message: string;
    }>('/api/vinted/check-connection')

    if (response.connected) {
      connectionInfo.value.userId = response.vinted_user_id
      connectionInfo.value.username = response.login || 'user@vinted.com'
      connectionInfo.value.lastSync = 'À l\'instant'
      isConnected.value = true

      // Marquer comme connecté dans le store
      await publicationsStore.connectIntegration('vinted')

      toast?.add({
        severity: 'success',
        summary: 'Connecté',
        detail: response.message || `Connecté en tant que ${response.login}`,
        life: 5000
      })

      // Rafraîchir les données
      await fetchVintedProducts()
      await fetchVintedStats()
    } else {
      toast?.add({
        severity: 'warn',
        summary: 'Non connecté',
        detail: response.message || 'Connectez-vous à Vinted et réessayez',
        life: 5000
      })
    }

  } catch (error: any) {
    // Gérer le timeout (408)
    if (error.statusCode === 408 || error.message?.includes('timeout')) {
      toast?.add({
        severity: 'warn',
        summary: 'Plugin non répondu',
        detail: 'Vérifiez que le plugin Stoflow est actif et qu\'un onglet Vinted.fr est ouvert',
        life: 8000
      })
    } else {
      toast?.add({
        severity: 'error',
        summary: 'Erreur de connexion',
        detail: error.message || 'Impossible de vérifier la connexion à Vinted',
        life: 5000
      })
    }
  } finally {
    loading.value = false
  }
}

const handleDisconnect = () => {
  confirm?.require({
    message: 'Voulez-vous vraiment déconnecter votre compte Vinted ?',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Oui, déconnecter',
    rejectLabel: 'Annuler',
    accept: async () => {
      try {
        await publicationsStore.disconnectIntegration('vinted')
        toast?.add({
          severity: 'info',
          summary: 'Déconnecté',
          detail: 'Votre compte Vinted a été déconnecté',
          life: 3000
        })
      } catch (error) {
        toast?.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Impossible de déconnecter le compte',
          life: 5000
        })
      }
    }
  })
}

const handleSync = async () => {
  try {
    syncLoading.value = true
    syncedProducts.value = []

    toast?.add({
      severity: 'info',
      summary: 'Synchronisation',
      detail: 'Récupération de vos produits Vinted...',
      life: 3000
    })

    // Appel synchrone à la nouvelle route /products/sync
    const syncResponse = await post<{
      created: number;
      updated: number;
      enriched: number;
      enrichment_errors: number;
      errors: number;
    }>('/api/vinted/products/sync')

    // Récupérer ensuite la liste des produits
    const productsResponse = await get<{
      products: any[];
      total: number;
    }>('/api/vinted/products?limit=100')

    syncedProducts.value = productsResponse.products || []
    connectionInfo.value.lastSync = 'À l\'instant'

    // Rafraîchir la liste des publications
    await publicationsStore.fetchPublications()

    const totalSynced = (syncResponse.created || 0) + (syncResponse.updated || 0)
    const enrichedCount = syncResponse.enriched || 0
    toast?.add({
      severity: 'success',
      summary: 'Synchronisé',
      detail: `${totalSynced} produit(s) synchronisé(s)${enrichedCount > 0 ? `, ${enrichedCount} enrichi(s)` : ''}`,
      life: 5000
    })

    // Ouvrir le modal avec les produits
    if (syncedProducts.value.length > 0) {
      syncModalVisible.value = true
    }

  } catch (error: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur de synchronisation',
      detail: error.message || 'Échec de la synchronisation',
      life: 5000
    })
  } finally {
    syncLoading.value = false
  }
}

// Nouvelle fonction pour sync et afficher le résultat brut
const handleSyncProducts = async () => {
  try {
    syncLoading.value = true
    rawSyncResult.value = null

    toast?.add({
      severity: 'info',
      summary: 'Synchronisation en cours',
      detail: 'Récupération des produits depuis Vinted via le plugin...',
      life: 5000
    })

    // 1. Appeler la sync
    const syncResponse = await post<any>('/api/vinted/products/sync')

    // 2. Récupérer les produits de la BDD
    const productsResponse = await get<any>('/api/vinted/products?limit=100')

    // 3. Stocker le résultat brut complet
    rawSyncResult.value = {
      timestamp: new Date().toISOString(),
      stats: {
        created: syncResponse.created || 0,
        updated: syncResponse.updated || 0,
        enriched: syncResponse.enriched || 0,
        enrichment_errors: syncResponse.enrichment_errors || 0,
        errors: syncResponse.errors || 0
      },
      syncResponse,
      products: productsResponse.products || [],
      totalProducts: productsResponse.total || 0
    }

    connectionInfo.value.lastSync = 'À l\'instant'

    const totalProcessed = (syncResponse.created || 0) + (syncResponse.updated || 0)
    const enriched = syncResponse.enriched || 0
    toast?.add({
      severity: 'success',
      summary: 'Synchronisation terminée',
      detail: `${totalProcessed} produit(s) synchronisé(s)${enriched > 0 ? `, ${enriched} enrichi(s)` : ''}`,
      life: 5000
    })

  } catch (error: any) {
    // Afficher l'erreur dans le résultat brut aussi
    rawSyncResult.value = {
      timestamp: new Date().toISOString(),
      error: true,
      message: error.message || 'Erreur inconnue',
      details: error
    }

    toast?.add({
      severity: 'error',
      summary: 'Erreur de synchronisation',
      detail: error.message || 'Échec de la synchronisation',
      life: 5000
    })
  } finally {
    syncLoading.value = false
  }
}

const copyRawResult = async () => {
  try {
    await navigator.clipboard.writeText(JSON.stringify(rawSyncResult.value, null, 2))
    toast?.add({
      severity: 'success',
      summary: 'Copié',
      detail: 'Résultat JSON copié dans le presse-papiers',
      life: 2000
    })
  } catch (error) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de copier',
      life: 2000
    })
  }
}

const openPublication = (publication: any) => {
  // Mock URL - à remplacer par vraie URL de la plateforme
  const url = `https://www.vinted.fr/items/${publication.id}`
  window.open(url, '_blank')

  toast?.add({
    severity: 'info',
    summary: 'Ouverture',
    detail: 'Ouverture de la publication sur Vinted',
    life: 2000
  })
}

// Open Vinted product on vinted.fr
const openVintedProduct = (product: any) => {
  if (product.url) {
    window.open(product.url, '_blank')
  } else if (product.vinted_id) {
    window.open(`https://www.vinted.fr/items/${product.vinted_id}`, '_blank')
  }
}


// Delete Vinted product
const confirmDeleteVinted = (product: any) => {
  confirm?.require({
    message: `Voulez-vous vraiment supprimer "${product.title || 'ce produit'}" de la liste ?`,
    header: 'Confirmation de suppression',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    acceptLabel: 'Supprimer',
    rejectLabel: 'Annuler',
    accept: async () => {
      try {
        toast?.add({
          severity: 'info',
          summary: 'Suppression en cours',
          detail: 'Suppression du produit de la liste...',
          life: 3000
        })

        const response = await del<{ success: boolean; vinted_id: number }>(
          `/api/vinted/products/${product.vinted_id}`
        )

        if (!response.success) {
          throw new Error('Échec de la suppression')
        }

        toast?.add({
          severity: 'success',
          summary: 'Produit supprimé',
          detail: 'Le produit a été supprimé de la liste',
          life: 3000
        })

        // Refresh list
        await fetchVintedProducts()

      } catch (error: any) {
        toast?.add({
          severity: 'error',
          summary: 'Erreur',
          detail: error.message || 'Impossible de supprimer le produit',
          life: 5000
        })
      }
    }
  })
}

const editPrice = (publication: any) => {
  selectedPublication.value = publication
  newPrice.value = publication.price
  priceModalVisible.value = true
}

const updatePrice = async () => {
  if (!selectedPublication.value) return

  try {
    const productId = selectedPublication.value.product_id || selectedPublication.value.id

    toast?.add({
      severity: 'info',
      summary: 'Modification du prix',
      detail: 'Mise à jour du prix sur Vinted...',
      life: 3000
    })

    // Appeler la nouvelle route PUT /products/{id}
    const response = await put<{ success: boolean; product_id: number }>(
      `/api/vinted/products/${productId}`
    )

    if (!response.success) {
      throw new Error('Échec de la mise à jour')
    }

    // Mise à jour locale immédiate (optimistic update)
    selectedPublication.value.price = newPrice.value

    toast?.add({
      severity: 'success',
      summary: 'Prix modifié',
      detail: 'Le prix a été mis à jour sur Vinted',
      life: 3000
    })

    priceModalVisible.value = false

    // Rafraîchir la liste
    await publicationsStore.fetchPublications()

  } catch (error: any) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: error.message || 'Impossible de modifier le prix',
      life: 5000
    })
  }
}

const confirmDelete = (publication: any) => {
  confirm?.require({
    message: `Voulez-vous vraiment supprimer "${publication.product.title}" de Vinted ?`,
    header: 'Confirmation de suppression',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    acceptLabel: 'Supprimer',
    rejectLabel: 'Annuler',
    accept: async () => {
      try {
        const productId = publication.product_id || publication.id

        toast?.add({
          severity: 'info',
          summary: 'Suppression en cours',
          detail: 'Suppression du produit sur Vinted...',
          life: 3000
        })

        // Appeler la nouvelle route DELETE /products/{id}
        const response = await del<{ success: boolean; product_id: number }>(
          `/api/vinted/products/${productId}`
        )

        if (!response.success) {
          throw new Error('Échec de la suppression')
        }

        toast?.add({
          severity: 'success',
          summary: 'Publication supprimée',
          detail: 'Le produit a été supprimé de Vinted',
          life: 3000
        })

        // Rafraîchir la liste
        await publicationsStore.fetchPublications()

      } catch (error: any) {
        toast?.add({
          severity: 'error',
          summary: 'Erreur',
          detail: error.message || 'Impossible de supprimer la publication',
          life: 5000
        })
      }
    }
  })
}

const saveSettings = () => {
  toast?.add({
    severity: 'success',
    summary: 'Paramètres sauvegardés',
    detail: 'Vos préférences ont été enregistrées',
    life: 3000
  })
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    active: 'Actif',
    published: 'Publié',
    sold: 'Vendu',
    paused: 'En pause',
    expired: 'Expiré',
    pending: 'En attente',
    deleted: 'Supprimé'
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
    pending: 'secondary',
    deleted: 'danger'
  }
  return severities[status] || 'secondary'
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(value)
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

const copyJsonToClipboard = async () => {
  try {
    const jsonString = JSON.stringify(syncedProducts.value, null, 2)
    await navigator.clipboard.writeText(jsonString)

    toast?.add({
      severity: 'success',
      summary: 'Copié',
      detail: 'Le JSON a été copié dans le presse-papier',
      life: 2000
    })
  } catch (error) {
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de copier le JSON',
      life: 3000
    })
  }
}

// Fetch connection status - nouvelle route simplifiée /status
const fetchConnectionStatus = async () => {
  try {
    const response = await get<{
      is_connected: boolean;
      vinted_user_id: number | null;
      login: string | null;
      last_sync: string | null;
    }>('/api/vinted/status')

    isConnected.value = response.is_connected
    if (response.is_connected) {
      connectionInfo.value = {
        userId: response.vinted_user_id,
        username: response.login,
        lastSync: response.last_sync ? formatDate(response.last_sync) : 'Jamais'
      }
    }
  } catch (error) {
    console.error('Erreur récupération statut:', error)
    isConnected.value = false
  }
}

// Fetch Vinted products from database
const fetchVintedProducts = async () => {
  try {
    vintedProductsLoading.value = true
    const response = await get<{
      products: any[];
      total: number;
      limit: number;
      offset: number;
    }>('/api/vinted/products?limit=100')

    vintedProducts.value = response.products || []
    vintedProductsTotal.value = response.total || 0

    // Stats are now fetched from /api/vinted/stats

  } catch (error) {
    console.error('Erreur récupération produits Vinted:', error)
    vintedProducts.value = []
  } finally {
    vintedProductsLoading.value = false
  }
}

// Note: fetchDescriptionsBatch removed - descriptions are now enriched automatically during sync

// Fetch Vinted stats from API
const fetchVintedStats = async () => {
  try {
    const response = await get<{
      activePublications: number
      totalViews: number
      totalFavourites: number
      potentialRevenue: number
      totalProducts: number
    }>('/api/vinted/stats')

    stats.value = {
      activePublications: response.activePublications || 0,
      totalViews: response.totalViews || 0,
      totalFavourites: response.totalFavourites || 0,
      potentialRevenue: response.potentialRevenue || 0,
      totalProducts: response.totalProducts || 0
    }
  } catch (error) {
    console.error('Erreur récupération stats Vinted:', error)
  }
}

// Fetch Vinted orders from API
const fetchOrders = async () => {
  try {
    ordersLoading.value = true
    const response = await get<{
      orders: any[]
      total: number
    }>('/api/vinted/orders?limit=100')

    orders.value = response.orders || []
  } catch (error) {
    console.error('Erreur récupération commandes Vinted:', error)
    orders.value = []
  } finally {
    ordersLoading.value = false
  }
}

// Sync orders from Vinted API
const handleSyncOrders = async () => {
  try {
    ordersLoading.value = true
    monthSyncResult.value = null

    toast?.add({
      severity: 'info',
      summary: 'Synchronisation',
      detail: 'Récupération des ventes depuis Vinted...',
      life: 3000
    })

    const response = await post<{
      synced: number
      errors: number
    }>('/api/vinted/orders/sync')

    toast?.add({
      severity: 'success',
      summary: 'Synchronisation terminée',
      detail: `${response.synced} ventes synchronisées`,
      life: 3000
    })

    // Recharger les commandes
    await fetchOrders()

  } catch (error: any) {
    console.error('Erreur sync commandes:', error)
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: error.message || 'Erreur lors de la synchronisation des ventes',
      life: 5000
    })
  } finally {
    ordersLoading.value = false
  }
}

// Sync orders for a specific month
const handleSyncOrdersByMonth = async () => {
  try {
    ordersLoading.value = true
    monthSyncResult.value = null

    const monthLabel = monthOptions.value.find(m => m.value === selectedMonth.value)?.label || selectedMonth.value

    toast?.add({
      severity: 'info',
      summary: 'Synchronisation',
      detail: `Récupération des ventes de ${monthLabel} ${selectedYear.value}...`,
      life: 5000
    })

    const response = await post<{
      synced: number
      duplicates: number
      errors: number
      month: string
      last_error?: string
    }>(`/api/vinted/orders/sync/month?year=${selectedYear.value}&month=${selectedMonth.value}`)

    monthSyncResult.value = response

    toast?.add({
      severity: 'success',
      summary: 'Synchronisation terminée',
      detail: `${response.synced} nouvelles ventes, ${response.duplicates} doublons`,
      life: 5000
    })

    // Recharger les commandes
    await fetchOrders()

  } catch (error: any) {
    console.error('Erreur sync commandes par mois:', error)
    monthSyncResult.value = {
      error: true,
      message: error.message || 'Erreur lors de la synchronisation'
    }
    toast?.add({
      severity: 'error',
      summary: 'Erreur',
      detail: error.message || 'Erreur lors de la synchronisation des ventes',
      life: 5000
    })
  } finally {
    ordersLoading.value = false
  }
}

// Order status helpers
const getOrderStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    'completed': 'Terminée',
    'shipped': 'Expédiée',
    'pending': 'En attente',
    'cancelled': 'Annulée'
  }
  return labels[status] || status
}

const getOrderStatusSeverity = (status: string): string => {
  const severities: Record<string, string> = {
    'completed': 'success',
    'shipped': 'info',
    'pending': 'warn',
    'cancelled': 'danger'
  }
  return severities[status] || 'secondary'
}

// Open order on Vinted
const openVintedOrder = (order: any) => {
  if (order.transaction_id) {
    window.open(`https://www.vinted.fr/transaction/${order.transaction_id}`, '_blank')
  }
}

// Shipment status helpers
const getShipmentStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    'pending': 'À expédier',
    'awaiting_shipment': 'À expédier',
    'shipped': 'Expédié',
    'in_transit': 'En transit',
    'completed': 'Livré',
    'delivered': 'Livré'
  }
  return labels[status] || status
}

const getShipmentStatusSeverity = (status: string): string => {
  const severities: Record<string, string> = {
    'pending': 'warn',
    'awaiting_shipment': 'warn',
    'shipped': 'info',
    'in_transit': 'info',
    'completed': 'success',
    'delivered': 'success'
  }
  return severities[status] || 'secondary'
}

// Download shipping label
const downloadLabel = async (order: any) => {
  toast?.add({
    severity: 'info',
    summary: 'Téléchargement',
    detail: 'Ouverture de Vinted pour télécharger le bordereau...',
    life: 3000
  })

  // Open the transaction page on Vinted where user can download the label
  if (order.transaction_id) {
    window.open(`https://www.vinted.fr/transaction/${order.transaction_id}/shipping_label`, '_blank')
  }
}

// Percentage helper for analytics
const getPercentage = (value: number, total: number): string => {
  if (total === 0) return '0'
  return ((value / total) * 100).toFixed(0)
}

// Load data on mount
onMounted(async () => {
  try {
    loading.value = true
    await Promise.all([
      fetchConnectionStatus(),
      fetchVintedProducts(),
      fetchVintedStats(),
      fetchOrders()
    ])

    // Load messages stats if connected (for unread badge)
    if (isConnected.value) {
      try {
        await messagesStore.fetchStats()
      } catch (e) {
        // Silent fail - just for badge display
        console.debug('Could not fetch messages stats:', e)
      }
    }
  } catch (error) {
    console.error('Erreur chargement données:', error)
  } finally {
    loading.value = false
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
  background: linear-gradient(90deg, #06b6d4, #0891b2);
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
</style>

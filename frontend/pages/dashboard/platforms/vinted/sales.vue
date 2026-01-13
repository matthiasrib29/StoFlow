<template>
  <div class="page-container">
    <!-- Page Header -->
    <PageHeader
      title="Commandes Vinted"
      subtitle="Gérez vos commandes depuis Vinted"
    >
      <template #actions>
        <Button
          label="Synchroniser"
          icon="pi pi-refresh"
          :loading="syncing"
          :disabled="!isConnected || syncing"
          class="bg-platform-vinted hover:bg-cyan-600 text-white border-0"
          v-tooltip.top="!isConnected ? 'Connexion Vinted requise pour synchroniser' : ''"
          @click="syncOrders"
        />
      </template>
    </PageHeader>

    <!-- Content -->
    <Card class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <!-- Offline banner -->
        <InfoBox v-if="!isConnected" type="warning" icon="pi pi-exclamation-triangle" class="mb-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="font-semibold">Mode hors ligne</p>
              <p class="text-sm mt-1">
                Vous consultez vos commandes importées. Reconnectez-vous pour synchroniser.
              </p>
            </div>
            <Button
              label="Connecter"
              icon="pi pi-link"
              size="small"
              class="btn-primary ml-4"
              @click="$router.push('/dashboard/platforms/vinted/settings')"
            />
          </div>
        </InfoBox>

        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card class="shadow-sm modern-rounded border border-gray-100">
            <template #content>
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-gray-500 mb-1">Total commandes</p>
                  <p class="text-2xl font-bold text-secondary-900">{{ stats.total_orders }}</p>
                </div>
                <i class="pi pi-shopping-bag text-3xl text-platform-vinted"/>
              </div>
            </template>
          </Card>

          <Card class="shadow-sm modern-rounded border border-gray-100">
            <template #content>
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-gray-500 mb-1">Revenus</p>
                  <p class="text-2xl font-bold text-success-600">{{ formatCurrency(stats.total_revenue) }}</p>
                </div>
                <i class="pi pi-euro text-3xl text-success-600"/>
              </div>
            </template>
          </Card>

          <Card class="shadow-sm modern-rounded border border-gray-100">
            <template #content>
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-gray-500 mb-1">En cours</p>
                  <p class="text-2xl font-bold text-warning-600">{{ stats.pending_orders }}</p>
                </div>
                <i class="pi pi-clock text-3xl text-warning-600"/>
              </div>
            </template>
          </Card>

          <Card class="shadow-sm modern-rounded border border-gray-100">
            <template #content>
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-gray-500 mb-1">Livrées</p>
                  <p class="text-2xl font-bold text-info-600">{{ stats.delivered_orders }}</p>
                </div>
                <i class="pi pi-check-circle text-3xl text-info-600"/>
              </div>
            </template>
          </Card>
        </div>

        <!-- Toolbar -->
        <div class="flex flex-col md:flex-row gap-4 mb-6">
          <div class="flex-1">
            <IconField>
              <InputIcon class="pi pi-search" />
              <InputText
                v-model="searchQuery"
                placeholder="Rechercher par produit, acheteur..."
                class="w-full"
              />
            </IconField>
          </div>
          <Dropdown
            v-model="statusFilter"
            :options="statusOptions"
            option-label="label"
            option-value="value"
            placeholder="Tous les statuts"
            class="w-full md:w-64"
            show-clear
          />
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-12">
          <ProgressSpinner style="width: 50px; height: 50px" />
          <p class="mt-4 text-gray-500">Chargement des commandes...</p>
        </div>

        <!-- Error -->
        <div v-else-if="error" class="text-center py-12">
          <i class="pi pi-exclamation-triangle text-4xl text-red-400 mb-4"/>
          <p class="text-red-600">{{ error }}</p>
          <Button
            label="Réessayer"
            icon="pi pi-refresh"
            class="mt-4"
            @click="fetchOrders"
          />
        </div>

        <!-- Empty -->
        <div v-else-if="orders.length === 0" class="text-center py-12">
          <i class="pi pi-shopping-bag text-4xl text-gray-300 mb-4"/>
          <p class="text-gray-500">
            {{ isConnected ? 'Aucune commande synchronisée' : 'Aucune commande importée' }}
          </p>
          <Button
            v-if="isConnected"
            label="Synchroniser maintenant"
            icon="pi pi-refresh"
            class="mt-4 bg-platform-vinted hover:bg-cyan-600 text-white border-0"
            @click="syncOrders"
          />
        </div>

        <!-- Orders DataTable -->
        <DataTable
          v-else
          :value="filteredOrders"
          :rows="20"
          :rows-per-page-options="[20, 50, 100]"
          paginator
          striped-rows
          responsive-layout="scroll"
          :global-filter-fields="['product_title', 'buyer_login']"
        >
          <Column header="Image" style="width: 80px">
            <template #body="{ data }">
              <img
                v-if="data.product_photo"
                :src="data.product_photo"
                :alt="data.product_title"
                class="w-16 h-16 object-cover rounded"
              />
              <div v-else class="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
                <i class="pi pi-image text-gray-400 text-xl"/>
              </div>
            </template>
          </Column>

          <Column field="product_title" header="Produit" sortable>
            <template #body="{ data }">
              <div class="font-medium">{{ data.product_title }}</div>
            </template>
          </Column>

          <Column field="buyer_login" header="Acheteur" sortable>
            <template #body="{ data }">
              <span class="text-sm">{{ data.buyer_login }}</span>
            </template>
          </Column>

          <Column field="total_price" header="Prix total" sortable>
            <template #body="{ data }">
              <span class="font-semibold">{{ formatCurrency(data.total_price) }}</span>
            </template>
          </Column>

          <Column field="seller_revenue" header="Revenus" sortable>
            <template #body="{ data }">
              <span class="font-semibold text-success-600">{{ formatCurrency(data.seller_revenue) }}</span>
            </template>
          </Column>

          <Column field="order_status" header="Statut paiement" sortable>
            <template #body="{ data }">
              <Tag :value="getOrderStatusLabel(data.order_status)" :severity="getOrderStatusSeverity(data.order_status)" />
            </template>
          </Column>

          <Column field="shipping_status" header="Statut livraison" sortable>
            <template #body="{ data }">
              <Tag :value="getShippingStatusLabel(data.shipping_status)" :severity="getShippingStatusSeverity(data.shipping_status)" />
            </template>
          </Column>

          <Column field="created_at_vinted" header="Date" sortable>
            <template #body="{ data }">
              <span class="text-sm">{{ formatDate(data.created_at_vinted) }}</span>
            </template>
          </Column>

          <Column field="tracking_number" header="Suivi" sortable>
            <template #body="{ data }">
              <span v-if="data.tracking_number" class="text-sm font-mono">{{ data.tracking_number }}</span>
              <span v-else class="text-gray-400 text-sm">-</span>
            </template>
          </Column>

          <Column header="Actions" style="width: 120px">
            <template #body="{ data }">
              <div class="flex gap-2">
                <Button
                  icon="pi pi-external-link"
                  text
                  rounded
                  size="small"
                  severity="secondary"
                  title="Voir sur Vinted"
                  @click="openOnVinted(data)"
                />
              </div>
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import type { VintedOrder, OrderStats } from '~/types/orders'
import { vintedLogger } from '~/utils/logger'
import InfoBox from '~/components/ui/InfoBox.vue'

definePageMeta({
  layout: 'dashboard'
})

// Platform connection
const { isConnected, fetchStatus } = usePlatformConnection('vinted')

// IMPORTANT: Call composables at setup level, not inside async functions
// This fixes "inject() can only be used inside setup()" error
const api = useApi()
const { showSuccess, showError, showInfo } = useAppToast()

// State
const loading = ref(false)
const syncing = ref(false)
const error = ref<string | null>(null)
const orders = ref<VintedOrder[]>([])
const searchQuery = ref('')
const statusFilter = ref<string | null>(null)

// Stats
const stats = ref<OrderStats>({
  total_orders: 0,
  total_revenue: 0,
  pending_orders: 0,
  shipped_orders: 0,
  delivered_orders: 0
})

// Computed
const isEmpty = computed(() => orders.value.length === 0 && !loading.value)

const filteredOrders = computed(() => {
  return orders.value.filter(order => {
    // Filter by search query
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      if (!order.product_title.toLowerCase().includes(query) &&
          !order.buyer_login.toLowerCase().includes(query)) {
        return false
      }
    }

    // Filter by status
    if (statusFilter.value && order.shipping_status !== statusFilter.value) {
      return false
    }

    return true
  })
})

// Status options for filter
const statusOptions = [
  { label: 'Tous les statuts', value: null },
  { label: 'En attente', value: 'pending' },
  { label: 'Expédiée', value: 'shipped' },
  { label: 'Livrée', value: 'delivered' },
  { label: 'Terminée', value: 'completed' }
]

// Methods
const fetchOrders = async () => {
  loading.value = true
  error.value = null
  vintedLogger.debug('[Sales] Fetching orders...')

  try {
    const response = await api.get('/vinted/orders')

    orders.value = response.orders || []
    vintedLogger.info(`[Sales] Fetched ${orders.value.length} orders`)

    // Calculate stats
    calculateStats()
  } catch (e: any) {
    error.value = e.message || 'Erreur lors du chargement des commandes'
    vintedLogger.error('[Sales] Failed to fetch orders:', e)
  } finally {
    loading.value = false
  }
}

// Polling interval ref for cleanup
const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)

const syncOrders = async () => {
  if (!isConnected.value) {
    vintedLogger.warn('[Sales] Cannot sync: platform not connected')
    return
  }

  syncing.value = true
  error.value = null
  vintedLogger.info('[Sales] Starting orders sync (fire-and-forget mode)...')

  showSuccess('Synchronisation lancée en arrière-plan')

  // Start polling immediately to show updates as they come in
  startPolling()

  // Fire-and-forget: launch sync but don't wait for completion
  api.post('/vinted/orders/sync')
    .then((response: any) => {
      vintedLogger.info('[Sales] Sync completed:', response)
      stopPolling()
      syncing.value = false
      fetchOrders() // Final refresh
      showSuccess('Synchronisation terminée')
    })
    .catch((e: any) => {
      vintedLogger.error('[Sales] Sync failed:', e)
      stopPolling()
      syncing.value = false
      error.value = e.message || 'Erreur lors de la synchronisation'
      showError('Erreur de synchronisation')
    })
}

const startPolling = () => {
  // Clear any existing polling
  stopPolling()

  vintedLogger.debug('[Sales] Starting polling for order updates...')

  // Refresh immediately
  fetchOrders()

  // Then poll every 5 seconds to show new orders as they arrive
  pollingInterval.value = setInterval(async () => {
    vintedLogger.debug('[Sales] Polling for new orders...')
    await fetchOrders()
  }, 5000)
}

const stopPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

const calculateStats = () => {
  stats.value = {
    total_orders: orders.value.length,
    total_revenue: orders.value.reduce((sum, order) => sum + (order.seller_revenue || 0), 0),
    pending_orders: orders.value.filter(o => o.shipping_status === 'pending').length,
    shipped_orders: orders.value.filter(o => o.shipping_status === 'shipped').length,
    delivered_orders: orders.value.filter(o => o.shipping_status === 'delivered').length
  }
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount)
}

const formatDate = (date: string) => {
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'short',
    timeStyle: 'short'
  }).format(new Date(date))
}

const getOrderStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: 'En attente',
    paid: 'Payée',
    completed: 'Terminée',
    cancelled: 'Annulée'
  }
  return labels[status] || status
}

const getOrderStatusSeverity = (status: string) => {
  const severities: Record<string, 'success' | 'info' | 'warn' | 'danger'> = {
    paid: 'success',
    completed: 'info',
    pending: 'warn',
    cancelled: 'danger'
  }
  return severities[status] || 'info'
}

const getShippingStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: 'En attente',
    shipped: 'Expédiée',
    delivered: 'Livrée',
    completed: 'Terminée'
  }
  return labels[status] || status
}

const getShippingStatusSeverity = (status: string) => {
  const severities: Record<string, 'success' | 'info' | 'warn' | 'danger'> = {
    delivered: 'success',
    shipped: 'info',
    pending: 'warn',
    completed: 'success'
  }
  return severities[status] || 'info'
}

const openOnVinted = (order: VintedOrder) => {
  if (order.transaction_id) {
    window.open(`https://www.vinted.fr/transaction/${order.transaction_id}`, '_blank')
  }
}

// Lifecycle
onMounted(async () => {
  // Fetch status in background (for UI indicators)
  fetchStatus()
  // Always load orders from database (even if disconnected)
  await fetchOrders()
})

onUnmounted(() => {
  // Cleanup polling interval to prevent memory leaks
  stopPolling()
})
</script>

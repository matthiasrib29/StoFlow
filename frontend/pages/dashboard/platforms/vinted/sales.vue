<template>
  <PlatformOrdersPage
    platform="vinted"
    :is-connected="isConnected"
    :loading="loading"
    :error="error"
    :is-empty="isEmpty"
    empty-message="Aucune commande trouvée"
    back-to="/dashboard/platforms"
    @retry="fetchOrders"
  >
    <!-- Header Actions -->
    <template #header-actions>
      <Button
        label="Synchroniser"
        icon="pi pi-refresh"
        :loading="syncing"
        :disabled="!isConnected"
        class="bg-platform-vinted hover:bg-cyan-600 text-white border-0"
        @click="syncOrders"
      />
    </template>

    <!-- Stats Cards -->
    <template #stats>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
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
    </template>

    <!-- Toolbar -->
    <template #toolbar>
      <div class="flex flex-col md:flex-row gap-4">
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
    </template>

    <!-- Orders DataTable -->
    <template #content>
      <DataTable
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

    <!-- Empty Actions -->
    <template #empty-actions>
      <Button
        v-if="isConnected"
        label="Synchroniser les commandes"
        icon="pi pi-refresh"
        class="mt-4 bg-platform-vinted hover:bg-cyan-600 text-white border-0"
        @click="syncOrders"
      />
    </template>
  </PlatformOrdersPage>
</template>

<script setup lang="ts">
import type { VintedOrder, OrderStats } from '~/types/orders'

definePageMeta({
  layout: 'dashboard'
})

// Platform connection
const { isConnected, fetchStatus } = usePlatformConnection('vinted')

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
  if (!isConnected.value) return

  loading.value = true
  error.value = null

  try {
    const api = useApi()
    const response = await api.get('/api/vinted/orders')

    orders.value = response.orders || []

    // Calculate stats
    calculateStats()
  } catch (e: any) {
    error.value = e.message || 'Erreur lors du chargement des commandes'
    console.error('Failed to fetch Vinted orders:', e)
  } finally {
    loading.value = false
  }
}

const syncOrders = async () => {
  if (!isConnected.value) return

  syncing.value = true
  error.value = null

  try {
    const api = useApi()
    await api.post('/api/vinted/orders/sync')

    const toast = useAppToast()
    toast.success('Synchronisation des commandes lancée')

    // Refresh orders after sync
    await fetchOrders()
  } catch (e: any) {
    error.value = e.message || 'Erreur lors de la synchronisation'
    console.error('Failed to sync Vinted orders:', e)
  } finally {
    syncing.value = false
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
  await fetchStatus()
  if (isConnected.value) {
    await fetchOrders()
  }
})
</script>

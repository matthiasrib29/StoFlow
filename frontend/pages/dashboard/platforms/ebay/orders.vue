<template>
  <PlatformOrdersPage
    platform="ebay"
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
        label="Rafraîchir"
        icon="pi pi-refresh"
        :loading="refreshing"
        :disabled="!isConnected"
        class="bg-platform-ebay hover:bg-blue-700 text-white border-0"
        @click="fetchOrders"
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
              <i class="pi pi-shopping-bag text-3xl text-platform-ebay"/>
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
              <i class="pi pi-dollar text-3xl text-success-600"/>
            </div>
          </template>
        </Card>

        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 mb-1">À expédier</p>
                <p class="text-2xl font-bold text-warning-600">{{ stats.pending_orders }}</p>
              </div>
              <i class="pi pi-box text-3xl text-warning-600"/>
            </div>
          </template>
        </Card>

        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 mb-1">Expédiées</p>
                <p class="text-2xl font-bold text-info-600">{{ stats.shipped_orders }}</p>
              </div>
              <i class="pi pi-send text-3xl text-info-600"/>
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
              placeholder="Rechercher par Order ID, acheteur..."
              class="w-full"
            />
          </IconField>
        </div>
        <div class="flex gap-2">
          <Dropdown
            v-model="paymentStatusFilter"
            :options="paymentStatusOptions"
            option-label="label"
            option-value="value"
            placeholder="Statut paiement"
            class="w-full md:w-48"
            show-clear
          />
          <Dropdown
            v-model="fulfillmentStatusFilter"
            :options="fulfillmentStatusOptions"
            option-label="label"
            option-value="value"
            placeholder="Statut livraison"
            class="w-full md:w-48"
            show-clear
          />
        </div>
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
        :global-filter-fields="['order_id', 'buyer_username']"
      >
        <Column field="order_id" header="Order ID" sortable>
          <template #body="{ data }">
            <span class="font-mono text-sm">{{ data.order_id }}</span>
          </template>
        </Column>

        <Column field="buyer_username" header="Acheteur" sortable>
          <template #body="{ data }">
            <div>
              <div class="font-medium">{{ data.buyer_username }}</div>
              <div v-if="data.buyer_email" class="text-xs text-gray-500">{{ data.buyer_email }}</div>
            </div>
          </template>
        </Column>

        <Column field="items_count" header="Articles" sortable>
          <template #body="{ data }">
            <span class="text-sm">{{ data.items_count || '-' }}</span>
          </template>
        </Column>

        <Column field="total_price" header="Total" sortable>
          <template #body="{ data }">
            <span class="font-semibold">{{ formatAmount(data.total_price, data.currency) }}</span>
          </template>
        </Column>

        <Column field="order_payment_status" header="Paiement" sortable>
          <template #body="{ data }">
            <Tag :value="getPaymentStatusLabel(data.order_payment_status)" :severity="getPaymentStatusSeverity(data.order_payment_status)" />
          </template>
        </Column>

        <Column field="order_fulfillment_status" header="Livraison" sortable>
          <template #body="{ data }">
            <Tag :value="getFulfillmentStatusLabel(data.order_fulfillment_status)" :severity="getFulfillmentStatusSeverity(data.order_fulfillment_status)" />
          </template>
        </Column>

        <Column field="creation_date" header="Date création" sortable>
          <template #body="{ data }">
            <span class="text-sm">{{ formatDate(data.creation_date) }}</span>
          </template>
        </Column>

        <Column field="tracking_number" header="Suivi" sortable>
          <template #body="{ data }">
            <div v-if="data.tracking_number" class="text-sm">
              <div class="font-mono">{{ data.tracking_number }}</div>
              <div v-if="data.shipping_carrier" class="text-xs text-gray-500">{{ data.shipping_carrier }}</div>
            </div>
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
                title="Voir sur eBay"
                @click="openOnEbay(data)"
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
        label="Rafraîchir"
        icon="pi pi-refresh"
        class="mt-4 bg-platform-ebay hover:bg-blue-700 text-white border-0"
        @click="fetchOrders"
      />
    </template>
  </PlatformOrdersPage>
</template>

<script setup lang="ts">
import type { EbayOrder, OrderStats } from '~/types/orders'
import { EbayFulfillmentStatus, EbayPaymentStatus } from '~/types/orders'

definePageMeta({
  layout: 'dashboard'
})

// Platform connection
const { isConnected, fetchStatus } = usePlatformConnection('ebay')

// State
const loading = ref(false)
const refreshing = ref(false)
const error = ref<string | null>(null)
const orders = ref<EbayOrder[]>([])
const searchQuery = ref('')
const paymentStatusFilter = ref<string | null>(null)
const fulfillmentStatusFilter = ref<string | null>(null)

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
      if (!order.order_id.toLowerCase().includes(query) &&
          !order.buyer_username.toLowerCase().includes(query)) {
        return false
      }
    }

    // Filter by payment status
    if (paymentStatusFilter.value && order.order_payment_status !== paymentStatusFilter.value) {
      return false
    }

    // Filter by fulfillment status
    if (fulfillmentStatusFilter.value && order.order_fulfillment_status !== fulfillmentStatusFilter.value) {
      return false
    }

    return true
  })
})

// Filter options
const paymentStatusOptions = [
  { label: 'Tous', value: null },
  { label: 'Payée', value: EbayPaymentStatus.PAID },
  { label: 'En attente', value: EbayPaymentStatus.PENDING },
  { label: 'Échouée', value: EbayPaymentStatus.FAILED }
]

const fulfillmentStatusOptions = [
  { label: 'Tous', value: null },
  { label: 'Non commencé', value: EbayFulfillmentStatus.NOT_STARTED },
  { label: 'En cours', value: EbayFulfillmentStatus.IN_PROGRESS },
  { label: 'Terminé', value: EbayFulfillmentStatus.FULFILLED },
  { label: 'Annulé', value: EbayFulfillmentStatus.CANCELLED }
]

// Methods
const fetchOrders = async () => {
  if (!isConnected.value) return

  loading.value = true
  refreshing.value = true
  error.value = null

  try {
    const api = useApi()
    // Use new paginated endpoint with large page_size to get all orders
    const response = await api.get('/api/ebay/orders', {
      params: {
        page: 1,
        page_size: 200 // Max allowed
      }
    })

    // New format returns { items, total, page, page_size, total_pages }
    orders.value = response.items || []

    // Calculate stats
    calculateStats()
  } catch (e: any) {
    error.value = e.message || 'Erreur lors du chargement des commandes'
    console.error('Failed to fetch eBay orders:', e)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

const calculateStats = () => {
  stats.value = {
    total_orders: orders.value.length,
    total_revenue: orders.value.reduce((sum, order) => sum + (order.total_price || 0), 0),
    pending_orders: orders.value.filter(o =>
      o.order_fulfillment_status === EbayFulfillmentStatus.NOT_STARTED ||
      o.order_fulfillment_status === EbayFulfillmentStatus.IN_PROGRESS
    ).length,
    shipped_orders: orders.value.filter(o => o.order_fulfillment_status === EbayFulfillmentStatus.FULFILLED).length,
    delivered_orders: 0 // eBay doesn't have a specific delivered status
  }
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount)
}

const formatAmount = (amount: number, currency: string = 'EUR') => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: currency || 'EUR'
  }).format(amount)
}

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'short',
    timeStyle: 'short'
  }).format(new Date(date))
}

const getPaymentStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    [EbayPaymentStatus.PAID]: 'Payée',
    [EbayPaymentStatus.PENDING]: 'En attente',
    [EbayPaymentStatus.FAILED]: 'Échouée'
  }
  return labels[status] || status
}

const getPaymentStatusSeverity = (status: string) => {
  const severities: Record<string, 'success' | 'info' | 'warn' | 'danger'> = {
    [EbayPaymentStatus.PAID]: 'success',
    [EbayPaymentStatus.PENDING]: 'warn',
    [EbayPaymentStatus.FAILED]: 'danger'
  }
  return severities[status] || 'info'
}

const getFulfillmentStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    [EbayFulfillmentStatus.NOT_STARTED]: 'Non commencé',
    [EbayFulfillmentStatus.IN_PROGRESS]: 'En cours',
    [EbayFulfillmentStatus.FULFILLED]: 'Terminé',
    [EbayFulfillmentStatus.CANCELLED]: 'Annulé'
  }
  return labels[status] || status
}

const getFulfillmentStatusSeverity = (status: string) => {
  const severities: Record<string, 'success' | 'info' | 'warn' | 'danger'> = {
    [EbayFulfillmentStatus.FULFILLED]: 'success',
    [EbayFulfillmentStatus.IN_PROGRESS]: 'info',
    [EbayFulfillmentStatus.NOT_STARTED]: 'warn',
    [EbayFulfillmentStatus.CANCELLED]: 'danger'
  }
  return severities[status] || 'info'
}

const openOnEbay = (order: EbayOrder) => {
  if (order.order_id) {
    // eBay order management URL
    window.open(`https://www.ebay.fr/sh/ord/details?orderid=${order.order_id}`, '_blank')
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

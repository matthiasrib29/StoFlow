<template>
  <div class="page-container">
    <!-- Back Button & Header -->
    <div class="flex items-center gap-4 mb-6">
      <Button
        icon="pi pi-arrow-left"
        text
        rounded
        severity="secondary"
        @click="navigateTo('/dashboard/platforms/ebay/orders')"
      />
      <div class="flex-1">
        <h1 class="text-2xl font-bold text-secondary-900">Détails de la commande</h1>
        <p v-if="order" class="text-sm text-gray-500 mt-1">{{ order.order_id }}</p>
      </div>
      <Button
        v-if="order"
        label="Voir sur eBay"
        icon="pi pi-external-link"
        class="bg-platform-ebay hover:bg-blue-700 text-white border-0"
        @click="openOnEbay"
      />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-20">
      <ProgressSpinner />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-error-50 border border-error-200 rounded-lg p-6">
      <div class="flex items-center gap-3">
        <i class="pi pi-exclamation-circle text-2xl text-error-600" />
        <div>
          <h3 class="font-semibold text-error-900">Erreur</h3>
          <p class="text-sm text-error-700 mt-1">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Order Details -->
    <div v-else-if="order" class="space-y-6">
      <!-- Status Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Payment Status -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="text-center">
              <p class="text-sm text-gray-500 mb-2">Statut Paiement</p>
              <Tag
                :value="getPaymentStatusLabel(order.order_payment_status)"
                :severity="getPaymentStatusSeverity(order.order_payment_status)"
                class="text-base px-4 py-2"
              />
            </div>
          </template>
        </Card>

        <!-- Fulfillment Status -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="text-center">
              <p class="text-sm text-gray-500 mb-2">Statut Livraison</p>
              <Tag
                :value="getFulfillmentStatusLabel(order.order_fulfillment_status)"
                :severity="getFulfillmentStatusSeverity(order.order_fulfillment_status)"
                class="text-base px-4 py-2"
              />
            </div>
          </template>
        </Card>

        <!-- Total Amount -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="text-center">
              <p class="text-sm text-gray-500 mb-2">Montant Total</p>
              <p class="text-2xl font-bold text-success-600">{{ formatAmount(order.total_price, order.currency) }}</p>
            </div>
          </template>
        </Card>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Buyer Information -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #header>
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
                <i class="pi pi-user text-platform-ebay" />
                Informations Acheteur
              </h2>
            </div>
          </template>
          <template #content>
            <div class="space-y-3">
              <div>
                <p class="text-xs text-gray-500 mb-1">Nom d'utilisateur</p>
                <p class="font-medium">{{ order.buyer_username || '-' }}</p>
              </div>
              <div v-if="order.buyer_email">
                <p class="text-xs text-gray-500 mb-1">Email</p>
                <p class="font-medium">{{ order.buyer_email }}</p>
              </div>
              <div v-if="order.marketplace_id">
                <p class="text-xs text-gray-500 mb-1">Marketplace</p>
                <p class="font-medium">{{ order.marketplace_id }}</p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Shipping Address -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #header>
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
                <i class="pi pi-map-marker text-platform-ebay" />
                Adresse de Livraison
              </h2>
            </div>
          </template>
          <template #content>
            <div class="space-y-3">
              <div v-if="order.shipping_name">
                <p class="text-xs text-gray-500 mb-1">Destinataire</p>
                <p class="font-medium">{{ order.shipping_name }}</p>
              </div>
              <div v-if="order.shipping_address">
                <p class="text-xs text-gray-500 mb-1">Adresse</p>
                <p class="font-medium">{{ order.shipping_address }}</p>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div v-if="order.shipping_postal_code">
                  <p class="text-xs text-gray-500 mb-1">Code postal</p>
                  <p class="font-medium">{{ order.shipping_postal_code }}</p>
                </div>
                <div v-if="order.shipping_city">
                  <p class="text-xs text-gray-500 mb-1">Ville</p>
                  <p class="font-medium">{{ order.shipping_city }}</p>
                </div>
              </div>
              <div v-if="order.shipping_country">
                <p class="text-xs text-gray-500 mb-1">Pays</p>
                <p class="font-medium">{{ order.shipping_country }}</p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Pricing Details -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #header>
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
                <i class="pi pi-dollar text-platform-ebay" />
                Détails Financiers
              </h2>
            </div>
          </template>
          <template #content>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-gray-600">Sous-total produits</span>
                <span class="font-semibold">{{ formatAmount(subtotal, order.currency) }}</span>
              </div>
              <div v-if="order.shipping_cost" class="flex justify-between">
                <span class="text-gray-600">Frais de port</span>
                <span class="font-semibold">{{ formatAmount(order.shipping_cost, order.currency) }}</span>
              </div>
              <Divider />
              <div class="flex justify-between items-center">
                <span class="text-lg font-semibold text-gray-900">Total</span>
                <span class="text-xl font-bold text-success-600">{{ formatAmount(order.total_price, order.currency) }}</span>
              </div>
            </div>
          </template>
        </Card>

        <!-- Tracking & Dates -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #header>
            <div class="p-4 border-b border-gray-100">
              <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
                <i class="pi pi-calendar text-platform-ebay" />
                Suivi & Dates
              </h2>
            </div>
          </template>
          <template #content>
            <div class="space-y-3">
              <div v-if="order.tracking_number">
                <p class="text-xs text-gray-500 mb-1">Numéro de suivi</p>
                <p class="font-mono font-medium">{{ order.tracking_number }}</p>
              </div>
              <div v-if="order.shipping_carrier">
                <p class="text-xs text-gray-500 mb-1">Transporteur</p>
                <p class="font-medium">{{ order.shipping_carrier }}</p>
              </div>
              <Divider />
              <div v-if="order.creation_date">
                <p class="text-xs text-gray-500 mb-1">Date de création</p>
                <p class="font-medium">{{ formatDate(order.creation_date) }}</p>
              </div>
              <div v-if="order.paid_date">
                <p class="text-xs text-gray-500 mb-1">Date de paiement</p>
                <p class="font-medium">{{ formatDate(order.paid_date) }}</p>
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Products Table -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #header>
          <div class="p-4 border-b border-gray-100">
            <h2 class="text-lg font-semibold text-secondary-900 flex items-center gap-2">
              <i class="pi pi-shopping-bag text-platform-ebay" />
              Produits ({{ order.items_count }})
            </h2>
          </div>
        </template>
        <template #content>
          <DataTable :value="order.products" striped-rows responsive-layout="scroll">
            <Column field="sku" header="SKU" sortable>
              <template #body="{ data }">
                <span class="font-mono text-sm">{{ data.sku || '-' }}</span>
              </template>
            </Column>

            <Column field="title" header="Titre" sortable>
              <template #body="{ data }">
                <span class="font-medium">{{ data.title || '-' }}</span>
              </template>
            </Column>

            <Column field="quantity" header="Qté" sortable>
              <template #body="{ data }">
                <span class="text-center">{{ data.quantity || 1 }}</span>
              </template>
            </Column>

            <Column field="unit_price" header="Prix unitaire" sortable>
              <template #body="{ data }">
                <span class="font-semibold">{{ formatAmount(data.unit_price, data.currency) }}</span>
              </template>
            </Column>

            <Column field="total_price" header="Total ligne" sortable>
              <template #body="{ data }">
                <span class="font-semibold text-success-600">{{ formatAmount(data.total_price, data.currency) }}</span>
              </template>
            </Column>

            <Column v-if="hasLegacyItemIds" field="legacy_item_id" header="Item ID" sortable>
              <template #body="{ data }">
                <span class="font-mono text-xs text-gray-500">{{ data.legacy_item_id || '-' }}</span>
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { EbayOrder } from '~/types/orders'
import { EbayFulfillmentStatus, EbayPaymentStatus } from '~/types/orders'
import { ebayLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

// Get order ID from route
const route = useRoute()
const orderId = computed(() => Number(route.params.id))

// Toast notifications
const { showError } = useAppToast()

// State
const loading = ref(true)
const error = ref<string | null>(null)
const order = ref<EbayOrder | null>(null)

// Computed
const subtotal = computed(() => {
  if (!order.value?.products) return 0
  return order.value.products.reduce((sum, product) => sum + (product.total_price || 0), 0)
})

const hasLegacyItemIds = computed(() => {
  return order.value?.products?.some(p => p.legacy_item_id) || false
})

// Methods
const fetchOrder = async () => {
  loading.value = true
  error.value = null

  try {
    const api = useApi()
    order.value = await api.get(`/api/ebay/orders/${orderId.value}`)
  } catch (e: any) {
    error.value = e.message || 'Erreur lors du chargement de la commande'
    ebayLogger.error('Failed to fetch order:', e)
    showError('Erreur', error.value, 5000)
  } finally {
    loading.value = false
  }
}

const formatAmount = (amount: number | null | undefined, currency: string = 'EUR') => {
  if (amount === null || amount === undefined) return '-'
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: currency || 'EUR'
  }).format(amount)
}

const formatDate = (date: string | null | undefined) => {
  if (!date) return '-'
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(date))
}

const getPaymentStatusLabel = (status: string | null | undefined) => {
  if (!status) return '-'
  const labels: Record<string, string> = {
    [EbayPaymentStatus.PAID]: 'Payée',
    [EbayPaymentStatus.PENDING]: 'En attente',
    [EbayPaymentStatus.FAILED]: 'Échouée'
  }
  return labels[status] || status
}

const getPaymentStatusSeverity = (status: string | null | undefined) => {
  if (!status) return 'secondary'
  const severities: Record<string, 'success' | 'info' | 'warn' | 'danger' | 'secondary'> = {
    [EbayPaymentStatus.PAID]: 'success',
    [EbayPaymentStatus.PENDING]: 'warn',
    [EbayPaymentStatus.FAILED]: 'danger'
  }
  return severities[status] || 'secondary'
}

const getFulfillmentStatusLabel = (status: string | null | undefined) => {
  if (!status) return '-'
  const labels: Record<string, string> = {
    [EbayFulfillmentStatus.NOT_STARTED]: 'Non commencé',
    [EbayFulfillmentStatus.IN_PROGRESS]: 'En cours',
    [EbayFulfillmentStatus.FULFILLED]: 'Terminé',
    [EbayFulfillmentStatus.CANCELLED]: 'Annulé'
  }
  return labels[status] || status
}

const getFulfillmentStatusSeverity = (status: string | null | undefined) => {
  if (!status) return 'secondary'
  const severities: Record<string, 'success' | 'info' | 'warn' | 'danger' | 'secondary'> = {
    [EbayFulfillmentStatus.FULFILLED]: 'success',
    [EbayFulfillmentStatus.IN_PROGRESS]: 'info',
    [EbayFulfillmentStatus.NOT_STARTED]: 'warn',
    [EbayFulfillmentStatus.CANCELLED]: 'danger'
  }
  return severities[status] || 'secondary'
}

const openOnEbay = () => {
  if (order.value?.order_id) {
    window.open(`https://www.ebay.fr/sh/ord/details?orderid=${order.value.order_id}`, '_blank')
  }
}

// Lifecycle
onMounted(() => {
  fetchOrder()
})
</script>

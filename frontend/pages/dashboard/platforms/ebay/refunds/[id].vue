<script setup lang="ts">
/**
 * eBay Refund Detail Page
 *
 * Displays detailed information about a specific refund.
 */

import type { EbayRefund } from '~/types/ebay'

definePageMeta({
  layout: 'dashboard',
})

const route = useRoute()
const router = useRouter()
const toast = useAppToast()

const {
  fetchRefund,
  getStatusLabel,
  getStatusSeverity,
  getSourceLabel,
  getSourceSeverity,
  getReasonLabel,
  formatAmount,
  formatDate,
  getSourceIcon
} = useEbayRefunds()

// =========================================================================
// STATE
// =========================================================================

const refund = ref<EbayRefund | null>(null)
const loading = ref(false)

// =========================================================================
// COMPUTED
// =========================================================================

const refundId = computed(() => {
  const id = route.params.id
  return Array.isArray(id) ? parseInt(id[0]) : parseInt(id)
})

// =========================================================================
// DATA FETCHING
// =========================================================================

const loadRefund = async () => {
  loading.value = true
  try {
    refund.value = await fetchRefund(refundId.value)
  } catch (error) {
    console.error('Failed to load refund:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de charger le remboursement',
      life: 5000
    })
    router.push('/dashboard/platforms/ebay/refunds')
  } finally {
    loading.value = false
  }
}

// =========================================================================
// NAVIGATION
// =========================================================================

const goBack = () => {
  router.push('/dashboard/platforms/ebay/refunds')
}

const goToOrder = () => {
  if (refund.value?.order_id) {
    // Assuming orders page exists
    router.push(`/dashboard/platforms/ebay/orders?search=${refund.value.order_id}`)
  }
}

const goToReturn = () => {
  if (refund.value?.return_id) {
    router.push(`/dashboard/platforms/ebay/returns?search=${refund.value.return_id}`)
  }
}

const goToCancellation = () => {
  if (refund.value?.cancel_id) {
    router.push(`/dashboard/platforms/ebay/cancellations?search=${refund.value.cancel_id}`)
  }
}

// =========================================================================
// LIFECYCLE
// =========================================================================

onMounted(async () => {
  await loadRefund()
})
</script>

<template>
  <div class="p-6">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <ProgressSpinner />
    </div>

    <!-- Content -->
    <div v-else-if="refund">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-4">
          <Button
            icon="pi pi-arrow-left"
            severity="secondary"
            text
            rounded
            @click="goBack"
          />
          <div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
              Remboursement #{{ refund.refund_id }}
            </h1>
            <p class="text-gray-600 dark:text-gray-400 mt-1">
              {{ formatDate(refund.refund_date || refund.created_at) }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <Tag
            :value="getStatusLabel(refund.refund_status)"
            :severity="getStatusSeverity(refund.refund_status)"
            class="text-base px-4 py-2"
          />
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column: Main Info -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Amount Card -->
          <Card>
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-euro" />
                <span>Montant</span>
              </div>
            </template>
            <template #content>
              <div class="text-center py-4">
                <p class="text-4xl font-bold text-gray-900 dark:text-white">
                  {{ formatAmount(refund) }}
                </p>
                <p v-if="refund.original_amount" class="text-sm text-gray-500 mt-2">
                  Montant original : {{ new Intl.NumberFormat('fr-FR', { style: 'currency', currency: refund.refund_currency || 'EUR' }).format(refund.original_amount) }}
                </p>
              </div>
            </template>
          </Card>

          <!-- Details Card -->
          <Card>
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-info-circle" />
                <span>Détails</span>
              </div>
            </template>
            <template #content>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Source -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Source</p>
                  <Tag
                    :severity="getSourceSeverity(refund.refund_source)"
                  >
                    <template #default>
                      <i :class="getSourceIcon(refund.refund_source)" class="mr-1" />
                      {{ getSourceLabel(refund.refund_source) }}
                    </template>
                  </Tag>
                </div>

                <!-- Reason -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Raison</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ getReasonLabel(refund.reason) }}
                  </p>
                </div>

                <!-- Buyer -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Acheteur</p>
                  <p class="font-medium text-gray-900 dark:text-white">
                    {{ refund.buyer_username || '-' }}
                  </p>
                </div>

                <!-- Line Item -->
                <div v-if="refund.line_item_id">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Article</p>
                  <p class="font-mono text-sm text-gray-900 dark:text-white">
                    {{ refund.line_item_id }}
                  </p>
                </div>

                <!-- Comment -->
                <div v-if="refund.comment" class="md:col-span-2">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Commentaire</p>
                  <p class="text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                    {{ refund.comment }}
                  </p>
                </div>
              </div>
            </template>
          </Card>

          <!-- Reference IDs Card -->
          <Card>
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-link" />
                <span>Références</span>
              </div>
            </template>
            <template #content>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Order ID -->
                <div>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">N° Commande</p>
                  <div class="flex items-center gap-2">
                    <p class="font-mono text-sm text-gray-900 dark:text-white">
                      {{ refund.order_id || '-' }}
                    </p>
                    <Button
                      v-if="refund.order_id"
                      icon="pi pi-external-link"
                      text
                      rounded
                      size="small"
                      @click="goToOrder"
                    />
                  </div>
                </div>

                <!-- Return ID -->
                <div v-if="refund.return_id">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">ID Retour</p>
                  <div class="flex items-center gap-2">
                    <p class="font-mono text-sm text-gray-900 dark:text-white">
                      {{ refund.return_id }}
                    </p>
                    <Button
                      icon="pi pi-external-link"
                      text
                      rounded
                      size="small"
                      @click="goToReturn"
                    />
                  </div>
                </div>

                <!-- Cancel ID -->
                <div v-if="refund.cancel_id">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">ID Annulation</p>
                  <div class="flex items-center gap-2">
                    <p class="font-mono text-sm text-gray-900 dark:text-white">
                      {{ refund.cancel_id }}
                    </p>
                    <Button
                      icon="pi pi-external-link"
                      text
                      rounded
                      size="small"
                      @click="goToCancellation"
                    />
                  </div>
                </div>

                <!-- Refund Reference ID -->
                <div v-if="refund.refund_reference_id">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Réf. Remboursement</p>
                  <p class="font-mono text-sm text-gray-900 dark:text-white">
                    {{ refund.refund_reference_id }}
                  </p>
                </div>

                <!-- Transaction ID -->
                <div v-if="refund.transaction_id">
                  <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">ID Transaction</p>
                  <p class="font-mono text-sm text-gray-900 dark:text-white">
                    {{ refund.transaction_id }}
                  </p>
                </div>
              </div>
            </template>
          </Card>
        </div>

        <!-- Right Column: Timeline & Actions -->
        <div class="space-y-6">
          <!-- Status Card -->
          <Card>
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-chart-bar" />
                <span>Statut</span>
              </div>
            </template>
            <template #content>
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-gray-600 dark:text-gray-400">État</span>
                  <Tag
                    :value="getStatusLabel(refund.refund_status)"
                    :severity="getStatusSeverity(refund.refund_status)"
                  />
                </div>

                <div class="flex items-center justify-between">
                  <span class="text-gray-600 dark:text-gray-400">Source</span>
                  <Tag
                    :severity="getSourceSeverity(refund.refund_source)"
                  >
                    <template #default>
                      <i :class="getSourceIcon(refund.refund_source)" class="mr-1" />
                      {{ getSourceLabel(refund.refund_source) }}
                    </template>
                  </Tag>
                </div>

                <!-- Status indicators -->
                <div class="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                  <div class="flex items-center gap-2 text-sm">
                    <i
                      :class="[
                        'pi',
                        refund.is_completed
                          ? 'pi-check-circle text-green-500'
                          : 'pi-circle text-gray-300'
                      ]"
                    />
                    <span :class="refund.is_completed ? 'text-green-600' : 'text-gray-400'">
                      Remboursement effectué
                    </span>
                  </div>

                  <div class="flex items-center gap-2 text-sm">
                    <i
                      :class="[
                        'pi',
                        refund.is_pending
                          ? 'pi-clock text-yellow-500'
                          : 'pi-circle text-gray-300'
                      ]"
                    />
                    <span :class="refund.is_pending ? 'text-yellow-600' : 'text-gray-400'">
                      En attente de traitement
                    </span>
                  </div>

                  <div class="flex items-center gap-2 text-sm">
                    <i
                      :class="[
                        'pi',
                        refund.is_failed
                          ? 'pi-times-circle text-red-500'
                          : 'pi-circle text-gray-300'
                      ]"
                    />
                    <span :class="refund.is_failed ? 'text-red-600' : 'text-gray-400'">
                      Échec du remboursement
                    </span>
                  </div>
                </div>
              </div>
            </template>
          </Card>

          <!-- Timeline Card -->
          <Card>
            <template #title>
              <div class="flex items-center gap-2">
                <i class="pi pi-history" />
                <span>Chronologie</span>
              </div>
            </template>
            <template #content>
              <div class="space-y-4">
                <!-- Creation Date -->
                <div class="flex items-start gap-3">
                  <div class="p-2 bg-blue-100 dark:bg-blue-900/40 rounded-full">
                    <i class="pi pi-plus text-blue-600 dark:text-blue-400 text-sm" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      Remboursement initié
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(refund.creation_date) }}
                    </p>
                  </div>
                </div>

                <!-- Refund Date -->
                <div v-if="refund.refund_date" class="flex items-start gap-3">
                  <div
                    class="p-2 rounded-full"
                    :class="
                      refund.is_completed
                        ? 'bg-green-100 dark:bg-green-900/40'
                        : refund.is_failed
                        ? 'bg-red-100 dark:bg-red-900/40'
                        : 'bg-yellow-100 dark:bg-yellow-900/40'
                    "
                  >
                    <i
                      :class="[
                        'pi text-sm',
                        refund.is_completed
                          ? 'pi-check text-green-600 dark:text-green-400'
                          : refund.is_failed
                          ? 'pi-times text-red-600 dark:text-red-400'
                          : 'pi-clock text-yellow-600 dark:text-yellow-400'
                      ]"
                    />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      {{
                        refund.is_completed
                          ? 'Remboursement effectué'
                          : refund.is_failed
                          ? 'Remboursement échoué'
                          : 'En cours de traitement'
                      }}
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(refund.refund_date) }}
                    </p>
                  </div>
                </div>

                <!-- Record Created -->
                <div class="flex items-start gap-3">
                  <div class="p-2 bg-gray-100 dark:bg-gray-700 rounded-full">
                    <i class="pi pi-database text-gray-600 dark:text-gray-400 text-sm" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      Enregistré dans StoFlow
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(refund.created_at) }}
                    </p>
                  </div>
                </div>

                <!-- Last Update -->
                <div class="flex items-start gap-3">
                  <div class="p-2 bg-gray-100 dark:bg-gray-700 rounded-full">
                    <i class="pi pi-refresh text-gray-600 dark:text-gray-400 text-sm" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      Dernière mise à jour
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatDate(refund.updated_at) }}
                    </p>
                  </div>
                </div>
              </div>
            </template>
          </Card>
        </div>
      </div>
    </div>
  </div>
</template>

<!--
  ╔═══════════════════════════════════════════════════════════════╗
  ║  🚧 PMV2 - Cette page est cachée pour la phase 1              ║
  ║                                                               ║
  ║  Pour activer: useFeatureFlags.ts → ebayPostSale: true        ║
  ╚═══════════════════════════════════════════════════════════════╝
-->
<script setup lang="ts">
/**
 * eBay Payment Disputes List Page
 *
 * Displays all payment disputes with filtering, statistics, and actions.
 */

import type { EbayPaymentDispute, EbayPaymentDisputeStatistics } from '~/types/ebay'

definePageMeta({
  layout: 'dashboard',
})

const toast = useAppToast()
const router = useRouter()

const {
  fetchDisputes,
  fetchStatistics,
  syncDisputes,
  getStateLabel,
  getStateSeverity,
  getReasonLabel,
  getStateIcon,
  formatAmount,
  formatDate,
  isUrgent,
  getDaysUntilDeadline
} = useEbayPaymentDisputes()

// =========================================================================
// STATE
// =========================================================================

const disputes = ref<EbayPaymentDispute[]>([])
const statistics = ref<EbayPaymentDisputeStatistics | null>(null)
const loading = ref(false)
const syncing = ref(false)
const totalRecords = ref(0)

// Pagination
const currentPage = ref(1)
const pageSize = ref(20)

// Filters
const selectedState = ref<'OPEN' | 'ACTION_NEEDED' | 'CLOSED' | null>(null)
const orderIdFilter = ref<string>('')

// Filter options
const stateOptions = [
  { label: 'Tous les états', value: null },
  { label: 'Ouvert', value: 'OPEN' },
  { label: 'Action requise', value: 'ACTION_NEEDED' },
  { label: 'Fermé', value: 'CLOSED' }
]

// =========================================================================
// DATA FETCHING
// =========================================================================

const loadDisputes = async () => {
  loading.value = true
  try {
    const response = await fetchDisputes({
      page: currentPage.value,
      page_size: pageSize.value,
      state: selectedState.value,
      order_id: orderIdFilter.value || null
    })
    disputes.value = response.items
    totalRecords.value = response.total
  } catch (error) {
    console.error('Failed to load disputes:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de charger les litiges',
      life: 5000
    })
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  try {
    statistics.value = await fetchStatistics()
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

const handleSync = async () => {
  syncing.value = true
  try {
    const result = await syncDisputes()
    toast.add({
      severity: 'success',
      summary: 'Synchronisation terminée',
      detail: `${result.created} créés, ${result.updated} mis à jour`,
      life: 5000
    })
    // Reload data
    await Promise.all([loadDisputes(), loadStatistics()])
  } catch (error) {
    console.error('Sync failed:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'La synchronisation a échoué',
      life: 5000
    })
  } finally {
    syncing.value = false
  }
}

// =========================================================================
// NAVIGATION
// =========================================================================

const viewDispute = (dispute: EbayPaymentDispute) => {
  router.push(`/dashboard/platforms/ebay/payment-disputes/${dispute.id}`)
}

// =========================================================================
// PAGINATION
// =========================================================================

const onPageChange = (event: { page: number; rows: number }) => {
  currentPage.value = event.page + 1
  pageSize.value = event.rows
  loadDisputes()
}

// =========================================================================
// FILTERS
// =========================================================================

const applyFilters = () => {
  currentPage.value = 1
  loadDisputes()
}

const clearFilters = () => {
  selectedState.value = null
  orderIdFilter.value = ''
  currentPage.value = 1
  loadDisputes()
}

// =========================================================================
// HELPERS
// =========================================================================

const formatCurrency = (amount: number | null, currency: string | null): string => {
  if (!amount) return '-'
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: currency || 'EUR'
  }).format(amount)
}

const getRowClass = (dispute: EbayPaymentDispute): string => {
  if (dispute.is_past_due) {
    return 'bg-red-50 dark:bg-red-900/20'
  }
  if (dispute.needs_action || dispute.dispute_state === 'ACTION_NEEDED') {
    return 'bg-orange-50 dark:bg-orange-900/20'
  }
  return ''
}

const getDeadlineClass = (dispute: EbayPaymentDispute): string => {
  const days = getDaysUntilDeadline(dispute)
  if (days === null) return ''
  if (days < 0) return 'text-red-600 font-bold'
  if (days <= 2) return 'text-orange-600 font-bold'
  if (days <= 5) return 'text-yellow-600'
  return 'text-gray-600'
}

const formatDeadline = (dispute: EbayPaymentDispute): string => {
  const days = getDaysUntilDeadline(dispute)
  if (days === null) return '-'
  if (days < 0) return `${Math.abs(days)}j en retard`
  if (days === 0) return "Aujourd'hui"
  if (days === 1) return 'Demain'
  return `${days} jours`
}

// =========================================================================
// LIFECYCLE
// =========================================================================

onMounted(async () => {
  await Promise.all([loadDisputes(), loadStatistics()])
})
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Litiges de Paiement eBay
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Gérez les litiges et réclamations de paiement
        </p>
      </div>
      <Button
        label="Synchroniser"
        icon="pi pi-refresh"
        :loading="syncing"
        @click="handleSync"
      />
    </div>

    <!-- Statistics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <Card class="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="p-3 bg-blue-100 dark:bg-blue-900/40 rounded-lg">
              <i class="pi pi-exclamation-circle text-blue-600 dark:text-blue-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-blue-600 dark:text-blue-400">Ouverts</p>
              <p class="text-2xl font-bold text-blue-700 dark:text-blue-300">
                {{ statistics?.open ?? '-' }}
              </p>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="p-3 bg-orange-100 dark:bg-orange-900/40 rounded-lg">
              <i class="pi pi-exclamation-triangle text-orange-600 dark:text-orange-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-orange-600 dark:text-orange-400">Action requise</p>
              <p class="text-2xl font-bold text-orange-700 dark:text-orange-300">
                {{ statistics?.action_needed ?? '-' }}
              </p>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="p-3 bg-green-100 dark:bg-green-900/40 rounded-lg">
              <i class="pi pi-check-circle text-green-600 dark:text-green-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-green-600 dark:text-green-400">Fermés</p>
              <p class="text-2xl font-bold text-green-700 dark:text-green-300">
                {{ statistics?.closed ?? '-' }}
              </p>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="p-3 bg-purple-100 dark:bg-purple-900/40 rounded-lg">
              <i class="pi pi-euro text-purple-600 dark:text-purple-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-purple-600 dark:text-purple-400">Total contesté</p>
              <p class="text-xl font-bold text-purple-700 dark:text-purple-300">
                {{ formatCurrency(statistics?.total_disputed ?? null, 'EUR') }}
              </p>
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Filters -->
    <Card class="mb-6">
      <template #content>
        <div class="flex flex-wrap items-end gap-4">
          <div class="flex-1 min-w-[200px]">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              État
            </label>
            <Dropdown
              v-model="selectedState"
              :options="stateOptions"
              option-label="label"
              option-value="value"
              placeholder="Tous les états"
              class="w-full"
            />
          </div>

          <div class="flex-1 min-w-[200px]">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              N° Commande
            </label>
            <InputText
              v-model="orderIdFilter"
              placeholder="Rechercher par n° commande"
              class="w-full"
              @keyup.enter="applyFilters"
            />
          </div>

          <div class="flex gap-2">
            <Button
              label="Filtrer"
              icon="pi pi-filter"
              @click="applyFilters"
            />
            <Button
              label="Effacer"
              icon="pi pi-filter-slash"
              severity="secondary"
              outlined
              @click="clearFilters"
            />
          </div>
        </div>
      </template>
    </Card>

    <!-- Data Table -->
    <Card>
      <template #content>
        <DataTable
          :value="disputes"
          :loading="loading"
          :row-class="getRowClass"
          striped-rows
          responsive-layout="scroll"
          class="cursor-pointer"
          @row-click="(e) => viewDispute(e.data)"
        >
          <template #empty>
            <div class="text-center py-8 text-gray-500 dark:text-gray-400">
              <i class="pi pi-inbox text-4xl mb-3" />
              <p>Aucun litige de paiement trouvé</p>
            </div>
          </template>

          <Column field="dispute_id" header="ID Litige" style="min-width: 150px">
            <template #body="{ data }">
              <span class="font-mono text-sm">{{ data.dispute_id }}</span>
            </template>
          </Column>

          <Column field="order_id" header="N° Commande" style="min-width: 150px">
            <template #body="{ data }">
              <span class="font-mono text-sm">{{ data.order_id || '-' }}</span>
            </template>
          </Column>

          <Column field="dispute_state" header="État" style="min-width: 140px">
            <template #body="{ data }">
              <Tag
                :value="getStateLabel(data.dispute_state)"
                :severity="getStateSeverity(data.dispute_state)"
              >
                <template #default>
                  <i :class="getStateIcon(data.dispute_state)" class="mr-1" />
                  {{ getStateLabel(data.dispute_state) }}
                </template>
              </Tag>
            </template>
          </Column>

          <Column field="dispute_reason" header="Raison" style="min-width: 180px">
            <template #body="{ data }">
              <span class="text-sm">{{ getReasonLabel(data.dispute_reason) }}</span>
            </template>
          </Column>

          <Column field="dispute_amount" header="Montant" style="min-width: 120px">
            <template #body="{ data }">
              <span class="font-medium text-red-600 dark:text-red-400">
                {{ formatAmount(data) }}
              </span>
            </template>
          </Column>

          <Column field="buyer_username" header="Acheteur" style="min-width: 120px">
            <template #body="{ data }">
              <span class="text-sm">{{ data.buyer_username || '-' }}</span>
            </template>
          </Column>

          <Column field="response_due_date" header="Deadline" style="min-width: 120px">
            <template #body="{ data }">
              <span :class="getDeadlineClass(data)">
                {{ formatDeadline(data) }}
              </span>
            </template>
          </Column>

          <Column field="seller_response" header="Réponse" style="min-width: 120px">
            <template #body="{ data }">
              <Tag
                v-if="data.seller_response"
                :value="data.seller_response === 'CONTEST' ? 'Contesté' : 'Accepté'"
                :severity="data.seller_response === 'CONTEST' ? 'warn' : 'info'"
              />
              <span v-else class="text-gray-400 text-sm">-</span>
            </template>
          </Column>

          <Column field="creation_date" header="Date" style="min-width: 150px">
            <template #body="{ data }">
              <span class="text-sm">{{ formatDate(data.creation_date) }}</span>
            </template>
          </Column>

          <Column header="Actions" style="min-width: 80px" :exportable="false">
            <template #body="{ data }">
              <div class="flex items-center gap-2">
                <Button
                  icon="pi pi-eye"
                  severity="secondary"
                  text
                  rounded
                  @click.stop="viewDispute(data)"
                />
                <i
                  v-if="isUrgent(data)"
                  class="pi pi-exclamation-triangle text-orange-500"
                  v-tooltip.top="'Action urgente requise'"
                />
              </div>
            </template>
          </Column>
        </DataTable>

        <!-- Pagination -->
        <Paginator
          v-if="totalRecords > 0"
          :rows="pageSize"
          :total-records="totalRecords"
          :rows-per-page-options="[10, 20, 50, 100]"
          :first="(currentPage - 1) * pageSize"
          class="mt-4"
          @page="onPageChange"
        />
      </template>
    </Card>
  </div>
</template>

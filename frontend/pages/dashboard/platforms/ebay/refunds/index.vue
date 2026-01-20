<!--
  ╔═══════════════════════════════════════════════════════════════╗
  ║  🚧 PMV2 - Cette page est cachée pour la phase 1              ║
  ║                                                               ║
  ║  Pour activer: useFeatureFlags.ts → ebayPostSale: true        ║
  ╚═══════════════════════════════════════════════════════════════╝
-->
<script setup lang="ts">
import { ebayLogger } from '~/utils/logger'
/**
 * eBay Refunds List Page
 *
 * Displays all refunds with filtering, statistics, and actions.
 */

import type { EbayRefund, EbayRefundStatistics } from '~/types/ebay'

definePageMeta({
  layout: 'dashboard',
})

const toast = useAppToast()
const router = useRouter()

const {
  fetchRefunds,
  fetchStatistics,
  syncRefunds,
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

const refunds = ref<EbayRefund[]>([])
const statistics = ref<EbayRefundStatistics | null>(null)
const loading = ref(false)
const syncing = ref(false)
const totalRecords = ref(0)

// Pagination
const currentPage = ref(1)
const pageSize = ref(20)

// Filters
const selectedStatus = ref<'PENDING' | 'REFUNDED' | 'FAILED' | null>(null)
const selectedSource = ref<'RETURN' | 'CANCELLATION' | 'MANUAL' | 'OTHER' | null>(null)
const orderIdFilter = ref<string>('')

// Filter options
const statusOptions = [
  { label: 'Tous les statuts', value: null },
  { label: 'En attente', value: 'PENDING' },
  { label: 'Remboursé', value: 'REFUNDED' },
  { label: 'Échoué', value: 'FAILED' }
]

const sourceOptions = [
  { label: 'Toutes les sources', value: null },
  { label: 'Retour', value: 'RETURN' },
  { label: 'Annulation', value: 'CANCELLATION' },
  { label: 'Manuel', value: 'MANUAL' },
  { label: 'Autre', value: 'OTHER' }
]

// =========================================================================
// DATA FETCHING
// =========================================================================

const loadRefunds = async () => {
  loading.value = true
  try {
    const response = await fetchRefunds({
      page: currentPage.value,
      page_size: pageSize.value,
      status: selectedStatus.value,
      source: selectedSource.value,
      order_id: orderIdFilter.value || null
    })
    refunds.value = response.items
    totalRecords.value = response.total
  } catch (error) {
    ebayLogger.error('Failed to load refunds:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de charger les remboursements',
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
    ebayLogger.error('Failed to load statistics:', error)
  }
}

const handleSync = async () => {
  syncing.value = true
  try {
    const result = await syncRefunds({ days_back: 30 })
    toast.add({
      severity: 'success',
      summary: 'Synchronisation terminée',
      detail: `${result.created} créés, ${result.updated} mis à jour`,
      life: 5000
    })
    // Reload data
    await Promise.all([loadRefunds(), loadStatistics()])
  } catch (error) {
    ebayLogger.error('Sync failed:', error)
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

const viewRefund = (refund: EbayRefund) => {
  router.push(`/dashboard/platforms/ebay/refunds/${refund.id}`)
}

// =========================================================================
// PAGINATION
// =========================================================================

const onPageChange = (event: { page: number; rows: number }) => {
  currentPage.value = event.page + 1
  pageSize.value = event.rows
  loadRefunds()
}

// =========================================================================
// FILTERS
// =========================================================================

const applyFilters = () => {
  currentPage.value = 1
  loadRefunds()
}

const clearFilters = () => {
  selectedStatus.value = null
  selectedSource.value = null
  orderIdFilter.value = ''
  currentPage.value = 1
  loadRefunds()
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

const getRowClass = (refund: EbayRefund): string => {
  if (refund.is_failed) {
    return 'bg-red-50 dark:bg-red-900/20'
  }
  if (refund.is_pending) {
    return 'bg-yellow-50 dark:bg-yellow-900/20'
  }
  return ''
}

// =========================================================================
// LIFECYCLE
// =========================================================================

onMounted(async () => {
  await Promise.all([loadRefunds(), loadStatistics()])
})
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Remboursements eBay
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Suivez et gérez les remboursements de vos commandes eBay
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
    <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
      <Card class="bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="p-3 bg-yellow-100 dark:bg-yellow-900/40 rounded-lg">
              <i class="pi pi-clock text-yellow-600 dark:text-yellow-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-yellow-600 dark:text-yellow-400">En attente</p>
              <p class="text-2xl font-bold text-yellow-700 dark:text-yellow-300">
                {{ statistics?.pending ?? '-' }}
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
              <p class="text-sm text-green-600 dark:text-green-400">Remboursés</p>
              <p class="text-2xl font-bold text-green-700 dark:text-green-300">
                {{ statistics?.completed ?? '-' }}
              </p>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="p-3 bg-red-100 dark:bg-red-900/40 rounded-lg">
              <i class="pi pi-times-circle text-red-600 dark:text-red-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-red-600 dark:text-red-400">Échoués</p>
              <p class="text-2xl font-bold text-red-700 dark:text-red-300">
                {{ statistics?.failed ?? '-' }}
              </p>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="p-3 bg-blue-100 dark:bg-blue-900/40 rounded-lg">
              <i class="pi pi-euro text-blue-600 dark:text-blue-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-blue-600 dark:text-blue-400">Total remboursé</p>
              <p class="text-xl font-bold text-blue-700 dark:text-blue-300">
                {{ formatCurrency(statistics?.total_refunded ?? null, 'EUR') }}
              </p>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800">
        <template #content>
          <div class="flex flex-col gap-2">
            <p class="text-sm text-purple-600 dark:text-purple-400 font-medium">Par source</p>
            <div class="flex flex-wrap gap-2 text-xs">
              <span class="px-2 py-1 bg-purple-100 dark:bg-purple-900/40 rounded text-purple-700 dark:text-purple-300">
                <i class="pi pi-replay mr-1" />
                {{ statistics?.by_source?.RETURN ?? 0 }} retours
              </span>
              <span class="px-2 py-1 bg-purple-100 dark:bg-purple-900/40 rounded text-purple-700 dark:text-purple-300">
                <i class="pi pi-times-circle mr-1" />
                {{ statistics?.by_source?.CANCELLATION ?? 0 }} annul.
              </span>
              <span class="px-2 py-1 bg-purple-100 dark:bg-purple-900/40 rounded text-purple-700 dark:text-purple-300">
                <i class="pi pi-user mr-1" />
                {{ statistics?.by_source?.MANUAL ?? 0 }} manuels
              </span>
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
              Statut
            </label>
            <Dropdown
              v-model="selectedStatus"
              :options="statusOptions"
              option-label="label"
              option-value="value"
              placeholder="Tous les statuts"
              class="w-full"
            />
          </div>

          <div class="flex-1 min-w-[200px]">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Source
            </label>
            <Dropdown
              v-model="selectedSource"
              :options="sourceOptions"
              option-label="label"
              option-value="value"
              placeholder="Toutes les sources"
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
          :value="refunds"
          :loading="loading"
          :row-class="getRowClass"
          striped-rows
          responsive-layout="scroll"
          class="cursor-pointer"
          @row-click="(e) => viewRefund(e.data)"
        >
          <template #empty>
            <div class="text-center py-8 text-gray-500 dark:text-gray-400">
              <i class="pi pi-inbox text-4xl mb-3" />
              <p>Aucun remboursement trouvé</p>
            </div>
          </template>

          <Column field="refund_id" header="ID Remboursement" style="min-width: 150px">
            <template #body="{ data }">
              <span class="font-mono text-sm">{{ data.refund_id }}</span>
            </template>
          </Column>

          <Column field="order_id" header="N° Commande" style="min-width: 150px">
            <template #body="{ data }">
              <span class="font-mono text-sm">{{ data.order_id || '-' }}</span>
            </template>
          </Column>

          <Column field="refund_source" header="Source" style="min-width: 120px">
            <template #body="{ data }">
              <Tag
                :value="getSourceLabel(data.refund_source)"
                :severity="getSourceSeverity(data.refund_source)"
              >
                <template #default>
                  <i :class="getSourceIcon(data.refund_source)" class="mr-1" />
                  {{ getSourceLabel(data.refund_source) }}
                </template>
              </Tag>
            </template>
          </Column>

          <Column field="refund_status" header="Statut" style="min-width: 120px">
            <template #body="{ data }">
              <Tag
                :value="getStatusLabel(data.refund_status)"
                :severity="getStatusSeverity(data.refund_status)"
              />
            </template>
          </Column>

          <Column field="refund_amount" header="Montant" style="min-width: 120px">
            <template #body="{ data }">
              <span class="font-medium">{{ formatAmount(data) }}</span>
            </template>
          </Column>

          <Column field="reason" header="Raison" style="min-width: 150px">
            <template #body="{ data }">
              <span class="text-sm">{{ getReasonLabel(data.reason) }}</span>
            </template>
          </Column>

          <Column field="buyer_username" header="Acheteur" style="min-width: 120px">
            <template #body="{ data }">
              <span class="text-sm">{{ data.buyer_username || '-' }}</span>
            </template>
          </Column>

          <Column field="refund_date" header="Date" style="min-width: 150px">
            <template #body="{ data }">
              <span class="text-sm">{{ formatDate(data.refund_date) }}</span>
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
                  @click.stop="viewRefund(data)"
                />
                <i
                  v-if="data.is_failed"
                  class="pi pi-exclamation-triangle text-red-500"
                  v-tooltip.top="'Remboursement échoué'"
                />
                <i
                  v-else-if="data.is_pending"
                  class="pi pi-clock text-yellow-500"
                  v-tooltip.top="'En attente'"
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

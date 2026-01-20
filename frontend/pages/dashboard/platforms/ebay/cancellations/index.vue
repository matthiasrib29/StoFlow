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
 * eBay Cancellations List Page
 *
 * Displays all cancellations with filtering, statistics, and actions.
 */

import type { EbayCancellation, EbayCancellationStatistics } from '~/types/ebay'

definePageMeta({
  layout: 'dashboard',
})

const toast = useAppToast()
const router = useRouter()

const {
  fetchCancellations,
  fetchStatistics,
  syncCancellations,
  getStatusLabel,
  getStatusSeverity,
  getReasonLabel,
  getRequestorLabel,
  getRequestorSeverity,
  getStateLabel,
  getStateSeverity,
  formatRefundAmount,
  requiresAction
} = useEbayCancellations()

// =========================================================================
// STATE
// =========================================================================

const cancellations = ref<EbayCancellation[]>([])
const statistics = ref<EbayCancellationStatistics | null>(null)
const loading = ref(false)
const syncing = ref(false)
const totalRecords = ref(0)

// Pagination
const currentPage = ref(1)
const pageSize = ref(20)

// Filters
const selectedState = ref<'CLOSED' | null>(null)
const selectedStatus = ref<string | null>(null)
const orderIdFilter = ref<string>('')

// Filter options
const stateOptions = [
  { label: 'Toutes', value: null },
  { label: 'Actives', value: null },
  { label: 'Fermées', value: 'CLOSED' as const }
]

const statusOptions = [
  { label: 'Tous les statuts', value: null },
  { label: 'Demandée', value: 'CANCEL_REQUESTED' },
  { label: 'En attente', value: 'CANCEL_PENDING' },
  { label: 'Approuvée (remboursé)', value: 'CANCEL_CLOSED_WITH_REFUND' },
  { label: 'Approuvée (remb. inconnu)', value: 'CANCEL_CLOSED_UNKNOWN_REFUND' },
  { label: 'Approuvée (sans remb.)', value: 'CANCEL_CLOSED_NO_REFUND' },
  { label: 'Rejetée', value: 'CANCEL_REJECTED' }
]

// =========================================================================
// DATA FETCHING
// =========================================================================

const loadCancellations = async () => {
  loading.value = true
  try {
    const response = await fetchCancellations({
      page: currentPage.value,
      page_size: pageSize.value,
      state: selectedState.value,
      status: selectedStatus.value,
      order_id: orderIdFilter.value || null
    })
    cancellations.value = response.items
    totalRecords.value = response.total
  } catch (error) {
    ebayLogger.error('Failed to load cancellations:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de charger les annulations',
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
    const result = await syncCancellations({ days_back: 30 })
    toast.add({
      severity: 'success',
      summary: 'Synchronisation terminée',
      detail: `${result.created} créées, ${result.updated} mises à jour`,
      life: 5000
    })
    // Reload data
    await Promise.all([loadCancellations(), loadStatistics()])
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

const viewCancellation = (cancellation: EbayCancellation) => {
  router.push(`/dashboard/platforms/ebay/cancellations/${cancellation.id}`)
}

// =========================================================================
// PAGINATION
// =========================================================================

const onPageChange = (event: { page: number; rows: number }) => {
  currentPage.value = event.page + 1
  pageSize.value = event.rows
  loadCancellations()
}

// =========================================================================
// FILTERS
// =========================================================================

const applyFilters = () => {
  currentPage.value = 1
  loadCancellations()
}

const clearFilters = () => {
  selectedState.value = null
  selectedStatus.value = null
  orderIdFilter.value = ''
  currentPage.value = 1
  loadCancellations()
}

// =========================================================================
// HELPERS
// =========================================================================

const formatDate = (dateString: string | null): string => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getRowClass = (cancellation: EbayCancellation): string => {
  if (requiresAction(cancellation)) {
    return 'bg-orange-50 dark:bg-orange-900/20'
  }
  return ''
}

// =========================================================================
// LIFECYCLE
// =========================================================================

onMounted(async () => {
  await Promise.all([loadCancellations(), loadStatistics()])
})
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Annulations eBay
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Gérez les demandes d'annulation de vos commandes eBay
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

      <Card class="bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="p-3 bg-orange-100 dark:bg-orange-900/40 rounded-lg">
              <i class="pi pi-exclamation-triangle text-orange-600 dark:text-orange-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-orange-600 dark:text-orange-400">Action requise</p>
              <p class="text-2xl font-bold text-orange-700 dark:text-orange-300">
                {{ statistics?.needs_action ?? '-' }}
              </p>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="p-3 bg-red-100 dark:bg-red-900/40 rounded-lg">
              <i class="pi pi-calendar-times text-red-600 dark:text-red-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-red-600 dark:text-red-400">En retard</p>
              <p class="text-2xl font-bold text-red-700 dark:text-red-300">
                {{ statistics?.past_due ?? '-' }}
              </p>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
        <template #content>
          <div class="flex items-center gap-3">
            <div class="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
              <i class="pi pi-check-circle text-gray-600 dark:text-gray-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-gray-600 dark:text-gray-400">Fermées</p>
              <p class="text-2xl font-bold text-gray-700 dark:text-gray-300">
                {{ statistics?.closed ?? '-' }}
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
              placeholder="Toutes"
              class="w-full"
            />
          </div>

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
          :value="cancellations"
          :loading="loading"
          :row-class="getRowClass"
          striped-rows
          responsive-layout="scroll"
          class="cursor-pointer"
          @row-click="(e) => viewCancellation(e.data)"
        >
          <template #empty>
            <div class="text-center py-8 text-gray-500 dark:text-gray-400">
              <i class="pi pi-inbox text-4xl mb-3" />
              <p>Aucune annulation trouvée</p>
            </div>
          </template>

          <Column field="cancel_id" header="ID Annulation" style="min-width: 150px">
            <template #body="{ data }">
              <span class="font-mono text-sm">{{ data.cancel_id }}</span>
            </template>
          </Column>

          <Column field="order_id" header="N° Commande" style="min-width: 150px">
            <template #body="{ data }">
              <span class="font-mono text-sm">{{ data.order_id || '-' }}</span>
            </template>
          </Column>

          <Column field="requestor_role" header="Demandeur" style="min-width: 100px">
            <template #body="{ data }">
              <Tag
                :value="getRequestorLabel(data.requestor_role)"
                :severity="getRequestorSeverity(data.requestor_role)"
              />
            </template>
          </Column>

          <Column field="cancel_status" header="Statut" style="min-width: 180px">
            <template #body="{ data }">
              <Tag
                :value="getStatusLabel(data.cancel_status)"
                :severity="getStatusSeverity(data.cancel_status)"
              />
            </template>
          </Column>

          <Column field="cancel_reason" header="Raison" style="min-width: 150px">
            <template #body="{ data }">
              <span class="text-sm">{{ getReasonLabel(data.cancel_reason) }}</span>
            </template>
          </Column>

          <Column field="refund_amount" header="Remboursement" style="min-width: 120px">
            <template #body="{ data }">
              <span class="font-medium">{{ formatRefundAmount(data) }}</span>
            </template>
          </Column>

          <Column field="request_date" header="Date demande" style="min-width: 150px">
            <template #body="{ data }">
              <span class="text-sm">{{ formatDate(data.request_date) }}</span>
            </template>
          </Column>

          <Column field="response_due_date" header="Date limite" style="min-width: 150px">
            <template #body="{ data }">
              <span
                class="text-sm"
                :class="{
                  'text-red-600 dark:text-red-400 font-medium': data.is_past_response_due
                }"
              >
                {{ formatDate(data.response_due_date) }}
                <i
                  v-if="data.is_past_response_due"
                  class="pi pi-exclamation-circle ml-1"
                />
              </span>
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
                  @click.stop="viewCancellation(data)"
                />
                <i
                  v-if="requiresAction(data)"
                  class="pi pi-bell text-orange-500"
                  v-tooltip.top="'Action requise'"
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

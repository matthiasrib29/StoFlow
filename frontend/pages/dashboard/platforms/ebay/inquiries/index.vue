<!--
  ╔═══════════════════════════════════════════════════════════════╗
  ║  🚧 PMV2 - Cette page est cachée pour la phase 1              ║
  ║                                                               ║
  ║  Pour activer: useFeatureFlags.ts → ebayPostSale: true        ║
  ╚═══════════════════════════════════════════════════════════════╝
-->
<script setup lang="ts">
/**
 * eBay INR Inquiries List Page
 *
 * Displays all INR (Item Not Received) inquiries with filtering, statistics, and actions.
 */

import type { EbayInquiry, EbayInquiryStatistics } from '~/types/ebay'

definePageMeta({
  layout: 'dashboard',
})

const toast = useAppToast()
const router = useRouter()

const {
  fetchInquiries,
  fetchStatistics,
  syncInquiries,
  getStateLabel,
  getStateSeverity,
  getStatusLabel,
  getStatusSeverity,
  getStateIcon,
  formatAmount,
  formatDate,
  isUrgent,
  getDaysUntilDeadline
} = useEbayInquiries()

// =========================================================================
// STATE
// =========================================================================

const inquiries = ref<EbayInquiry[]>([])
const statistics = ref<EbayInquiryStatistics | null>(null)
const loading = ref(false)
const syncing = ref(false)
const totalRecords = ref(0)

// Pagination
const currentPage = ref(1)
const pageSize = ref(20)

// Filters
const selectedState = ref<'OPEN' | 'CLOSED' | null>(null)
const orderIdFilter = ref<string>('')

// Filter options
const stateOptions = [
  { label: 'Tous les états', value: null },
  { label: 'Ouvert', value: 'OPEN' },
  { label: 'Fermé', value: 'CLOSED' }
]

// =========================================================================
// DATA FETCHING
// =========================================================================

const loadInquiries = async () => {
  loading.value = true
  try {
    const response = await fetchInquiries({
      page: currentPage.value,
      page_size: pageSize.value,
      state: selectedState.value,
      order_id: orderIdFilter.value || null
    })
    inquiries.value = response.items
    totalRecords.value = response.total
  } catch (error) {
    console.error('Failed to load inquiries:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de charger les réclamations',
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
    const result = await syncInquiries()
    toast.add({
      severity: 'success',
      summary: 'Synchronisation terminée',
      detail: `${result.created} créées, ${result.updated} mises à jour`,
      life: 5000
    })
    // Reload data
    await Promise.all([loadInquiries(), loadStatistics()])
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

const viewInquiry = (inquiry: EbayInquiry) => {
  router.push(`/dashboard/platforms/ebay/inquiries/${inquiry.id}`)
}

// =========================================================================
// PAGINATION
// =========================================================================

const onPageChange = (event: { page: number; rows: number }) => {
  currentPage.value = event.page + 1
  pageSize.value = event.rows
  loadInquiries()
}

// =========================================================================
// FILTERS
// =========================================================================

const applyFilters = () => {
  currentPage.value = 1
  loadInquiries()
}

const clearFilters = () => {
  selectedState.value = null
  orderIdFilter.value = ''
  currentPage.value = 1
  loadInquiries()
}

// =========================================================================
// HELPERS
// =========================================================================

const getRowClass = (inquiry: EbayInquiry): string => {
  if (inquiry.is_past_due) {
    return 'bg-red-50 dark:bg-red-900/20'
  }
  if (inquiry.needs_action) {
    return 'bg-orange-50 dark:bg-orange-900/20'
  }
  if (inquiry.is_escalated) {
    return 'bg-purple-50 dark:bg-purple-900/20'
  }
  return ''
}

const getDeadlineClass = (inquiry: EbayInquiry): string => {
  const days = getDaysUntilDeadline(inquiry)
  if (days === null) return ''
  if (days < 0) return 'text-red-600 font-bold'
  if (days <= 2) return 'text-orange-600 font-bold'
  if (days <= 5) return 'text-yellow-600'
  return 'text-gray-600'
}

const formatDeadline = (inquiry: EbayInquiry): string => {
  const days = getDaysUntilDeadline(inquiry)
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
  await Promise.all([loadInquiries(), loadStatistics()])
})
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Réclamations INR eBay
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Gérez les réclamations "Article non reçu"
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
              <i class="pi pi-exclamation-circle text-yellow-600 dark:text-yellow-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-yellow-600 dark:text-yellow-400">Ouvertes</p>
              <p class="text-2xl font-bold text-yellow-700 dark:text-yellow-300">
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
              <i class="pi pi-clock text-orange-600 dark:text-orange-400 text-xl" />
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
              <i class="pi pi-exclamation-triangle text-red-600 dark:text-red-400 text-xl" />
            </div>
            <div>
              <p class="text-sm text-red-600 dark:text-red-400">En retard</p>
              <p class="text-2xl font-bold text-red-700 dark:text-red-300">
                {{ statistics?.past_deadline ?? '-' }}
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
              <p class="text-sm text-green-600 dark:text-green-400">Fermées</p>
              <p class="text-2xl font-bold text-green-700 dark:text-green-300">
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
          :value="inquiries"
          :loading="loading"
          :row-class="getRowClass"
          striped-rows
          responsive-layout="scroll"
          class="cursor-pointer"
          @row-click="(e) => viewInquiry(e.data)"
        >
          <template #empty>
            <div class="text-center py-8 text-gray-500 dark:text-gray-400">
              <i class="pi pi-inbox text-4xl mb-3" />
              <p>Aucune réclamation INR trouvée</p>
            </div>
          </template>

          <Column field="inquiry_id" header="ID Réclamation" style="min-width: 150px">
            <template #body="{ data }">
              <span class="font-mono text-sm">{{ data.inquiry_id }}</span>
            </template>
          </Column>

          <Column field="order_id" header="N° Commande" style="min-width: 150px">
            <template #body="{ data }">
              <span class="font-mono text-sm">{{ data.order_id || '-' }}</span>
            </template>
          </Column>

          <Column field="inquiry_state" header="État" style="min-width: 120px">
            <template #body="{ data }">
              <Tag
                :value="getStateLabel(data.inquiry_state)"
                :severity="getStateSeverity(data.inquiry_state)"
              >
                <template #default>
                  <i :class="getStateIcon(data.inquiry_state)" class="mr-1" />
                  {{ getStateLabel(data.inquiry_state) }}
                </template>
              </Tag>
            </template>
          </Column>

          <Column field="inquiry_status" header="Statut" style="min-width: 180px">
            <template #body="{ data }">
              <Tag
                :value="getStatusLabel(data.inquiry_status)"
                :severity="getStatusSeverity(data.inquiry_status)"
              >
                {{ getStatusLabel(data.inquiry_status) }}
              </Tag>
            </template>
          </Column>

          <Column field="claim_amount" header="Montant" style="min-width: 120px">
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

          <Column field="respond_by_date" header="Deadline" style="min-width: 120px">
            <template #body="{ data }">
              <span :class="getDeadlineClass(data)">
                {{ formatDeadline(data) }}
              </span>
            </template>
          </Column>

          <Column field="item_title" header="Article" style="min-width: 200px">
            <template #body="{ data }">
              <span class="text-sm truncate max-w-[200px] block">
                {{ data.item_title || '-' }}
              </span>
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
                  @click.stop="viewInquiry(data)"
                />
                <i
                  v-if="isUrgent(data)"
                  class="pi pi-exclamation-triangle text-orange-500"
                  v-tooltip.top="'Action urgente requise'"
                />
                <i
                  v-if="data.is_escalated"
                  class="pi pi-arrow-up text-purple-500"
                  v-tooltip.top="'Escaladé'"
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

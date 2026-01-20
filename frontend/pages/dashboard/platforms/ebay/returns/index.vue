<!--
  ╔═══════════════════════════════════════════════════════════════╗
  ║  🚧 PMV2 - Cette page est cachée pour la phase 1              ║
  ║                                                               ║
  ║  Pour activer: useFeatureFlags.ts → ebayPostSale: true        ║
  ╚═══════════════════════════════════════════════════════════════╝
-->
<template>
  <PlatformOrdersPage
    platform="ebay"
    :is-connected="isConnected"
    :loading="loading"
    :error="error"
    :is-empty="isEmpty"
    empty-message="Aucun retour trouvé"
    back-to="/dashboard/platforms"
    @retry="fetchReturns"
  >
    <!-- Header Actions -->
    <template #header-actions>
      <div class="flex gap-2">
        <!-- Sync button -->
        <Button
          label="Synchroniser"
          icon="pi pi-sync"
          :loading="isSyncing"
          :disabled="!isConnected"
          class="bg-platform-ebay hover:bg-blue-700 text-white border-0"
          @click="triggerSync"
        />

        <!-- Refresh button -->
        <Button
          label="Rafraîchir"
          icon="pi pi-refresh"
          :loading="refreshing"
          :disabled="!isConnected"
          class="bg-gray-500 hover:bg-gray-600 text-white border-0"
          @click="fetchReturns"
        />
      </div>
    </template>

    <!-- Stats Cards -->
    <template #stats>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 mb-1">Ouverts</p>
                <p class="text-2xl font-bold text-amber-600">{{ stats.open }}</p>
              </div>
              <i class="pi pi-undo text-3xl text-amber-600" />
            </div>
          </template>
        </Card>

        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 mb-1">Action requise</p>
                <p class="text-2xl font-bold text-red-600">{{ stats.needs_action }}</p>
              </div>
              <i class="pi pi-exclamation-triangle text-3xl text-red-600" />
            </div>
          </template>
        </Card>

        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 mb-1">En retard</p>
                <p class="text-2xl font-bold text-red-500">{{ stats.past_deadline }}</p>
              </div>
              <i class="pi pi-clock text-3xl text-red-500" />
            </div>
          </template>
        </Card>

        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 mb-1">Fermés</p>
                <p class="text-2xl font-bold text-gray-600">{{ stats.closed }}</p>
              </div>
              <i class="pi pi-check-circle text-3xl text-gray-600" />
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
              placeholder="Rechercher par ID retour, commande, acheteur..."
              class="w-full"
            />
          </IconField>
        </div>
        <div class="flex gap-2">
          <Select
            v-model="stateFilter"
            :options="stateOptions"
            option-label="label"
            option-value="value"
            placeholder="État"
            class="w-full md:w-36"
            show-clear
          />
          <Select
            v-model="statusFilter"
            :options="statusOptions"
            option-label="label"
            option-value="value"
            placeholder="Statut"
            class="w-full md:w-48"
            show-clear
          />
        </div>
      </div>
    </template>

    <!-- Returns DataTable -->
    <template #content>
      <EbayReturnsDataTable
        :returns="filteredReturns"
        :total-records="pagination.total"
        :current-page="pagination.page"
        :rows-per-page="pagination.page_size"
        :loading="loading"
        @page="onPageChange"
        @row-click="onRowClick"
        @view="viewDetails"
        @sync="triggerSync"
      />
    </template>

    <!-- Empty Actions -->
    <template #empty-actions>
      <Button
        v-if="isConnected"
        label="Synchroniser les retours"
        icon="pi pi-sync"
        class="mt-4 bg-platform-ebay hover:bg-blue-700 text-white border-0"
        @click="triggerSync"
      />
    </template>
  </PlatformOrdersPage>
</template>

<script setup lang="ts">
import { ebayLogger } from '~/utils/logger'
import type { EbayReturn, EbayReturnStatistics, EbayReturnStatus } from '~/types/ebay'

definePageMeta({
  layout: 'dashboard'
})

// Platform connection
const { isConnected, fetchStatus } = usePlatformConnection('ebay')

// Toast notifications
const { showSuccess, showError, showInfo } = useAppToast()

// Composable
const {
  fetchReturns: apiFetchReturns,
  fetchStatistics,
  syncReturns: apiSyncReturns
} = useEbayReturns()

// State
const loading = ref(false)
const refreshing = ref(false)
const isSyncing = ref(false)
const error = ref<string | null>(null)
const returns = ref<EbayReturn[]>([])
const searchQuery = ref('')
const stateFilter = ref<'OPEN' | 'CLOSED' | null>(null)
const statusFilter = ref<EbayReturnStatus | null>(null)

// Stats
const stats = ref<EbayReturnStatistics>({
  open: 0,
  closed: 0,
  needs_action: 0,
  past_deadline: 0
})

// Pagination
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

// Computed
const isEmpty = computed(() => returns.value.length === 0 && !loading.value)

const filteredReturns = computed(() => {
  return returns.value.filter(ret => {
    // Filter by search query
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      if (
        !ret.return_id.toLowerCase().includes(query) &&
        !(ret.order_id?.toLowerCase().includes(query)) &&
        !(ret.buyer_username?.toLowerCase().includes(query))
      ) {
        return false
      }
    }

    // Filter by state
    if (stateFilter.value && ret.state !== stateFilter.value) {
      return false
    }

    // Filter by status
    if (statusFilter.value && ret.status !== statusFilter.value) {
      return false
    }

    return true
  })
})

// Filter options
const stateOptions = [
  { label: 'Ouverts', value: 'OPEN' },
  { label: 'Fermés', value: 'CLOSED' }
]

const statusOptions = [
  { label: 'Demandé', value: 'RETURN_REQUESTED' },
  { label: 'Attente RMA', value: 'RETURN_WAITING_FOR_RMA' },
  { label: 'Accepté', value: 'RETURN_ACCEPTED' },
  { label: 'Refusé', value: 'RETURN_DECLINED' },
  { label: 'Article expédié', value: 'RETURN_ITEM_SHIPPED' },
  { label: 'Article reçu', value: 'RETURN_ITEM_DELIVERED' },
  { label: 'Fermé', value: 'RETURN_CLOSED' },
  { label: 'Annulé', value: 'RETURN_CANCELLED' }
]

// Methods
const fetchReturns = async () => {
  if (!isConnected.value) return

  loading.value = true
  refreshing.value = true
  error.value = null

  try {
    const response = await apiFetchReturns({
      page: pagination.value.page,
      page_size: pagination.value.page_size
    })

    returns.value = response.items || []
    pagination.value = {
      page: response.page,
      page_size: response.page_size,
      total: response.total,
      total_pages: response.total_pages
    }

    // Fetch statistics
    await fetchStats()
  } catch (e: unknown) {
    const err = e as Error
    error.value = err.message || 'Erreur lors du chargement des retours'
    ebayLogger.error('Failed to fetch eBay returns:', e)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

const fetchStats = async () => {
  try {
    stats.value = await fetchStatistics()
  } catch (e) {
    ebayLogger.error('Failed to fetch return statistics:', e)
  }
}

const triggerSync = async () => {
  if (!isConnected.value) return

  isSyncing.value = true

  try {
    const response = await apiSyncReturns({
      days_back: 30
    })

    const created = response.created || 0
    const updated = response.updated || 0
    const errors = response.errors || 0

    if (created > 0 || updated > 0) {
      showSuccess(
        'Synchronisation terminée',
        `${created} retour(s) importé(s), ${updated} mise(s) à jour`,
        4000
      )

      // Refresh returns list
      await fetchReturns()
    } else if (errors > 0) {
      showError('Erreurs', `${errors} erreur(s) lors de la synchronisation`, 5000)
    } else {
      showInfo('Info', 'Aucun nouveau retour trouvé', 3000)
    }
  } catch (e: unknown) {
    const err = e as Error
    showError('Erreur', err.message || 'Impossible de synchroniser', 5000)
  } finally {
    isSyncing.value = false
  }
}

const onPageChange = (event: { page: number; rows: number }) => {
  pagination.value.page = event.page + 1
  pagination.value.page_size = event.rows
  fetchReturns()
}

const viewDetails = (returnItem: EbayReturn) => {
  navigateTo(`/dashboard/platforms/ebay/returns/${returnItem.id}`)
}

const onRowClick = (event: { data: EbayReturn }) => {
  viewDetails(event.data)
}

// Lifecycle
onMounted(async () => {
  await fetchStatus()
  if (isConnected.value) {
    await fetchReturns()
  }
})
</script>

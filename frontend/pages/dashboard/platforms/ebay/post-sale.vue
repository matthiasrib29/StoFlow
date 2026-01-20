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
 * eBay Post-Sale Dashboard Page
 *
 * Unified dashboard showing statistics, urgent items, and recent activity
 * across all post-sale domains: returns, cancellations, refunds, disputes, INR.
 */

import type {
  EbayDashboardStatistics,
  EbayUrgentItemsResponse,
  EbayRecentActivityResponse,
  EbayUrgentItem,
  EbayActivityItem
} from '~/types/ebay'

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth']
})

const toast = useToast()
const router = useRouter()

const {
  fetchStatistics,
  fetchUrgentItems,
  fetchRecentActivity,
  getTypeLabel,
  getTypeIcon,
  getTypeRoute,
  getUrgencySeverity,
  getUrgencyLabel,
  formatAmount,
  formatDate,
  getRelativeTime,
  getExternalId,
  getStatusDisplay
} = useEbayDashboard()

// =========================================================================
// STATE
// =========================================================================

const statistics = ref<EbayDashboardStatistics | null>(null)
const urgentItems = ref<EbayUrgentItemsResponse | null>(null)
const recentActivity = ref<EbayRecentActivityResponse | null>(null)
const loading = ref(true)

// =========================================================================
// DATA FETCHING
// =========================================================================

const loadDashboard = async () => {
  loading.value = true
  try {
    const [stats, urgent, activity] = await Promise.all([
      fetchStatistics(),
      fetchUrgentItems(10),
      fetchRecentActivity(15)
    ])
    statistics.value = stats
    urgentItems.value = urgent
    recentActivity.value = activity
  } catch (error) {
    ebayLogger.error('Failed to load dashboard:', error)
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: 'Impossible de charger le tableau de bord',
      life: 5000
    })
  } finally {
    loading.value = false
  }
}

// =========================================================================
// NAVIGATION
// =========================================================================

const navigateTo = (item: EbayUrgentItem | EbayActivityItem) => {
  const route = getTypeRoute(item.type, item.id)
  router.push(route)
}

const navigateToList = (type: string) => {
  const routes: Record<string, string> = {
    returns: '/dashboard/platforms/ebay/returns',
    cancellations: '/dashboard/platforms/ebay/cancellations',
    refunds: '/dashboard/platforms/ebay/refunds',
    payment_disputes: '/dashboard/platforms/ebay/payment-disputes',
    inquiries: '/dashboard/platforms/ebay/inquiries'
  }
  router.push(routes[type] || '/dashboard/platforms/ebay')
}

// =========================================================================
// COMPUTED
// =========================================================================

const allUrgentItems = computed((): EbayUrgentItem[] => {
  if (!urgentItems.value) return []
  return [
    ...urgentItems.value.returns,
    ...urgentItems.value.cancellations,
    ...urgentItems.value.payment_disputes,
    ...urgentItems.value.inquiries
  ].sort((a, b) => {
    // Critical first, then by deadline
    if (a.urgency === 'critical' && b.urgency !== 'critical') return -1
    if (b.urgency === 'critical' && a.urgency !== 'critical') return 1
    return 0
  })
})

// =========================================================================
// LIFECYCLE
// =========================================================================

onMounted(() => {
  loadDashboard()
})
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Tableau de bord Post-Vente
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Vue d'ensemble de la gestion post-vente eBay
        </p>
      </div>
      <Button
        label="Actualiser"
        icon="pi pi-refresh"
        :loading="loading"
        @click="loadDashboard"
      />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner />
    </div>

    <template v-else>
      <!-- Summary Cards Row -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <!-- Total Open -->
        <Card class="bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-yellow-600 dark:text-yellow-400 font-medium">
                  Cas ouverts
                </p>
                <p class="text-3xl font-bold text-yellow-700 dark:text-yellow-300 mt-1">
                  {{ statistics?.totals.open ?? 0 }}
                </p>
              </div>
              <div class="p-3 bg-yellow-100 dark:bg-yellow-900/40 rounded-full">
                <i class="pi pi-folder-open text-yellow-600 dark:text-yellow-400 text-2xl" />
              </div>
            </div>
          </template>
        </Card>

        <!-- Needs Action -->
        <Card class="bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-orange-600 dark:text-orange-400 font-medium">
                  Action requise
                </p>
                <p class="text-3xl font-bold text-orange-700 dark:text-orange-300 mt-1">
                  {{ statistics?.totals.needs_action ?? 0 }}
                </p>
              </div>
              <div class="p-3 bg-orange-100 dark:bg-orange-900/40 rounded-full">
                <i class="pi pi-clock text-orange-600 dark:text-orange-400 text-2xl" />
              </div>
            </div>
          </template>
        </Card>

        <!-- Past Deadline -->
        <Card class="bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
          <template #content>
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-red-600 dark:text-red-400 font-medium">
                  En retard
                </p>
                <p class="text-3xl font-bold text-red-700 dark:text-red-300 mt-1">
                  {{ statistics?.totals.past_deadline ?? 0 }}
                </p>
              </div>
              <div class="p-3 bg-red-100 dark:bg-red-900/40 rounded-full">
                <i class="pi pi-exclamation-triangle text-red-600 dark:text-red-400 text-2xl" />
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Domain Statistics -->
      <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <!-- Returns -->
        <Card
          class="cursor-pointer hover:shadow-md transition-shadow"
          @click="navigateToList('returns')"
        >
          <template #content>
            <div class="text-center">
              <i class="pi pi-replay text-2xl text-blue-500 mb-2" />
              <p class="text-sm text-gray-600 dark:text-gray-400">Retours</p>
              <p class="text-xl font-bold text-gray-900 dark:text-white">
                {{ statistics?.returns.open ?? 0 }}
              </p>
              <p
                v-if="statistics?.returns.needs_action"
                class="text-xs text-orange-600 mt-1"
              >
                {{ statistics.returns.needs_action }} en attente
              </p>
            </div>
          </template>
        </Card>

        <!-- Cancellations -->
        <Card
          class="cursor-pointer hover:shadow-md transition-shadow"
          @click="navigateToList('cancellations')"
        >
          <template #content>
            <div class="text-center">
              <i class="pi pi-times-circle text-2xl text-purple-500 mb-2" />
              <p class="text-sm text-gray-600 dark:text-gray-400">Annulations</p>
              <p class="text-xl font-bold text-gray-900 dark:text-white">
                {{ statistics?.cancellations.pending ?? 0 }}
              </p>
              <p
                v-if="statistics?.cancellations.needs_action"
                class="text-xs text-orange-600 mt-1"
              >
                {{ statistics.cancellations.needs_action }} en attente
              </p>
            </div>
          </template>
        </Card>

        <!-- Refunds -->
        <Card
          class="cursor-pointer hover:shadow-md transition-shadow"
          @click="navigateToList('refunds')"
        >
          <template #content>
            <div class="text-center">
              <i class="pi pi-euro text-2xl text-green-500 mb-2" />
              <p class="text-sm text-gray-600 dark:text-gray-400">Remboursements</p>
              <p class="text-xl font-bold text-gray-900 dark:text-white">
                {{ statistics?.refunds.pending ?? 0 }}
              </p>
              <p class="text-xs text-green-600 mt-1">
                {{ new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(statistics?.refunds.total_refunded ?? 0) }}
              </p>
            </div>
          </template>
        </Card>

        <!-- Payment Disputes -->
        <Card
          class="cursor-pointer hover:shadow-md transition-shadow"
          @click="navigateToList('payment_disputes')"
        >
          <template #content>
            <div class="text-center">
              <i class="pi pi-exclamation-triangle text-2xl text-red-500 mb-2" />
              <p class="text-sm text-gray-600 dark:text-gray-400">Litiges</p>
              <p class="text-xl font-bold text-gray-900 dark:text-white">
                {{ (statistics?.payment_disputes.open ?? 0) + (statistics?.payment_disputes.action_needed ?? 0) }}
              </p>
              <p
                v-if="statistics?.payment_disputes.action_needed"
                class="text-xs text-orange-600 mt-1"
              >
                {{ statistics.payment_disputes.action_needed }} action requise
              </p>
            </div>
          </template>
        </Card>

        <!-- INR Inquiries -->
        <Card
          class="cursor-pointer hover:shadow-md transition-shadow"
          @click="navigateToList('inquiries')"
        >
          <template #content>
            <div class="text-center">
              <i class="pi pi-inbox text-2xl text-yellow-500 mb-2" />
              <p class="text-sm text-gray-600 dark:text-gray-400">INR</p>
              <p class="text-xl font-bold text-gray-900 dark:text-white">
                {{ statistics?.inquiries.open ?? 0 }}
              </p>
              <p
                v-if="statistics?.inquiries.needs_action"
                class="text-xs text-orange-600 mt-1"
              >
                {{ statistics.inquiries.needs_action }} en attente
              </p>
            </div>
          </template>
        </Card>
      </div>

      <!-- Two Column Layout: Urgent + Activity -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Urgent Items -->
        <Card>
          <template #title>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <i class="pi pi-bell text-orange-500" />
                <span>Actions urgentes</span>
              </div>
              <Tag
                v-if="urgentItems?.total_count"
                :value="urgentItems.total_count.toString()"
                severity="warn"
              />
            </div>
          </template>
          <template #content>
            <div v-if="allUrgentItems.length === 0" class="text-center py-6 text-gray-500">
              <i class="pi pi-check-circle text-3xl text-green-500 mb-2" />
              <p>Aucune action urgente</p>
            </div>
            <div v-else class="space-y-3">
              <div
                v-for="item in allUrgentItems.slice(0, 8)"
                :key="`${item.type}-${item.id}`"
                class="flex items-center justify-between p-3 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                :class="{
                  'bg-red-50 dark:bg-red-900/20': item.urgency === 'critical',
                  'bg-orange-50 dark:bg-orange-900/20': item.urgency === 'high'
                }"
                @click="navigateTo(item)"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="p-2 rounded-full"
                    :class="{
                      'bg-red-100 dark:bg-red-900/40': item.urgency === 'critical',
                      'bg-orange-100 dark:bg-orange-900/40': item.urgency === 'high'
                    }"
                  >
                    <i :class="[getTypeIcon(item.type), item.urgency === 'critical' ? 'text-red-600' : 'text-orange-600']" />
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="font-medium text-gray-900 dark:text-white">
                        {{ getTypeLabel(item.type) }}
                      </span>
                      <Tag
                        :value="getUrgencyLabel(item.urgency)"
                        :severity="getUrgencySeverity(item.urgency)"
                        class="text-xs"
                      />
                    </div>
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                      {{ item.buyer_username || 'Acheteur inconnu' }}
                      <span v-if="formatAmount(item) !== '-'">
                        &middot; {{ formatAmount(item) }}
                      </span>
                    </p>
                  </div>
                </div>
                <div class="text-right">
                  <p class="text-sm font-mono text-gray-500">
                    {{ getExternalId(item).slice(0, 10) }}...
                  </p>
                  <p
                    v-if="item.deadline_date"
                    class="text-xs"
                    :class="item.is_past_due ? 'text-red-600 font-bold' : 'text-gray-500'"
                  >
                    {{ item.is_past_due ? 'En retard' : 'Deadline: ' + formatDate(item.deadline_date).split(' ')[0] }}
                  </p>
                </div>
              </div>
            </div>
          </template>
        </Card>

        <!-- Recent Activity -->
        <Card>
          <template #title>
            <div class="flex items-center gap-2">
              <i class="pi pi-history text-blue-500" />
              <span>Activité récente</span>
            </div>
          </template>
          <template #content>
            <div
              v-if="!recentActivity?.items.length"
              class="text-center py-6 text-gray-500"
            >
              <i class="pi pi-inbox text-3xl text-gray-400 mb-2" />
              <p>Aucune activité récente</p>
            </div>
            <div v-else class="space-y-3">
              <div
                v-for="item in recentActivity.items.slice(0, 10)"
                :key="`${item.type}-${item.id}`"
                class="flex items-center justify-between p-3 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                @click="navigateTo(item)"
              >
                <div class="flex items-center gap-3">
                  <div class="p-2 bg-gray-100 dark:bg-gray-700 rounded-full">
                    <i :class="[getTypeIcon(item.type), 'text-gray-600 dark:text-gray-400']" />
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="font-medium text-gray-900 dark:text-white">
                        {{ getTypeLabel(item.type) }}
                      </span>
                      <span class="text-xs text-gray-500">
                        {{ getStatusDisplay(item) }}
                      </span>
                    </div>
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                      {{ item.buyer_username || 'Acheteur' }}
                      <span v-if="formatAmount(item) !== '-'">
                        &middot; {{ formatAmount(item) }}
                      </span>
                    </p>
                  </div>
                </div>
                <div class="text-right">
                  <p class="text-sm text-gray-500">
                    {{ getRelativeTime(item.updated_at || item.date) }}
                  </p>
                </div>
              </div>
            </div>
          </template>
        </Card>
      </div>
    </template>
  </div>
</template>

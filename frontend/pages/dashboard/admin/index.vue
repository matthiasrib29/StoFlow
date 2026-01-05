<template>
  <div class="page-container">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-secondary-900">Tableau de bord Admin</h1>
      <p class="text-gray-500 mt-1">Vue d'ensemble de la plateforme</p>
    </div>

    <!-- KPI Cards Row -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <StatCard
        label="Utilisateurs totaux"
        :value="overview?.total_users ?? 0"
        icon="pi pi-users"
        variant="primary"
        :loading="isLoading"
      />
      <StatCard
        label="Utilisateurs actifs"
        :value="overview?.active_users ?? 0"
        icon="pi pi-check-circle"
        variant="success"
        :loading="isLoading"
      />
      <StatCard
        label="Comptes verrouilles"
        :value="overview?.locked_users ?? 0"
        icon="pi pi-lock"
        variant="danger"
        :loading="isLoading"
      />
      <StatCard
        label="MRR estime"
        :value="subscriptions?.total_mrr ?? 0"
        icon="pi pi-euro"
        variant="primary"
        format="currency"
        :loading="isLoading"
      />
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <!-- Registrations Chart -->
      <Card class="shadow-sm">
        <template #title>
          <div class="flex items-center justify-between">
            <span>Inscriptions</span>
            <Select
              v-model="selectedPeriod"
              :options="periodOptions"
              optionLabel="label"
              optionValue="value"
              class="w-32"
              @change="onPeriodChange"
            />
          </div>
        </template>
        <template #content>
          <div class="h-64">
            <Line v-if="chartData" :data="chartData" :options="chartOptions" />
            <div v-else class="flex items-center justify-center h-full text-gray-400">
              <ProgressSpinner v-if="isLoading" style="width: 40px; height: 40px" />
              <span v-else>Aucune donnee</span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Subscription Distribution -->
      <Card class="shadow-sm">
        <template #title>Repartition des abonnements</template>
        <template #content>
          <div class="h-64">
            <Doughnut v-if="subscriptionChartData" :data="subscriptionChartData" :options="doughnutOptions" />
            <div v-else class="flex items-center justify-center h-full text-gray-400">
              <ProgressSpinner v-if="isLoading" style="width: 40px; height: 40px" />
              <span v-else>Aucune donnee</span>
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Bottom Row: Recent Activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Logins -->
      <Card class="shadow-sm">
        <template #title>Connexions recentes (24h)</template>
        <template #content>
          <div v-if="isLoading" class="flex justify-center py-4">
            <ProgressSpinner style="width: 30px; height: 30px" />
          </div>
          <div v-else-if="recentActivity?.recent_logins.length" class="space-y-3">
            <div
              v-for="login in recentActivity.recent_logins"
              :key="login.id"
              class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <div class="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                <i class="pi pi-user text-primary-600" />
              </div>
              <div class="flex-1">
                <p class="font-medium text-secondary-900">{{ login.full_name }}</p>
                <p class="text-sm text-gray-500">{{ login.email }}</p>
              </div>
              <p class="text-xs text-gray-400">
                {{ formatDateTime(login.last_login) }}
              </p>
            </div>
          </div>
          <p v-else class="text-gray-400 text-center py-4">Aucune connexion recente</p>
        </template>
      </Card>

      <!-- New Registrations -->
      <Card class="shadow-sm">
        <template #title>Nouvelles inscriptions (7 jours)</template>
        <template #content>
          <div v-if="isLoading" class="flex justify-center py-4">
            <ProgressSpinner style="width: 30px; height: 30px" />
          </div>
          <div v-else-if="recentActivity?.new_registrations.length" class="space-y-3">
            <div
              v-for="reg in recentActivity.new_registrations"
              :key="reg.id"
              class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <i class="pi pi-user-plus text-green-600" />
              </div>
              <div class="flex-1">
                <p class="font-medium text-secondary-900">{{ reg.full_name }}</p>
                <p class="text-sm text-gray-500">{{ reg.email }}</p>
              </div>
              <Tag :value="tierLabel(reg.subscription_tier)" :severity="tierSeverity(reg.subscription_tier)" />
            </div>
          </div>
          <p v-else class="text-gray-400 text-center py-4">Aucune inscription recente</p>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Line, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js'
import { formatDateTime } from '~/utils/formatters'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import ProgressSpinner from 'primevue/progressspinner'
import StatCard from '~/components/admin/StatCard.vue'
import { useAdminStats } from '~/composables/useAdminStats'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

definePageMeta({
  layout: 'dashboard',
  middleware: ['admin'],
})

// Composable
const {
  overview,
  subscriptions,
  registrations,
  recentActivity,
  isLoading,
  fetchAll,
  fetchRegistrations,
} = useAdminStats()

// Period selection
const selectedPeriod = ref('month')
const periodOptions = [
  { label: '7 jours', value: 'week' },
  { label: '30 jours', value: 'month' },
  { label: '3 mois', value: '3months' },
]

// Fetch data on mount
onMounted(async () => {
  try {
    await fetchAll(selectedPeriod.value as 'week' | 'month' | '3months')
  } catch (e) {
    console.error('Failed to fetch admin stats:', e)
  }
})

// Period change handler
const onPeriodChange = async () => {
  try {
    await fetchRegistrations(selectedPeriod.value as 'week' | 'month' | '3months')
  } catch (e) {
    console.error('Failed to fetch registrations:', e)
  }
}

// Chart data for registrations
const chartData = computed(() => {
  if (!registrations.value?.data) return null

  return {
    labels: registrations.value.data.map(d => formatChartDate(d.date)),
    datasets: [
      {
        label: 'Inscriptions',
        data: registrations.value.data.map(d => d.count),
        borderColor: '#facc15',
        backgroundColor: 'rgba(250, 204, 21, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        stepSize: 1,
      },
    },
  },
}

// Doughnut chart for subscriptions
const subscriptionChartData = computed(() => {
  if (!subscriptions.value?.users_by_tier) return null

  const tiers = subscriptions.value.users_by_tier
  return {
    labels: ['Free', 'Starter', 'Pro', 'Enterprise'],
    datasets: [
      {
        data: [tiers.free, tiers.starter, tiers.pro, tiers.enterprise],
        backgroundColor: ['#94a3b8', '#fbbf24', '#22c55e', '#8b5cf6'],
        borderWidth: 0,
      },
    ],
  }
})

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
    },
  },
}


const formatChartDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
}

const tierLabel = (tier: string): string => {
  const labels: Record<string, string> = {
    free: 'Free',
    starter: 'Starter',
    pro: 'Pro',
    enterprise: 'Enterprise',
  }
  return labels[tier] || tier
}

const tierSeverity = (tier: string): 'secondary' | 'warn' | 'success' | 'info' => {
  const severities: Record<string, 'secondary' | 'warn' | 'success' | 'info'> = {
    free: 'secondary',
    starter: 'warn',
    pro: 'success',
    enterprise: 'info',
  }
  return severities[tier] || 'secondary'
}
</script>

<style scoped>
.page-container {
  @apply p-6 lg:p-8;
}
</style>

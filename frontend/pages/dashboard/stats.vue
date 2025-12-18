<template>
  <div class="p-8">
    <!-- Page Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-secondary-900 mb-1">Statistiques</h1>
          <p class="text-gray-600">Analysez vos performances et vos ventes</p>
        </div>

        <!-- Période sélecteur -->
        <Select
          v-model="selectedPeriod"
          :options="periods"
          option-label="label"
          option-value="value"
          class="w-48"
        />
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
            <i class="pi pi-euro text-primary-600 text-xl"/>
          </div>
          <span class="text-xs font-semibold text-green-600 bg-green-50 px-3 py-1 rounded-full">+15%</span>
        </div>
        <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ formatCurrency(kpis.totalRevenue) }}</h3>
        <p class="text-sm text-gray-600">Chiffre d'affaires</p>
      </div>

      <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <div class="w-12 h-12 rounded-xl bg-secondary-100 flex items-center justify-center">
            <i class="pi pi-shopping-cart text-secondary-700 text-xl"/>
          </div>
          <span class="text-xs font-semibold text-green-600 bg-green-50 px-3 py-1 rounded-full">+8%</span>
        </div>
        <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ kpis.totalSales }}</h3>
        <p class="text-sm text-gray-600">Ventes totales</p>
      </div>

      <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
            <i class="pi pi-eye text-primary-600 text-xl"/>
          </div>
          <span class="text-xs font-semibold text-green-600 bg-green-50 px-3 py-1 rounded-full">+23%</span>
        </div>
        <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ kpis.totalViews.toLocaleString() }}</h3>
        <p class="text-sm text-gray-600">Vues totales</p>
      </div>

      <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <div class="w-12 h-12 rounded-xl bg-secondary-100 flex items-center justify-center">
            <i class="pi pi-percentage text-secondary-700 text-xl"/>
          </div>
        </div>
        <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ kpis.conversionRate }}%</h3>
        <p class="text-sm text-gray-600">Taux de conversion</p>
      </div>
    </div>

    <!-- Graphiques -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <!-- Évolution des ventes -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
          <h3 class="text-lg font-bold text-secondary-900 mb-4">Évolution des ventes</h3>
          <Line :data="salesChartData" :options="salesChartOptions" />
        </template>
      </Card>

      <!-- Performance par plateforme -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
          <h3 class="text-lg font-bold text-secondary-900 mb-4">Performance par plateforme</h3>
          <Bar :data="platformsChartData" :options="platformsChartOptions" />
        </template>
      </Card>
    </div>

    <!-- Évolution du chiffre d'affaires -->
    <Card class="shadow-sm modern-rounded border border-gray-100 mb-8">
      <template #content>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-secondary-900">Évolution du chiffre d'affaires</h3>
          <div class="flex gap-2">
            <Badge value="Revenus" severity="success" />
            <Badge value="Objectif" severity="secondary" />
          </div>
        </div>
        <Line :data="revenueChartData" :options="revenueChartOptions" />
      </template>
    </Card>

    <!-- Top produits -->
    <Card class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <h3 class="text-lg font-bold text-secondary-900 mb-4">Top produits</h3>

        <DataTable :value="topProducts" class="modern-table" striped-rows>
          <Column header="#" style="width: 60px">
            <template #body="{ index }">
              <div class="flex items-center justify-center">
                <Badge
                  :value="(index + 1).toString()"
                  :severity="index === 0 ? 'warning' : index === 1 ? 'secondary' : 'info'"
                />
              </div>
            </template>
          </Column>

          <Column field="name" header="Produit">
            <template #body="{ data }">
              <div class="flex items-center gap-3">
                <img
                  v-if="data.image"
                  :src="data.image"
                  :alt="data.name"
                  class="w-12 h-12 rounded-lg object-cover"
                >
                <div v-else class="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center">
                  <i class="pi pi-image text-gray-400"/>
                </div>
                <div>
                  <p class="font-semibold text-secondary-900">{{ data.name }}</p>
                  <p class="text-xs text-gray-500">{{ data.category }}</p>
                </div>
              </div>
            </template>
          </Column>

          <Column field="views" header="Vues" sortable>
            <template #body="{ data }">
              <div class="flex items-center gap-2">
                <i class="pi pi-eye text-gray-400 text-sm"/>
                <span class="font-semibold">{{ data.views.toLocaleString() }}</span>
              </div>
            </template>
          </Column>

          <Column field="sales" header="Ventes" sortable>
            <template #body="{ data }">
              <span class="font-bold text-secondary-900">{{ data.sales }}</span>
            </template>
          </Column>

          <Column field="revenue" header="CA" sortable>
            <template #body="{ data }">
              <span class="font-bold text-green-600">{{ formatCurrency(data.revenue) }}</span>
            </template>
          </Column>

          <Column field="conversionRate" header="Conversion">
            <template #body="{ data }">
              <div class="flex items-center gap-2">
                <ProgressBar
                  :value="data.conversionRate"
                  :show-value="false"
                  class="w-24 h-2"
                />
                <span class="text-sm font-semibold">{{ data.conversionRate }}%</span>
              </div>
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { Line, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

// Enregistrer les composants Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

definePageMeta({
  layout: 'dashboard'
})

const productsStore = useProductsStore()
const publicationsStore = usePublicationsStore()

// State
const selectedPeriod = ref('30d')

const periods = [
  { label: '7 derniers jours', value: '7d' },
  { label: '30 derniers jours', value: '30d' },
  { label: '90 derniers jours', value: '90d' },
  { label: 'Cette année', value: 'year' }
]

// KPIs (mock data)
const kpis = ref({
  totalRevenue: 12450,
  totalSales: 87,
  totalViews: 3420,
  conversionRate: 2.5
})

// Données pour le graphique d'évolution des ventes
const salesChartData = computed(() => ({
  labels: getLast30Days(),
  datasets: [
    {
      label: 'Ventes',
      data: generateSalesData(),
      borderColor: '#facc15',
      backgroundColor: 'rgba(250, 204, 21, 0.1)',
      tension: 0.4,
      fill: true,
      pointBackgroundColor: '#facc15',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6
    }
  ]
}))

const salesChartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      backgroundColor: '#1a1a1a',
      padding: 12,
      titleColor: '#facc15',
      bodyColor: '#fff',
      borderColor: '#facc15',
      borderWidth: 1
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: '#f3f4f6'
      },
      ticks: {
        color: '#6b7280'
      }
    },
    x: {
      grid: {
        display: false
      },
      ticks: {
        color: '#6b7280'
      }
    }
  }
}

// Données pour le graphique performance par plateforme
const platformsChartData = computed(() => ({
  labels: ['Vinted', 'eBay', 'Etsy', 'Facebook'],
  datasets: [
    {
      label: 'Ventes',
      data: [45, 23, 12, 7],
      backgroundColor: [
        'rgba(6, 182, 212, 0.8)',
        'rgba(59, 130, 246, 0.8)',
        'rgba(249, 115, 22, 0.8)',
        'rgba(24, 119, 242, 0.8)'
      ],
      borderColor: [
        '#06b6d4',
        '#3b82f6',
        '#f97316',
        '#1877f2'
      ],
      borderWidth: 2,
      borderRadius: 8
    }
  ]
}))

const platformsChartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      backgroundColor: '#1a1a1a',
      padding: 12,
      titleColor: '#facc15',
      bodyColor: '#fff',
      borderColor: '#facc15',
      borderWidth: 1
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: '#f3f4f6'
      },
      ticks: {
        color: '#6b7280'
      }
    },
    x: {
      grid: {
        display: false
      },
      ticks: {
        color: '#6b7280'
      }
    }
  }
}

// Données pour le graphique d'évolution du CA
const revenueChartData = computed(() => ({
  labels: getLast30Days(),
  datasets: [
    {
      label: 'Revenus',
      data: generateRevenueData(),
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      tension: 0.4,
      fill: true,
      pointBackgroundColor: '#10b981',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 3
    },
    {
      label: 'Objectif',
      data: Array(30).fill(500),
      borderColor: '#6b7280',
      borderDash: [5, 5],
      tension: 0,
      fill: false,
      pointRadius: 0
    }
  ]
}))

const revenueChartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        color: '#6b7280',
        usePointStyle: true,
        padding: 15
      }
    },
    tooltip: {
      backgroundColor: '#1a1a1a',
      padding: 12,
      titleColor: '#facc15',
      bodyColor: '#fff',
      borderColor: '#facc15',
      borderWidth: 1,
      callbacks: {
        label: function(context: any) {
          return context.dataset.label + ': ' + formatCurrency(context.parsed.y)
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: '#f3f4f6'
      },
      ticks: {
        color: '#6b7280',
        callback: function(value: any) {
          return formatCurrency(value)
        }
      }
    },
    x: {
      grid: {
        display: false
      },
      ticks: {
        color: '#6b7280'
      }
    }
  }
}

// Top produits (mock data)
const topProducts = ref([
  {
    name: 'Nike Air Max 2023',
    category: 'Chaussures',
    image: 'https://picsum.photos/seed/1/200',
    views: 1245,
    sales: 23,
    revenue: 2185,
    conversionRate: 1.8
  },
  {
    name: 'iPhone 13 Pro',
    category: 'Électronique',
    image: 'https://picsum.photos/seed/2/200',
    views: 980,
    sales: 18,
    revenue: 1620,
    conversionRate: 1.8
  },
  {
    name: 'Sac à main Gucci',
    category: 'Mode',
    image: 'https://picsum.photos/seed/3/200',
    views: 856,
    sales: 12,
    revenue: 1080,
    conversionRate: 1.4
  },
  {
    name: 'PlayStation 5',
    category: 'Gaming',
    image: 'https://picsum.photos/seed/4/200',
    views: 745,
    sales: 10,
    revenue: 850,
    conversionRate: 1.3
  },
  {
    name: 'Apple Watch Series 8',
    category: 'Électronique',
    image: 'https://picsum.photos/seed/5/200',
    views: 623,
    sales: 9,
    revenue: 765,
    conversionRate: 1.4
  }
])

// Helpers
function getLast30Days(): string[] {
  const days = []
  for (let i = 29; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    days.push(date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }))
  }
  return days
}

function generateSalesData(): number[] {
  // Générer des données réalistes avec tendance croissante
  const data = []
  let base = 1
  for (let i = 0; i < 30; i++) {
    const variation = Math.random() * 4 - 1
    base = Math.max(0, base + variation)
    data.push(Math.round(base))
  }
  return data
}

function generateRevenueData(): number[] {
  // Générer des données de CA avec tendance croissante
  const data = []
  let base = 300
  for (let i = 0; i < 30; i++) {
    const variation = Math.random() * 200 - 50
    base = Math.max(200, base + variation)
    data.push(Math.round(base))
  }
  return data
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(value)
}
</script>

<style scoped>
.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #facc15, #eab308);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover::before {
  opacity: 1;
}

.modern-table {
  border-radius: 16px;
  overflow: hidden;
}
</style>

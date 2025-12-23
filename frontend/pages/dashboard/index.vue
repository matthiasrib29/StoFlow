<template>
  <div class="min-h-screen">
    <!-- Main Content -->
    <div class="dashboard-content p-4 lg:p-8">
      <!-- Header -->
      <div class="mb-6 lg:mb-8">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
          <h1 class="text-2xl lg:text-3xl font-bold text-secondary-900">Tableau de bord</h1>
          <span class="text-sm text-gray-500">{{ currentDate }}</span>
        </div>
        <p class="text-gray-600 text-sm lg:text-base">Bienvenue{{ authStore.user?.full_name ? `, ${authStore.user.full_name}` : '' }}</p>
      </div>

      <!-- Stats Cards - Simplified for MVP1 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 lg:gap-6 mb-6 lg:mb-8 stagger-grid-fast">
        <!-- Total Produits -->
        <div class="stat-card bg-white rounded-2xl p-4 lg:p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3 lg:mb-4">
            <div class="w-10 h-10 lg:w-12 lg:h-12 rounded-xl bg-primary-100 flex items-center justify-center">
              <i class="pi pi-box text-primary-500 text-lg lg:text-xl"/>
            </div>
          </div>
          <h3 class="text-2xl lg:text-3xl font-bold text-secondary-900 mb-1">{{ animatedTotalProducts }}</h3>
          <p class="text-xs lg:text-sm text-gray-600">Produits StoFlow</p>
        </div>

        <!-- Intégrations actives -->
        <div class="stat-card bg-white rounded-2xl p-4 lg:p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3 lg:mb-4">
            <div class="w-10 h-10 lg:w-12 lg:h-12 rounded-xl bg-secondary-100 flex items-center justify-center">
              <i class="pi pi-link text-secondary-700 text-lg lg:text-xl"/>
            </div>
            <span class="text-xs font-semibold text-secondary-700 bg-secondary-50 px-2 lg:px-3 py-1 rounded-full">{{ publicationsStore.connectedIntegrations.length }}/3</span>
          </div>
          <h3 class="text-2xl lg:text-3xl font-bold text-secondary-900 mb-1">{{ animatedConnectedIntegrations }}</h3>
          <p class="text-xs lg:text-sm text-gray-600">Intégrations actives</p>
        </div>
      </div>

      <!-- Quick Action - Simplified -->
      <div class="mb-6 lg:mb-8">
        <NuxtLink to="/dashboard/products/create">
          <Button
            label="Créer un produit"
            icon="pi pi-plus"
            class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold px-4 lg:px-6 py-2 lg:py-3 w-full sm:w-auto"
          />
        </NuxtLink>
      </div>

      <!-- Integrations Status - Full Width -->
      <DashboardIntegrationsStatus />
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})

const authStore = useAuthStore()
const productsStore = useProductsStore()
const publicationsStore = usePublicationsStore()

// Date actuelle
const currentDate = computed(() => {
  const now = new Date()
  return now.toLocaleDateString('fr-FR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})

// Animated counters pour les stats - MVP1 simplified
const totalProductsRef = computed(() => productsStore.totalProducts)
const connectedIntegrationsRef = computed(() => publicationsStore.connectedIntegrations.length)

const { displayValue: animatedTotalProducts } = useCountUp(totalProductsRef, { duration: 1500, delay: 0 })
const { displayValue: animatedConnectedIntegrations } = useCountUp(connectedIntegrationsRef, { duration: 1500, delay: 100 })

// Charger les données au montage
onMounted(async () => {
  try {
    // Charger les produits
    if (productsStore.products.length === 0) {
      await productsStore.fetchProducts()
    }
  } catch (error) {
    console.error('Erreur chargement dashboard:', error)
  }
})
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
</style>

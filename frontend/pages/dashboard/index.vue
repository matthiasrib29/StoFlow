<template>
  <div class="modern-dashboard min-h-screen">
    <!-- Main Content -->
    <div class="dashboard-content p-4 lg:p-8">
      <!-- Header -->
      <div class="mb-6 lg:mb-8">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
          <h1 class="text-2xl lg:text-3xl font-bold text-secondary-900">Tableau de bord</h1>
          <span class="text-sm text-gray-500">{{ currentDate }}</span>
        </div>
        <p class="text-gray-600 text-sm lg:text-base">Bienvenue, {{ authStore.user?.full_name }}</p>
      </div>

      <!-- Stats Cards with modern style -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-6 mb-6 lg:mb-8 stagger-grid-fast">
        <div class="stat-card bg-white rounded-2xl p-4 lg:p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3 lg:mb-4">
            <div class="w-10 h-10 lg:w-12 lg:h-12 rounded-xl bg-primary-100 flex items-center justify-center">
              <i class="pi pi-box text-primary-500 text-lg lg:text-xl"/>
            </div>
            <span class="text-xs font-semibold text-primary-500 bg-primary-50 px-2 lg:px-3 py-1 rounded-full hidden sm:inline">+12%</span>
          </div>
          <h3 class="text-2xl lg:text-3xl font-bold text-secondary-900 mb-1">{{ animatedTotalProducts }}</h3>
          <p class="text-xs lg:text-sm text-gray-600">Total Produits</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-4 lg:p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3 lg:mb-4">
            <div class="w-10 h-10 lg:w-12 lg:h-12 rounded-xl bg-secondary-100 flex items-center justify-center">
              <i class="pi pi-send text-secondary-700 text-lg lg:text-xl"/>
            </div>
            <span class="text-xs font-semibold text-secondary-700 bg-secondary-50 px-2 lg:px-3 py-1 rounded-full hidden sm:inline">Live</span>
          </div>
          <h3 class="text-2xl lg:text-3xl font-bold text-secondary-900 mb-1">{{ animatedActivePublications }}</h3>
          <p class="text-xs lg:text-sm text-gray-600">Publications</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-4 lg:p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3 lg:mb-4">
            <div class="w-10 h-10 lg:w-12 lg:h-12 rounded-xl bg-primary-100 flex items-center justify-center">
              <i class="pi pi-check-circle text-primary-500 text-lg lg:text-xl"/>
            </div>
            <span class="text-xs font-semibold text-primary-500 bg-primary-50 px-2 lg:px-3 py-1 rounded-full hidden sm:inline">+8%</span>
          </div>
          <h3 class="text-2xl lg:text-3xl font-bold text-secondary-900 mb-1">{{ animatedSoldPublications }}</h3>
          <p class="text-xs lg:text-sm text-gray-600">Vendus</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-4 lg:p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3 lg:mb-4">
            <div class="w-10 h-10 lg:w-12 lg:h-12 rounded-xl bg-secondary-100 flex items-center justify-center">
              <i class="pi pi-link text-secondary-700 text-lg lg:text-xl"/>
            </div>
            <span class="text-xs font-semibold text-secondary-700 bg-secondary-50 px-2 lg:px-3 py-1 rounded-full hidden sm:inline">{{ publicationsStore.connectedIntegrations.length }}/4</span>
          </div>
          <h3 class="text-2xl lg:text-3xl font-bold text-secondary-900 mb-1">{{ animatedConnectedIntegrations }}</h3>
          <p class="text-xs lg:text-sm text-gray-600">Intégrations</p>
        </div>
      </div>

      <!-- Quick Actions -->
      <DashboardQuickActions class="mb-6 lg:mb-8" />

      <!-- Two Column Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6 mb-6 lg:mb-8">
        <!-- Recent Activity -->
        <DashboardRecentActivity />

        <!-- Integrations Status -->
        <DashboardIntegrationsStatus />
      </div>

      <!-- Welcome Card -->
      <div class="bg-gradient-to-r from-primary-400 to-primary-500 rounded-2xl p-8 shadow-lg">
        <div class="flex items-start gap-6">
          <div class="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center flex-shrink-0">
            <i class="pi pi-bolt text-secondary-900 text-3xl"/>
          </div>
          <div class="flex-1 text-secondary-900">
            <h3 class="text-2xl font-bold mb-3">
              Boostez vos ventes avec Stoflow !
            </h3>
            <p class="mb-4 opacity-90">
              Gérez tous vos produits et publications depuis un seul endroit.
              Connectez vos comptes de vente en ligne et automatisez vos publications.
            </p>
            <div class="flex flex-wrap gap-3">
              <NuxtLink to="/dashboard/products/create">
                <Button
                  label="Créer un produit"
                  icon="pi pi-plus"
                  class="bg-secondary-900 hover:bg-secondary-800 text-primary-400 border-0 font-bold shadow-md"
                />
              </NuxtLink>
              <NuxtLink to="/dashboard/settings">
                <Button
                  label="Gérer les intégrations"
                  icon="pi pi-link"
                  class="bg-white/20 backdrop-blur-sm hover:bg-white/30 text-secondary-900 border-0 font-semibold"
                />
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
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

// Animated counters pour les stats
const totalProductsRef = computed(() => productsStore.totalProducts)
const activePublicationsRef = computed(() => publicationsStore.activePublications)
const soldPublicationsRef = computed(() => publicationsStore.soldPublications)
const connectedIntegrationsRef = computed(() => publicationsStore.connectedIntegrations.length)

const { displayValue: animatedTotalProducts } = useCountUp(totalProductsRef, { duration: 1500, delay: 0 })
const { displayValue: animatedActivePublications } = useCountUp(activePublicationsRef, { duration: 1500, delay: 100 })
const { displayValue: animatedSoldPublications } = useCountUp(soldPublicationsRef, { duration: 1500, delay: 200 })
const { displayValue: animatedConnectedIntegrations } = useCountUp(connectedIntegrationsRef, { duration: 1500, delay: 300 })

// Charger les données au montage
onMounted(async () => {
  try {
    // Charger les produits
    if (productsStore.products.length === 0) {
      await productsStore.fetchProducts()
    }

    // Charger les publications et l'activité récente
    await Promise.all([
      publicationsStore.fetchPublications(),
      publicationsStore.fetchRecentActivity()
    ])
  } catch (error) {
    console.error('Erreur chargement dashboard:', error)
  }
})
</script>

<style scoped>
.modern-dashboard {
  background: #f9fafb;
}

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

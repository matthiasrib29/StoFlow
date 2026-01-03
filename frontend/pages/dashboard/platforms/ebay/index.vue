<template>
  <div class="page-container">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-secondary-900">eBay</h1>
        <p class="text-gray-500 mt-1">Vue d'ensemble de votre compte eBay</p>
      </div>
      <div class="flex gap-3">
        <Button
          v-if="ebayStore.isConnected"
          label="Synchroniser"
          icon="pi pi-sync"
          class="btn-secondary"
          :loading="syncing"
          @click="handleSync"
        />
        <Button
          v-if="ebayStore.isConnected"
          label="Paramètres"
          icon="pi pi-cog"
          class="btn-secondary"
          @click="$router.push('/dashboard/platforms/ebay/settings')"
        />
      </div>
    </div>

    <!-- Not connected -->
    <Card v-if="!ebayStore.isConnected" class="shadow-lg modern-rounded border-0">
      <template #content>
        <div class="text-center py-12">
          <div class="w-24 h-24 mx-auto mb-6 rounded-full bg-blue-100 flex items-center justify-center">
            <i class="pi pi-link text-blue-500 text-5xl"/>
          </div>
          <h2 class="text-2xl font-bold text-secondary-900 mb-3">Connectez votre compte eBay</h2>
          <p class="text-gray-600 mb-6 max-w-md mx-auto">
            Liez votre compte eBay pour publier vos produits, gérer votre boutique et synchroniser vos ventes automatiquement.
          </p>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto mb-8">
            <div class="p-4 rounded-xl bg-gray-50">
              <i class="pi pi-send text-blue-500 text-2xl mb-2"/>
              <h4 class="font-semibold text-secondary-900 mb-1">Publication facile</h4>
              <p class="text-sm text-gray-600">Publiez vos produits en un clic</p>
            </div>
            <div class="p-4 rounded-xl bg-gray-50">
              <i class="pi pi-sync text-blue-500 text-2xl mb-2"/>
              <h4 class="font-semibold text-secondary-900 mb-1">Sync automatique</h4>
              <p class="text-sm text-gray-600">Stock et prix toujours à jour</p>
            </div>
            <div class="p-4 rounded-xl bg-gray-50">
              <i class="pi pi-chart-line text-blue-500 text-2xl mb-2"/>
              <h4 class="font-semibold text-secondary-900 mb-1">Statistiques</h4>
              <p class="text-sm text-gray-600">Analysez vos performances</p>
            </div>
          </div>

          <Button
            label="Connecter avec eBay"
            icon="pi pi-external-link"
            class="bg-blue-500 hover:bg-blue-600 text-white border-0 font-semibold px-8 py-3"
            :loading="ebayStore.isConnecting"
            @click="handleConnect"
          />

          <p class="text-xs text-gray-500 mt-4">
            En connectant votre compte, vous acceptez les conditions d'utilisation d'eBay
          </p>
        </div>
      </template>
    </Card>

    <!-- Connected: Stats Overview -->
    <template v-else>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-info-100 flex items-center justify-center">
              <i class="pi pi-send text-info-600 text-lg"/>
            </div>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ ebayStore.stats.activeListings }}</h3>
          <p class="text-xs text-gray-600">Annonces actives</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-secondary-100 flex items-center justify-center">
              <i class="pi pi-eye text-secondary-600 text-lg"/>
            </div>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ formatNumber(ebayStore.stats.totalViews) }}</h3>
          <p class="text-xs text-gray-600">Vues totales</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-success-100 flex items-center justify-center">
              <i class="pi pi-check-circle text-success-600 text-lg"/>
            </div>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ ebayStore.stats.totalSales }}</h3>
          <p class="text-xs text-gray-600">Ventes</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center">
              <i class="pi pi-euro text-primary-600 text-lg"/>
            </div>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ formatCurrency(ebayStore.stats.totalRevenue) }}</h3>
          <p class="text-xs text-gray-600">Chiffre d'affaires</p>
        </div>
      </div>

      <!-- Quick Links -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card
          class="shadow-sm modern-rounded border border-gray-100 cursor-pointer hover:shadow-lg transition-all"
          @click="$router.push('/dashboard/platforms/ebay/products')"
        >
          <template #content>
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center">
                <i class="pi pi-box text-blue-600 text-xl"/>
              </div>
              <div>
                <h3 class="font-bold text-secondary-900">Produits</h3>
                <p class="text-sm text-gray-500">Voir tous vos produits eBay</p>
              </div>
              <i class="pi pi-chevron-right ml-auto text-gray-400"/>
            </div>
          </template>
        </Card>

        <Card
          class="shadow-sm modern-rounded border border-gray-100 cursor-pointer hover:shadow-lg transition-all"
          @click="$router.push('/dashboard/platforms/ebay/settings')"
        >
          <template #content>
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center">
                <i class="pi pi-cog text-gray-600 text-xl"/>
              </div>
              <div>
                <h3 class="font-bold text-secondary-900">Paramètres</h3>
                <p class="text-sm text-gray-500">Configurer votre compte eBay</p>
              </div>
              <i class="pi pi-chevron-right ml-auto text-gray-400"/>
            </div>
          </template>
        </Card>

        <Card
          class="shadow-sm modern-rounded border border-gray-100 cursor-pointer hover:shadow-lg transition-all"
          @click="openEbayStore"
        >
          <template #content>
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl bg-yellow-100 flex items-center justify-center">
                <i class="pi pi-external-link text-yellow-600 text-xl"/>
              </div>
              <div>
                <h3 class="font-bold text-secondary-900">Ma Boutique eBay</h3>
                <p class="text-sm text-gray-500">Ouvrir sur eBay.fr</p>
              </div>
              <i class="pi pi-chevron-right ml-auto text-gray-400"/>
            </div>
          </template>
        </Card>
      </div>

      <!-- Account Info -->
      <Card v-if="ebayStore.account" class="shadow-sm modern-rounded border border-gray-100 mt-6">
        <template #content>
          <h3 class="text-lg font-bold text-secondary-900 mb-4">Informations du compte</h3>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p class="text-sm text-gray-500">Username</p>
              <p class="font-semibold text-secondary-900">{{ ebayStore.account.username || '-' }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Email</p>
              <p class="font-semibold text-secondary-900">{{ ebayStore.account.email || '-' }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Marketplace</p>
              <p class="font-semibold text-secondary-900">{{ ebayStore.account.marketplace || 'EBAY_FR' }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Niveau vendeur</p>
              <Tag :severity="getSellerLevelSeverity()">{{ ebayStore.account.sellerLevel || 'Standard' }}</Tag>
            </div>
          </div>
        </template>
      </Card>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})

const ebayStore = useEbayStore()
const { showSuccess, showError } = useAppToast()

const syncing = ref(false)

const handleConnect = async () => {
  try {
    await ebayStore.initiateOAuth()
    showSuccess('Connexion', 'Redirection vers eBay...', 3000)
  } catch (error: any) {
    showError('Erreur', error.message || 'Impossible de se connecter', 5000)
  }
}

const handleSync = async () => {
  syncing.value = true
  try {
    await ebayStore.fetchStats()
    showSuccess('Synchronisation', 'Données mises à jour', 3000)
  } catch (error: any) {
    showError('Erreur', error.message || 'Erreur de synchronisation', 5000)
  } finally {
    syncing.value = false
  }
}

const openEbayStore = () => {
  window.open('https://www.ebay.fr/sh/ovw', '_blank')
}

const getSellerLevelSeverity = () => {
  const level = ebayStore.account?.sellerLevel
  if (level === 'top_rated') return 'success'
  if (level === 'above_standard') return 'info'
  if (level === 'standard') return 'warning'
  return 'secondary'
}

const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('fr-FR').format(value || 0)
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(value || 0)
}

onMounted(async () => {
  try {
    await ebayStore.checkConnectionStatus()
    if (ebayStore.isConnected) {
      await ebayStore.fetchStats()
    }
  } catch (error) {
    console.error('Error checking eBay status:', error)
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
  background: linear-gradient(90deg, #3b82f6, #2563eb);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover::before {
  opacity: 1;
}
</style>

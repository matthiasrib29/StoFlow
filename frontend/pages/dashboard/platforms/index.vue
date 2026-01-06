<template>
  <div class="page-container">
    <PageHeader
      title="Plateformes"
      subtitle="Vue d'ensemble de vos intégrations et publications"
    />

    <!-- Stats globales des plateformes -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
            <i class="pi pi-link text-primary-500 text-xl"/>
          </div>
        </div>
        <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ connectedPlatforms }}</h3>
        <p class="text-sm text-gray-600">Plateformes connectées</p>
      </div>

      <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <div class="w-12 h-12 rounded-xl bg-secondary-100 flex items-center justify-center">
            <i class="pi pi-send text-secondary-700 text-xl"/>
          </div>
        </div>
        <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ totalPublications }}</h3>
        <p class="text-sm text-gray-600">Publications totales</p>
      </div>

      <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
            <i class="pi pi-eye text-primary-500 text-xl"/>
          </div>
        </div>
        <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ totalViews }}</h3>
        <p class="text-sm text-gray-600">Vues totales</p>
      </div>

      <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <div class="w-12 h-12 rounded-xl bg-secondary-100 flex items-center justify-center">
            <i class="pi pi-check-circle text-secondary-700 text-xl"/>
          </div>
        </div>
        <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ totalSales }}</h3>
        <p class="text-sm text-gray-600">Ventes totales</p>
      </div>
    </div>

    <!-- Cards des plateformes -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card
        v-for="platform in enrichedPlatforms"
        :key="platform.id"
        class="shadow-sm hover:shadow-lg transition-all modern-rounded border border-gray-100"
      >
        <template #content>
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-4">
              <div :class="['w-16 h-16 rounded-2xl flex items-center justify-center', platform.bgColor, platform.logo ? 'border border-gray-100 p-2' : '']">
                <img v-if="platform.logo" :src="platform.logo" :alt="platform.name" class="w-full h-full object-contain" >
                <i v-else :class="[platform.icon, 'text-3xl', platform.iconColor]"/>
              </div>
              <div>
                <h3 class="text-xl font-bold text-secondary-900 mb-1">{{ platform.name }}</h3>
                <Badge
                  :value="platform.is_connected ? 'Connecté' : 'Déconnecté'"
                  :severity="platform.is_connected ? 'success' : 'secondary'"
                  class="text-xs"
                />
              </div>
            </div>
            <NuxtLink :to="`/dashboard/platforms/${platform.id}`">
              <Button
                icon="pi pi-arrow-right"
                class="bg-gray-100 hover:bg-gray-200 text-secondary-900 border-0"
                rounded
                text
              />
            </NuxtLink>
          </div>

          <div class="grid grid-cols-3 gap-4 mb-4">
            <div>
              <p class="text-xs text-gray-500 mb-1">Publications</p>
              <p class="text-lg font-bold text-secondary-900">{{ platform.active_publications }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1">Vues</p>
              <p class="text-lg font-bold text-secondary-900">{{ platform.views || 0 }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1">Ventes</p>
              <p class="text-lg font-bold text-secondary-900">{{ platform.sales || 0 }}</p>
            </div>
          </div>

          <div v-if="platform.last_sync" class="text-xs text-gray-400 mb-3">
            Dernière synchro : {{ formatDateTime(platform.last_sync) }}
          </div>

          <div class="flex gap-2">
            <Button
              v-if="!platform.is_connected"
              label="Connecter"
              icon="pi pi-link"
              class="flex-1 bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
              size="small"
              @click="connectPlatform(platform.id)"
            />
            <Button
              v-else
              label="Gérer"
              icon="pi pi-cog"
              class="flex-1 bg-secondary-900 hover:bg-secondary-800 text-primary-400 border-0 font-semibold"
              size="small"
              @click="$router.push(`/dashboard/platforms/${platform.id}`)"
            />
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from 'primevue/usetoast'
import { formatDateTime } from '~/utils/formatters'
import { platformLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

const publicationsStore = usePublicationsStore()
const { showSuccess, showError } = useAppToast()

// Stats globales
const platforms = computed(() => publicationsStore.integrations)
const connectedPlatforms = computed(() => platforms.value.filter(p => p.is_connected).length)
const totalPublications = computed(() => platforms.value.reduce((sum, p) => sum + (p.active_publications || 0), 0))
const totalViews = computed(() => platforms.value.reduce((sum, p) => sum + (p.views || 0), 0))
const totalSales = computed(() => platforms.value.reduce((sum, p) => sum + (p.sales || 0), 0))

// Enrichir les données des plateformes avec couleurs et icônes
const enrichedPlatforms = computed(() => {
  return platforms.value.map(p => {
    let bgColor = 'bg-gray-100'
    let iconColor = 'text-gray-600'
    let icon = 'pi-link'
    let logo: string | null = null

    switch(p.platform) {
      case 'vinted':
        bgColor = 'bg-white'
        iconColor = 'text-platform-vinted'
        icon = 'pi-shopping-bag'
        logo = '/images/platforms/vinted-logo.png'
        break
      case 'ebay':
        bgColor = 'bg-white'
        iconColor = 'text-platform-ebay'
        icon = 'pi-shop'
        logo = '/images/platforms/ebay-logo.png'
        break
      case 'etsy':
        bgColor = 'bg-white'
        iconColor = 'text-platform-etsy'
        icon = 'pi-heart'
        logo = '/images/platforms/etsy-logo.png'
        break
    }

    return {
      ...p,
      id: p.platform,
      bgColor,
      iconColor,
      icon,
      logo,
      views: Math.floor(Math.random() * 500), // Mock data
      sales: Math.floor(Math.random() * 50)  // Mock data
    }
  })
})


const connectPlatform = async (platformId: string) => {
  try {
    await publicationsStore.connectIntegration(platformId as any)
    showSuccess('Connexion réussie', 'La plateforme a été connectée', 3000)
  } catch (error: any) {
    showError('Erreur', error.message || 'Impossible de connecter la plateforme', 5000)
  }
}

// Fetch publications on mount (non-blocking for instant navigation)
onMounted(async () => {
  try {
    await publicationsStore.fetchPublications()
  } catch (error) {
    platformLogger.error('Failed to load platforms', { error })
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

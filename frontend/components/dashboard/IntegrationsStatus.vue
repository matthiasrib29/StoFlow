<template>
  <Card class="shadow-md">
    <template #title>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <i class="pi pi-link text-primary-500"/>
          <span class="text-secondary-900 font-bold">Intégrations</span>
        </div>
        <NuxtLink
          to="/dashboard/settings"
          class="text-sm font-bold text-primary-600 hover:text-primary-700"
        >
          Gérer
          <i class="pi pi-arrow-right ml-1"/>
        </NuxtLink>
      </div>
    </template>
    <template #content>
      <div class="space-y-3">
        <div
          v-for="integration in integrations"
          :key="integration.platform"
          class="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-primary-400 transition"
        >
          <div class="flex items-center gap-3">
            <div
:class="[
              'w-10 h-10 rounded-lg flex items-center justify-center',
              getPlatformBgColor(integration.platform)
            ]">
              <NuxtImg :src="getPlatformLogo(integration.platform)" :alt="integration.name" class="w-6 h-6 object-contain" />
            </div>

            <div>
              <p class="text-sm font-bold text-secondary-900">{{ integration.name }}</p>
              <p class="text-xs text-gray-500">
                {{ integration.is_connected ? `${integration.active_publications || 0} publications actives` : 'Non connecté' }}
              </p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <Badge
              :value="integration.is_connected ? 'Connecté' : 'Déconnecté'"
              :severity="integration.is_connected ? 'success' : 'secondary'"
              :class="!integration.is_connected ? 'badge-status-disconnected' : ''"
            />
          </div>
        </div>
      </div>

      <UiInfoBox v-if="connectedCount === 0" class="mt-4" type="info" icon="pi pi-info-circle">
        Connectez vos comptes pour publier vos produits automatiquement sur plusieurs plateformes.
      </UiInfoBox>
    </template>
  </Card>
</template>

<script setup lang="ts">
const publicationsStore = usePublicationsStore()
const { showEtsyPlatform } = useFeatureFlags()

// PMV2: Filter out Etsy if not enabled
const integrations = computed(() => {
  const allIntegrations = publicationsStore.integrations
  if (showEtsyPlatform) return allIntegrations
  return allIntegrations.filter(i => i.platform !== 'etsy')
})
const connectedCount = computed(() => publicationsStore.connectedIntegrations.length)

// Platform logos
const getPlatformLogo = (platform: string) => {
  const logos: Record<string, string> = {
    vinted: '/images/platforms/vinted-logo.png',
    ebay: '/images/platforms/ebay-logo.png',
    etsy: '/images/platforms/etsy-logo.png'
  }
  return logos[platform] || '/images/platforms/default-logo.png'
}

// Platform background colors
const getPlatformBgColor = (platform: string) => {
  const colors: Record<string, string> = {
    vinted: 'bg-teal-50',
    ebay: 'bg-blue-50',
    etsy: 'bg-orange-50'
  }
  return colors[platform] || 'bg-gray-50'
}
</script>

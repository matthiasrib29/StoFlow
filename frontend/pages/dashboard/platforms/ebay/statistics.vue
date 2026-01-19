<!--
  ╔═══════════════════════════════════════════════════════════════╗
  ║  🚧 PMV2 - Cette page est cachée pour la phase 1              ║
  ║                                                               ║
  ║  Pour activer: useFeatureFlags.ts → platformStatistics: true  ║
  ╚═══════════════════════════════════════════════════════════════╝
-->
<template>
  <PlatformStatisticsPage
    platform="ebay"
    :is-connected="ebayStore.isConnected ?? false"
    :loading="false"
    :is-empty="true"
    empty-message="Vos statistiques eBay apparaîtront ici"
    back-to="/dashboard/platforms/ebay/products"
  >
    <!-- Statistics charts/content -->
    <template #content>
      <div class="text-center py-8 text-gray-500">
        <i class="pi pi-chart-bar text-4xl text-gray-300 mb-4"/>
        <p>Vos statistiques eBay apparaîtront ici</p>
      </div>
    </template>
  </PlatformStatisticsPage>
</template>

<script setup lang="ts">
import { ebayLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

const ebayStore = useEbayStore()

onMounted(async () => {
  ebayLogger.info('eBay Statistics page mounted', {
    route: '/dashboard/platforms/ebay/statistics'
  })

  try {
    await ebayStore.checkConnectionStatus()
    ebayLogger.debug('Connection status checked', {
      isConnected: ebayStore.isConnected
    })
  } catch (error) {
    ebayLogger.error('Failed to check eBay connection status', { error })
  }
})
</script>

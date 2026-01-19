<!--
  ╔═══════════════════════════════════════════════════════════════╗
  ║  🚧 PMV2 - Cette page est cachée pour la phase 1              ║
  ║                                                               ║
  ║  Pour activer: useFeatureFlags.ts → platformStatistics: true  ║
  ╚═══════════════════════════════════════════════════════════════╝
-->
<template>
  <PlatformStatisticsPage
    platform="vinted"
    :is-connected="isConnected"
    :loading="false"
    :is-empty="true"
    empty-message="Vos statistiques Vinted apparaîtront ici"
    subtitle="Analysez vos performances de vente"
    back-to="/dashboard/platforms/vinted/products"
  >
    <!-- Statistics charts/content -->
    <template #content>
      <div class="text-center py-8 text-gray-500">
        <i class="pi pi-chart-bar text-4xl text-gray-300 mb-4"/>
        <p>Vos statistiques Vinted apparaîtront ici</p>
      </div>
    </template>
  </PlatformStatisticsPage>
</template>

<script setup lang="ts">
import { usePlatformConnection } from '~/composables/usePlatformConnection'

definePageMeta({
  layout: 'dashboard'
})

// Connexion Vinted via composable
const { isConnected, fetchStatus } = usePlatformConnection('vinted')

// Charger l'état de connexion au montage
onMounted(async () => {
  await fetchStatus()
})
</script>

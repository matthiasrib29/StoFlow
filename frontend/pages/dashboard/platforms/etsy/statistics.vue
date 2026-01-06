<template>
  <PlatformStatisticsPage
    platform="etsy"
    :is-connected="isConnected"
    :loading="false"
    :is-empty="true"
  >
    <!-- Statistics charts/content -->
    <template #content>
      <!-- Graphiques et statistiques ici quand disponibles -->
    </template>
  </PlatformStatisticsPage>
</template>

<script setup lang="ts">
import { usePlatformConnection } from '~/composables/usePlatformConnection'

definePageMeta({
  layout: 'dashboard'
})

const { isConnected, fetchStatus } = usePlatformConnection('etsy')

onMounted(async () => {
  await fetchStatus()
})
</script>

<!--
  ╔═══════════════════════════════════════════════════════════════╗
  ║  🚧 PMV2 - Cette page est cachée pour la phase 1              ║
  ║                                                               ║
  ║  Pour activer: useFeatureFlags.ts → etsyPlatform: true        ║
  ╚═══════════════════════════════════════════════════════════════╝
-->
<template>
  <PlatformSettingsPage
    platform="etsy"
    :is-connected="isConnected"
    back-to="/dashboard/platforms/etsy/products"
    :columns="2"
  >
    <!-- Settings sections -->
    <template #content>
      <!-- Account Card -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
          <h3 class="text-lg font-bold text-secondary-900 mb-4">
            <i class="pi pi-user mr-2"/>
            Compte Etsy
          </h3>
          <p class="text-gray-500">Informations du compte apparaîtront ici</p>
        </template>
      </Card>

      <!-- Sync Settings Card -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
          <h3 class="text-lg font-bold text-secondary-900 mb-4">
            <i class="pi pi-sync mr-2"/>
            Synchronisation
          </h3>
          <p class="text-gray-500">Paramètres de synchronisation</p>
        </template>
      </Card>
    </template>
  </PlatformSettingsPage>
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

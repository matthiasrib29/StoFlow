<!--
  MVP1: Cette page est désactivée pour le MVP1
  Elle sera réactivée dans une version ultérieure
-->
<template>
  <div class="page-container">
    <div class="text-center py-20">
      <i class="pi pi-clock text-6xl text-gray-300 mb-4"/>
      <h3 class="text-2xl font-bold text-secondary-900 mb-2">Bientôt disponible</h3>
      <p class="text-gray-500">Cette fonctionnalité sera disponible dans une prochaine version</p>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})
</script>

<!--
  ORIGINAL CODE (MVP1 disabled):

<template>
  <div class="page-container">
    <VintedPageHeader
      title="Messages Vinted"
      subtitle="Gérez vos conversations avec les acheteurs"
    />

    <Card class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <div v-if="!isConnected" class="text-center py-12">
          <i class="pi pi-link text-4xl text-gray-300 mb-4"/>
          <h3 class="text-xl font-bold text-secondary-900 mb-2">Connectez votre compte Vinted</h3>
          <p class="text-gray-500 mb-4">Accédez à vos messages après connexion</p>
          <Button
            label="Connecter maintenant"
            icon="pi pi-link"
            class="bg-cyan-500 hover:bg-cyan-600 text-white border-0 font-semibold"
            @click="$router.push('/dashboard/platforms/vinted')"
          />
        </div>
        <div v-else>
          <VintedMessagesTab />
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import VintedPageHeader from '~/components/platforms/VintedPageHeader.vue'
import VintedMessagesTab from '~/components/vinted/VintedMessagesTab.vue'
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
-->

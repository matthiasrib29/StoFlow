<template>
  <PlatformSettingsPage
    platform="vinted"
    :is-connected="isConnected"
    subtitle="Configurez votre intégration Vinted"
    back-to="/dashboard/platforms/vinted/products"
    :columns="1"
  >
    <!-- Settings sections -->
    <template #content>
      <!-- Synchronisation Card -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
          <h4 class="text-lg font-bold text-secondary-900 mb-4">
            <i class="pi pi-sync mr-2"/>
            Synchronisation
          </h4>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="font-medium text-secondary-900">Synchronisation automatique</p>
                <p class="text-sm text-gray-500">Synchroniser automatiquement les produits</p>
              </div>
              <InputSwitch v-model="autoSync" />
            </div>
            <div class="flex items-center justify-between">
              <div>
                <p class="font-medium text-secondary-900">Notifications</p>
                <p class="text-sm text-gray-500">Recevoir des alertes pour les nouvelles ventes</p>
              </div>
              <InputSwitch v-model="notifications" />
            </div>
          </div>
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

// Connexion Vinted via composable
const { isConnected, fetchStatus } = usePlatformConnection('vinted')

const autoSync = ref(true)
const notifications = ref(true)

// Charger l'état de connexion au montage
onMounted(async () => {
  await fetchStatus()
})
</script>

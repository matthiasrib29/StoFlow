<template>
  <div class="p-8">
    <!-- Page Header -->
    <VintedPageHeader
      title="Paramètres Vinted"
      subtitle="Configurez votre intégration Vinted"
    />

    <!-- Content -->
    <Card class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <div v-if="!isConnected" class="text-center py-12">
          <i class="pi pi-link text-4xl text-gray-300 mb-4"/>
          <h3 class="text-xl font-bold text-secondary-900 mb-2">Connectez votre compte Vinted</h3>
          <p class="text-gray-500 mb-4">Accédez aux paramètres après connexion</p>
          <Button
            label="Connecter maintenant"
            icon="pi pi-link"
            class="bg-cyan-500 hover:bg-cyan-600 text-white border-0 font-semibold"
            @click="$router.push('/dashboard/platforms/vinted')"
          />
        </div>
        <div v-else>
          <!-- Paramètres de synchronisation -->
          <div class="space-y-6">
            <div>
              <h4 class="font-semibold text-secondary-900 mb-4">Synchronisation</h4>
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
            </div>
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import VintedPageHeader from '~/components/platforms/VintedPageHeader.vue'

definePageMeta({
  layout: 'dashboard'
})

const isConnected = ref(false)
const autoSync = ref(true)
const notifications = ref(true)
</script>

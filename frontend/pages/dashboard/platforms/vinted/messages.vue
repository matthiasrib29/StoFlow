<template>
  <div class="p-8">
    <!-- Page Header -->
    <VintedPageHeader
      title="Messages Vinted"
      subtitle="Gérez vos conversations avec les acheteurs"
    />

    <!-- Content -->
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
          <!-- Composant Messages -->
          <VintedMessagesTab />
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import VintedPageHeader from '~/components/platforms/VintedPageHeader.vue'
import VintedMessagesTab from '~/components/vinted/VintedMessagesTab.vue'

definePageMeta({
  layout: 'dashboard'
})

const isConnected = ref(false)
</script>

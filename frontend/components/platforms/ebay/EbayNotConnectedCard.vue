<template>
  <Card class="shadow-lg modern-rounded border-0">
    <template #content>
      <div class="text-center py-12">
        <div class="w-24 h-24 mx-auto mb-6 rounded-full bg-blue-100 flex items-center justify-center">
          <i class="pi pi-link text-blue-500 text-5xl"/>
        </div>
        <h2 class="text-2xl font-bold text-secondary-900 mb-3">Connectez votre compte eBay</h2>
        <p class="text-gray-600 mb-6 max-w-md mx-auto">
          Liez votre compte eBay pour publier vos produits, gérer votre boutique et synchroniser vos ventes automatiquement.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto mb-8">
          <div class="p-4 rounded-xl bg-gray-50">
            <i class="pi pi-send text-blue-500 text-2xl mb-2"/>
            <h4 class="font-semibold text-secondary-900 mb-1">Publication facile</h4>
            <p class="text-sm text-gray-600">Publiez vos produits en un clic</p>
          </div>
          <div class="p-4 rounded-xl bg-gray-50">
            <i class="pi pi-sync text-blue-500 text-2xl mb-2"/>
            <h4 class="font-semibold text-secondary-900 mb-1">Sync automatique</h4>
            <p class="text-sm text-gray-600">Stock et prix toujours à jour</p>
          </div>
          <div class="p-4 rounded-xl bg-gray-50">
            <i class="pi pi-chart-line text-blue-500 text-2xl mb-2"/>
            <h4 class="font-semibold text-secondary-900 mb-1">Statistiques</h4>
            <p class="text-sm text-gray-600">Analysez vos performances</p>
          </div>
        </div>

        <Button
          label="Connecter avec eBay"
          icon="pi pi-external-link"
          class="bg-blue-500 hover:bg-blue-600 text-white border-0 font-semibold px-8 py-3"
          :loading="loading"
          @click="$emit('connect')"
        />

        <p class="text-xs text-gray-500 mt-4">
          En connectant votre compte, vous acceptez les conditions d'utilisation d'eBay
        </p>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
defineProps<{
  loading: boolean
}>()

defineEmits<{
  connect: []
}>()
</script>

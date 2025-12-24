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
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-secondary-900 mb-1">Publications</h1>
      <p class="text-gray-600">Gérez vos publications sur toutes les plateformes</p>
    </div>

    <Card class="mb-6">
      <template #content>
        <div class="flex items-center gap-4 p-4 bg-primary-50 border border-primary-200 rounded-lg">
          <i class="pi pi-info-circle text-primary-600 text-3xl"/>
          <div>
            <p class="text-primary-900 font-medium">Fonctionnalité en développement</p>
            <p class="text-primary-700 text-sm mt-1">
              La gestion des publications sur les plateformes (Vinted, eBay, etc.) sera disponible prochainement.
            </p>
          </div>
        </div>
      </template>
    </Card>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <template #title>
          <div class="flex items-center gap-2">
            <i class="pi pi-send text-primary-600"/>
            <span>Publication automatique</span>
          </div>
        </template>
        <template #content>
          <p class="text-gray-600">
            Publiez vos produits sur plusieurs plateformes en un clic avec génération automatique de descriptions par IA.
          </p>
        </template>
      </Card>

      <Card>
        <template #title>
          <div class="flex items-center gap-2">
            <i class="pi pi-sync text-primary-600"/>
            <span>Synchronisation en temps réel</span>
          </div>
        </template>
        <template #content>
          <p class="text-gray-600">
            Synchronisez automatiquement les stocks entre toutes vos plateformes de vente.
          </p>
        </template>
      </Card>

      <Card>
        <template #title>
          <div class="flex items-center gap-2">
            <i class="pi pi-chart-line text-primary-600"/>
            <span>Suivi des performances</span>
          </div>
        </template>
        <template #content>
          <p class="text-gray-600">
            Suivez les performances de vos publications : vues, favoris, messages, conversions.
          </p>
        </template>
      </Card>

      <Card>
        <template #title>
          <div class="flex items-center gap-2">
            <i class="pi pi-cog text-primary-600"/>
            <span>Gestion des templates</span>
          </div>
        </template>
        <template #content>
          <p class="text-gray-600">
            Créez et gérez des templates de descriptions pour gagner du temps lors de vos publications.
          </p>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})
</script>
-->

<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">Statistiques</h1>

    <!-- Info Card -->
    <Card class="mb-6">
      <template #content>
        <div class="flex items-center gap-4 p-4 bg-primary-50 border border-primary-200 rounded-lg">
          <i class="pi pi-info-circle text-primary-600 text-3xl"></i>
          <div>
            <p class="text-primary-900 font-medium">Fonctionnalité en développement</p>
            <p class="text-primary-700 text-sm mt-1">
              Les statistiques détaillées seront disponibles prochainement avec graphiques et rapports.
            </p>
          </div>
        </div>
      </template>
    </Card>

    <!-- Mock Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <Card>
        <template #content>
          <div class="text-center">
            <i class="pi pi-eye text-4xl text-primary-600 mb-3"></i>
            <h3 class="text-2xl font-bold mb-1">1,234</h3>
            <p class="text-gray-600 text-sm">Vues totales</p>
            <p class="text-xs text-primary-600 mt-2">+12% ce mois</p>
          </div>
        </template>
      </Card>

      <Card>
        <template #content>
          <div class="text-center">
            <i class="pi pi-heart text-4xl text-secondary-600 mb-3"></i>
            <h3 class="text-2xl font-bold mb-1">89</h3>
            <p class="text-gray-600 text-sm">Favoris</p>
            <p class="text-xs text-primary-600 mt-2">+8% ce mois</p>
          </div>
        </template>
      </Card>

      <Card>
        <template #content>
          <div class="text-center">
            <i class="pi pi-shopping-cart text-4xl text-primary-600 mb-3"></i>
            <h3 class="text-2xl font-bold mb-1">23</h3>
            <p class="text-gray-600 text-sm">Ventes</p>
            <p class="text-xs text-primary-600 mt-2">+15% ce mois</p>
          </div>
        </template>
      </Card>

      <Card>
        <template #content>
          <div class="text-center">
            <i class="pi pi-euro text-4xl text-primary-600 mb-3"></i>
            <h3 class="text-2xl font-bold mb-1">1,456€</h3>
            <p class="text-gray-600 text-sm">Chiffre d'affaires</p>
            <p class="text-xs text-primary-600 mt-2">+20% ce mois</p>
          </div>
        </template>
      </Card>
    </div>

    <!-- Coming Soon Features -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <template #title>
          <div class="flex items-center gap-2">
            <i class="pi pi-chart-bar text-primary-600"></i>
            <span>Graphiques de performance</span>
          </div>
        </template>
        <template #content>
          <div class="h-48 bg-gray-100 rounded-lg flex items-center justify-center">
            <div class="text-center text-gray-500">
              <i class="pi pi-chart-line text-5xl mb-3"></i>
              <p class="text-sm">Graphiques interactifs bientôt disponibles</p>
            </div>
          </div>
        </template>
      </Card>

      <Card>
        <template #title>
          <div class="flex items-center gap-2">
            <i class="pi pi-list text-primary-600"></i>
            <span>Rapports détaillés</span>
          </div>
        </template>
        <template #content>
          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span class="text-sm text-gray-700">Taux de conversion</span>
              <Badge value="1.9%" severity="info" />
            </div>
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span class="text-sm text-gray-700">Temps moyen de vente</span>
              <Badge value="12j" severity="success" />
            </div>
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span class="text-sm text-gray-700">Panier moyen</span>
              <Badge value="63€" severity="warning" />
            </div>
          </div>
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

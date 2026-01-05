<template>
  <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
    <!-- Publications actives -->
    <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
      <div class="flex items-center justify-between mb-4">
        <div class="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center">
          <i class="pi pi-send text-platform-vinted text-xl"/>
        </div>
      </div>
      <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ stats.activePublications }}</h3>
      <p class="text-sm text-gray-600">Publications actives</p>
    </div>

    <!-- Vues totales -->
    <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
      <div class="flex items-center justify-between mb-4">
        <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
          <i class="pi pi-eye text-primary-600 text-xl"/>
        </div>
      </div>
      <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ stats.totalViews }}</h3>
      <p class="text-sm text-gray-600">Vues totales</p>
    </div>

    <!-- Favoris -->
    <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
      <div class="flex items-center justify-between mb-4">
        <div class="w-12 h-12 rounded-xl bg-error-100 flex items-center justify-center">
          <i class="pi pi-heart-fill text-error-500 text-xl"/>
        </div>
      </div>
      <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ stats.totalFavourites }}</h3>
      <p class="text-sm text-gray-600">Favoris</p>
    </div>

    <!-- CA Potentiel -->
    <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
      <div class="flex items-center justify-between mb-4">
        <div class="w-12 h-12 rounded-xl bg-success-100 flex items-center justify-center">
          <i class="pi pi-euro text-success-600 text-xl"/>
        </div>
      </div>
      <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ formatCurrency(stats.potentialRevenue) }}</h3>
      <p class="text-sm text-gray-600">CA potentiel</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency } from '~/utils/formatters'

interface VintedStats {
  activePublications: number
  totalViews: number
  totalFavourites: number
  potentialRevenue: number
  totalProducts: number
}

defineProps<{
  stats: VintedStats
}>()
</script>

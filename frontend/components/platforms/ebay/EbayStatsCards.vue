<template>
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
    <!-- Annonces actives -->
    <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
      <div class="flex items-center justify-between mb-3">
        <div class="w-10 h-10 rounded-xl bg-info-100 flex items-center justify-center">
          <i class="pi pi-send text-info-600 text-lg"/>
        </div>
        <span v-if="monthlyChange" class="text-xs text-success-600 font-medium">+{{ monthlyChange }} ce mois</span>
      </div>
      <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ stats.activeListings }}</h3>
      <p class="text-xs text-gray-600">Annonces actives</p>
    </div>

    <!-- Vues totales -->
    <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
      <div class="flex items-center justify-between mb-3">
        <div class="w-10 h-10 rounded-xl bg-secondary-100 flex items-center justify-center">
          <i class="pi pi-eye text-secondary-600 text-lg"/>
        </div>
      </div>
      <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ formatNumber(stats.totalViews) }}</h3>
      <p class="text-xs text-gray-600">Vues totales</p>
    </div>

    <!-- Ventes -->
    <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
      <div class="flex items-center justify-between mb-3">
        <div class="w-10 h-10 rounded-xl bg-success-100 flex items-center justify-center">
          <i class="pi pi-check-circle text-success-600 text-lg"/>
        </div>
      </div>
      <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ stats.totalSales }}</h3>
      <p class="text-xs text-gray-600">Ventes</p>
    </div>

    <!-- Chiffre d'affaires -->
    <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
      <div class="flex items-center justify-between mb-3">
        <div class="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center">
          <i class="pi pi-euro text-primary-600 text-lg"/>
        </div>
      </div>
      <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ formatCurrency(stats.totalRevenue) }}</h3>
      <p class="text-xs text-gray-600">Chiffre d'affaires</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatCurrency, formatNumber } from '~/utils/formatters'

interface EbayStats {
  activeListings: number
  totalViews: number
  totalSales: number
  totalRevenue: number
}

defineProps<{
  stats: EbayStats
  monthlyChange?: number
}>()
</script>

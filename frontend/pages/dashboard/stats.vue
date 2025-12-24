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

  See git history for the full original code with:
  - KPI Cards (Revenue, Sales, Views, Conversion Rate)
  - Sales evolution chart (Line chart)
  - Platform performance chart (Bar chart)
  - Revenue evolution chart with target line
  - Top products table with DataTable

  Dependencies used:
  - vue-chartjs (Line, Bar)
  - chart.js (CategoryScale, LinearScale, etc.)
  - PrimeVue components (Card, Select, DataTable, Badge, ProgressBar)
-->

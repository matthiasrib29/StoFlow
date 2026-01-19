<!--
  ╔═══════════════════════════════════════════════════════════════╗
  ║  🚧 PMV2 - Cette page est cachée pour la phase 1              ║
  ║                                                               ║
  ║  Pour activer: useFeatureFlags.ts → etsyPlatform: true        ║
  ╚═══════════════════════════════════════════════════════════════╝
-->
<template>
  <PlatformProductsPage
    platform="etsy"
    :is-connected="false"
    :loading="false"
    :error="null"
    :is-empty="true"
  >
    <!-- Optional: Header actions -->
    <template #header-actions>
      <!-- Boutons d'import/sync quand connecté -->
    </template>

    <!-- Optional: Stats cards -->
    <template #stats>
      <!-- Stats cards ici -->
    </template>

    <!-- Optional: Toolbar (search, filters) -->
    <template #toolbar>
      <!-- Toolbar ici -->
    </template>

    <!-- Products table/list -->
    <template #content>
      <!-- DataTable ici -->
    </template>

    <!-- Empty state actions -->
    <template #empty-actions>
      <!-- Boutons à afficher quand vide -->
    </template>
  </PlatformProductsPage>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})
</script>

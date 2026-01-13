<template>
  <div class="page-container">
    <!-- Page Header -->
    <PageHeader
      :title="`Produits ${platformLabel}`"
      :subtitle="`Gérez vos produits importés depuis ${platformLabel}`"
      :logo="logo"
      :back-to="backTo"
    >
      <template #actions>
        <slot name="header-actions" />
      </template>
    </PageHeader>

    <!-- Not connected state -->
    <PlatformNotConnected
      v-if="!isConnected"
      :platform="platform"
      :message="`Accédez à vos produits ${platformLabel} après connexion`"
    />

    <!-- Connected content -->
    <template v-else>
      <!-- Stats Cards (optional slot) -->
      <div v-if="$slots.stats" class="mb-6">
        <slot name="stats" />
      </div>

      <!-- Toolbar slot -->
      <div v-if="$slots.toolbar" class="mb-6">
        <slot name="toolbar" />
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="text-center py-12">
        <ProgressSpinner style="width: 50px; height: 50px" />
        <p class="mt-4 text-gray-500">Chargement des produits...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="text-center py-12">
        <i class="pi pi-exclamation-triangle text-4xl text-red-400 mb-4"/>
        <p class="text-red-600">{{ error }}</p>
        <Button
          label="Réessayer"
          icon="pi pi-refresh"
          class="mt-4"
          @click="$emit('retry')"
        />
      </div>

      <!-- Empty state -->
      <div v-else-if="isEmpty" class="text-center py-12">
        <i class="pi pi-box text-4xl text-gray-300 mb-4"/>
        <p class="text-gray-500">{{ emptyMessage }}</p>
        <slot name="empty-actions" />
      </div>

      <!-- Products table/list -->
      <slot v-else name="content" />
    </template>
  </div>
</template>

<script setup lang="ts">
type Platform = 'vinted' | 'ebay' | 'etsy'

const props = withDefaults(defineProps<{
  platform: Platform
  isConnected: boolean
  loading?: boolean
  error?: string | null
  isEmpty?: boolean
  emptyMessage?: string
  logo?: string
  backTo?: string
}>(), {
  loading: false,
  error: null,
  isEmpty: false,
  emptyMessage: 'Aucun produit importé'
})

defineEmits<{
  retry: []
}>()

const platformLabels: Record<Platform, string> = {
  vinted: 'Vinted',
  ebay: 'eBay',
  etsy: 'Etsy'
}

const platformLabel = computed(() => platformLabels[props.platform])
</script>

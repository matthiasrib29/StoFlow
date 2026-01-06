<template>
  <div class="page-container">
    <!-- Page Header -->
    <PageHeader
      :title="`Statistiques ${platformLabel}`"
      :subtitle="subtitle || `Analysez vos performances de vente ${platformLabel}`"
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
      message="Accédez à vos statistiques après connexion"
    />

    <!-- Connected content -->
    <template v-else>
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
          <!-- Loading state -->
          <div v-if="loading" class="text-center py-12">
            <ProgressSpinner style="width: 50px; height: 50px" />
            <p class="mt-4 text-gray-500">Chargement des statistiques...</p>
          </div>

          <!-- Empty/placeholder state -->
          <div v-else-if="isEmpty" class="text-center py-8 text-gray-500">
            <i class="pi pi-chart-bar text-4xl text-gray-300 mb-4"/>
            <p>{{ emptyMessage }}</p>
          </div>

          <!-- Statistics content -->
          <div v-else>
            <slot name="content" />
          </div>
        </template>
      </Card>
    </template>
  </div>
</template>

<script setup lang="ts">
type Platform = 'vinted' | 'ebay' | 'etsy'

const props = withDefaults(defineProps<{
  platform: Platform
  isConnected: boolean
  loading?: boolean
  isEmpty?: boolean
  emptyMessage?: string
  subtitle?: string
  logo?: string
  backTo?: string
}>(), {
  loading: false,
  isEmpty: true
})

const platformLabels: Record<Platform, string> = {
  vinted: 'Vinted',
  ebay: 'eBay',
  etsy: 'Etsy'
}

const platformLabel = computed(() => platformLabels[props.platform])

// Computed empty message with platform name
const emptyMessage = computed(() => {
  return props.emptyMessage || `Vos statistiques ${platformLabel.value} apparaîtront ici`
})
</script>

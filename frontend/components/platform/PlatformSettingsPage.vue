<template>
  <div class="page-container">
    <!-- Page Header -->
    <PageHeader
      :title="`Paramètres ${platformLabel}`"
      :subtitle="subtitle || `Configurez votre intégration ${platformLabel}`"
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
      message="Accédez aux paramètres après connexion"
    />

    <!-- Connected content -->
    <template v-else>
      <!-- Settings sections grid -->
      <div :class="gridClass">
        <slot name="content" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
type Platform = 'vinted' | 'ebay' | 'etsy'

const props = withDefaults(defineProps<{
  platform: Platform
  isConnected: boolean
  subtitle?: string
  logo?: string
  backTo?: string
  columns?: 1 | 2
}>(), {
  columns: 2
})

const platformLabels: Record<Platform, string> = {
  vinted: 'Vinted',
  ebay: 'eBay',
  etsy: 'Etsy'
}

const platformLabel = computed(() => platformLabels[props.platform])

const gridClass = computed(() => {
  return props.columns === 1
    ? 'space-y-6'
    : 'grid grid-cols-1 lg:grid-cols-2 gap-6'
})
</script>

<template>
  <div class="flex items-center gap-3">
    <!-- Platform Logo + Title -->
    <div class="flex items-center gap-2">
      <div class="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-sm border border-gray-100 p-1">
        <NuxtImg :src="logoSrc" :alt="platformName" class="w-full h-full object-contain" />
      </div>
      <span class="font-semibold text-secondary-900">{{ platformName }}</span>
    </div>

    <!-- Separator -->
    <div class="h-6 w-px bg-gray-300" />

    <!-- Jobs Button -->
    <Button
      :class="[
        'relative',
        activeJobsCount > 0 ? 'animate-pulse-subtle' : ''
      ]"
      :severity="activeJobsCount > 0 ? 'warning' : 'secondary'"
      :outlined="activeJobsCount === 0"
      size="small"
      @click="$emit('show-jobs')"
    >
      <i :class="['pi mr-2', activeJobsCount > 0 ? 'pi-spin pi-spinner' : 'pi-list']" />
      <span>{{ activeJobsCount > 0 ? `${activeJobsCount} tâche${activeJobsCount > 1 ? 's' : ''}` : 'Tâches' }}</span>
    </Button>

    <!-- Separator -->
    <div class="h-6 w-px bg-gray-300" />

    <!-- Connection Button (single button showing status) -->
    <Button
      :severity="isConnected ? 'success' : 'secondary'"
      :outlined="!isConnected"
      size="small"
      @click="isConnected ? $emit('disconnect') : $emit('connect')"
      class="flex items-center gap-2"
    >
      <span
        :class="[
          'w-2 h-2 rounded-full',
          isConnected ? 'bg-green-400' : 'bg-gray-400'
        ]"
      />
      <span>{{ isConnected ? 'Connecté' : 'Déconnecté' }}</span>
      <i :class="['pi text-xs', isConnected ? 'pi-power-off' : 'pi-link']" />
    </Button>
  </div>
</template>

<script setup lang="ts">
/**
 * Reusable platform header actions component
 *
 * Displays platform logo, jobs button, and connection status
 * Used in dashboard layout for all platforms (Vinted, eBay, Etsy, Facebook)
 */

interface Props {
  platformName: string
  platformCode: string
  logoSrc: string
  activeJobsCount: number
  isConnected: boolean
}

defineProps<Props>()

defineEmits<{
  'show-jobs': []
  'connect': []
  'disconnect': []
}>()
</script>

<style scoped>
.animate-pulse-subtle {
  animation: pulse-subtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse-subtle {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}
</style>

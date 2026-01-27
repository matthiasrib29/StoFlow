<template>
  <div class="mb-8">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 rounded-xl bg-white flex items-center justify-center shadow-sm border border-gray-100 p-2">
          <NuxtImg src="/images/platforms/vinted-logo.png" alt="Vinted" class="w-full h-full object-contain" />
        </div>
        <div>
          <h1 class="text-2xl font-bold text-secondary-900 mb-0.5">{{ title }}</h1>
          <p class="text-sm text-gray-500">{{ subtitle }}</p>
        </div>
      </div>
      <div class="flex gap-3">
        <Button
          v-if="showBackButton"
          label="Retour"
          icon="pi pi-arrow-left"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          size="small"
          @click="$router.push('/dashboard/platforms/vinted')"
        />
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  subtitle?: string
  showBackButton?: boolean
}

withDefaults(defineProps<Props>(), {
  subtitle: '',
  showBackButton: false
})
</script>

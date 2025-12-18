<template>
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-3xl font-bold text-secondary-900">{{ title }}</h1>
      <p v-if="subtitle" class="text-secondary-700 mt-1">{{ subtitle }}</p>
    </div>
    <slot name="actions" />
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  subtitle?: string
}

defineProps<Props>()
</script>

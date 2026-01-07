<template>
  <div class="space-y-2">
    <div
      v-if="showLabel"
      class="skeleton h-4 w-24 rounded"
    />
    <div class="skeleton h-10 w-full rounded-md" />
  </div>
</template>

<script setup lang="ts">
interface Props {
  showLabel?: boolean
}

withDefaults(defineProps<Props>(), {
  showLabel: true
})
</script>

<style scoped>
.skeleton {
  @apply bg-gray-200 animate-pulse;
}
</style>

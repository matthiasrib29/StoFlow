<template>
  <div class="flex items-center justify-between mb-4">
    <div>
      <div class="flex items-center gap-3 mb-1">
        <!-- Back button (optional) -->
        <NuxtLink v-if="backTo" :to="backTo" class="text-gray-500 hover:text-gray-700">
          <i class="pi pi-arrow-left"/>
        </NuxtLink>

        <!-- Title with optional icon/logo -->
        <div class="flex items-center gap-2">
          <slot name="icon">
            <NuxtImg v-if="logo" :src="logo" :alt="title" class="w-6 h-6 object-contain" />
          </slot>
          <h1 class="text-2xl font-bold text-secondary-900">{{ title }}</h1>
        </div>
      </div>

      <!-- Subtitle -->
      <p v-if="subtitle" class="text-gray-500">{{ subtitle }}</p>
    </div>

    <!-- Actions slot (buttons, etc.) -->
    <div v-if="$slots.actions" class="flex gap-3">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
  logo?: string
  backTo?: string
}>()
</script>

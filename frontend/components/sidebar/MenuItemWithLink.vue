<template>
  <div>
    <div class="flex items-center gap-1">
      <NuxtLink
        :to="to"
        class="flex-1 flex items-center gap-3 px-4 py-3 rounded-l-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
        active-class="bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100"
      >
        <i :class="['pi', icon, 'text-lg']"/>
        <span>{{ label }}</span>
      </NuxtLink>
      <button
        class="px-3 py-3 rounded-r-xl hover:bg-gray-50 transition-all text-gray-600"
        :class="{ 'bg-primary-50 text-secondary-900': isOpen }"
        @click="$emit('toggle')"
      >
        <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', isOpen ? 'rotate-180' : 'rotate-0']"/>
      </button>
    </div>

    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 max-h-0"
      enter-to-class="opacity-100 max-h-96"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 max-h-96"
      leave-to-class="opacity-0 max-h-0"
    >
      <div
        v-if="isOpen"
        class="mt-1 ml-3 space-y-1 overflow-hidden border-l-2 border-gray-100 pl-3"
      >
        <slot />
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  to: string
  icon: string
  label: string
  isOpen: boolean
}>()

defineEmits<{
  toggle: []
}>()
</script>

<template>
  <div>
    <button
      class="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-gray-50 transition-all text-gray-600 font-medium"
      :class="{ 'bg-primary-50 text-secondary-900 font-semibold shadow-sm border border-primary-100': isActive }"
      @click="$emit('toggle')"
    >
      <div class="flex items-center gap-3">
        <i :class="['pi', icon, 'text-lg']"/>
        <span>{{ label }}</span>
      </div>
      <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', isOpen ? 'rotate-180' : 'rotate-0']"/>
    </button>

    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 max-h-0 -translate-y-2"
      enter-to-class="opacity-100 max-h-96 translate-y-0"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 max-h-96 translate-y-0"
      leave-to-class="opacity-0 max-h-0 -translate-y-2"
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
  icon: string
  label: string
  isActive?: boolean
  isOpen: boolean
}>()

defineEmits<{
  toggle: []
}>()
</script>

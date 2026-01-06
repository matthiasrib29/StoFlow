<template>
  <div class="border border-gray-200 rounded-lg p-4 space-y-4 transition-all duration-200 hover:border-gray-300">
    <div
      class="flex items-center justify-between cursor-pointer select-none"
      @click="toggle"
    >
      <h4 class="text-xs font-semibold text-gray-600 uppercase flex items-center gap-2">
        <i :class="`pi ${icon} text-xs`" />
        {{ title }}
        <span class="text-gray-400 font-normal">(optionnel)</span>
        <span
          v-if="filledCount > 0"
          class="bg-primary-400 text-secondary-900 text-[10px] font-bold px-1.5 py-0.5 rounded-full ml-1"
        >
          {{ filledCount }} rempli{{ filledCount > 1 ? 's' : '' }}
        </span>
      </h4>
      <i
        :class="isOpen ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
        class="text-gray-400 transition-transform duration-200"
      />
    </div>

    <div v-show="isOpen" class="pt-2">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  icon: string
  filledCount?: number
  defaultOpen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  filledCount: 0,
  defaultOpen: false
})

const isOpen = ref(props.defaultOpen)

const toggle = () => {
  isOpen.value = !isOpen.value
}

// Allow external control
defineExpose({ isOpen, toggle })
</script>

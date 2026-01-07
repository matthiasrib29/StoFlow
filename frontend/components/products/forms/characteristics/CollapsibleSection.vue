<template>
  <div
    class="collapsible-section"
    :data-open="isOpen"
  >
    <div
      class="flex items-center justify-between cursor-pointer select-none"
      @click="toggle"
    >
      <div class="flex-1">
        <h4 class="text-xs font-semibold text-gray-700 uppercase flex items-center gap-2">
          <i :class="`pi ${icon} text-xs`" />
          {{ title }}
          <span class="text-gray-400 font-normal">(optionnel)</span>
          <span
            v-if="filledCount > 0"
            class="collapsible-section-badge"
          >
            {{ filledCount }}
          </span>
        </h4>

        <!-- NOUVEAU : Preview slot -->
        <div v-if="!isOpen && filledCount > 0" class="collapsible-preview">
          <slot name="preview" />
        </div>
      </div>

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

<template>
  <div :class="sectionClasses">
    <!-- Section Title -->
    <h4 v-if="title" class="text-xs font-semibold text-gray-600 uppercase mb-4">
      {{ title }}
    </h4>

    <!-- Section Content -->
    <div :class="gridClasses">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  columns?: 1 | 2 | 3 | 4
  variant?: 'default' | 'outlined' | 'flat'
  spacing?: 'tight' | 'normal' | 'relaxed'
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  columns: 3,
  variant: 'default',
  spacing: 'normal'
})

// Section wrapper classes based on variant
const sectionClasses = computed(() => {
  const base = []

  // Spacing
  const spacingMap = {
    tight: 'space-y-2',
    normal: 'space-y-4',
    relaxed: 'space-y-6'
  }
  base.push(spacingMap[props.spacing])

  // Variant styles
  const variantMap = {
    default: 'bg-gray-50 rounded-lg p-4',
    outlined: 'border border-gray-200 rounded-lg p-4',
    flat: ''
  }
  base.push(variantMap[props.variant])

  return base.join(' ')
})

// Grid classes based on columns
const gridClasses = computed(() => {
  const base = ['grid', 'gap-4']

  // Responsive columns
  const columnMap = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-3',
    4: 'grid-cols-2 md:grid-cols-4'
  }
  base.push(columnMap[props.columns])

  return base.join(' ')
})
</script>

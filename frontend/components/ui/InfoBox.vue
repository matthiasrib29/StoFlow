<template>
  <div :class="[
    'p-4 rounded-lg',
    bgColor,
    borderColor ? `border ${borderColor}` : ''
  ]">
    <p :class="['text-sm font-medium', textColor]">
      <i v-if="icon" :class="[icon, 'mr-2']"></i>
      <slot />
    </p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  type?: 'info' | 'success' | 'warning' | 'error'
  icon?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'info'
})

const bgColor = computed(() => {
  const colors = {
    info: 'bg-primary-50 border border-primary-400',
    success: 'bg-primary-50 border border-primary-200',
    warning: 'bg-primary-50 border border-primary-200',
    error: 'bg-secondary-50 border border-primary-200'
  }
  return colors[props.type]
})

const textColor = computed(() => {
  const colors = {
    info: 'text-secondary-900',
    success: 'text-primary-700',
    warning: 'text-primary-700',
    error: 'text-secondary-700'
  }
  return colors[props.type]
})

const borderColor = computed(() => {
  const colors = {
    info: 'border-primary-400',
    success: 'border-primary-200',
    warning: 'border-primary-200',
    error: 'border-primary-200'
  }
  return colors[props.type]
})
</script>

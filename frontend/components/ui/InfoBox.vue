<template>
  <div :class="['flex items-start gap-3 p-3 rounded-lg text-sm', typeClasses]">
    <i v-if="icon" :class="[icon, 'mt-0.5']" />
    <div class="flex-1">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  type?: 'info' | 'success' | 'warning' | 'error'
  icon?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'info',
  icon: ''
})

const typeClasses = computed(() => {
  switch (props.type) {
    case 'success':
      return 'bg-green-50 text-green-700 border border-green-200'
    case 'warning':
      return 'bg-yellow-50 text-yellow-700 border border-yellow-200'
    case 'error':
      return 'bg-red-50 text-red-700 border border-red-200'
    case 'info':
    default:
      return 'bg-blue-50 text-blue-700 border border-blue-200'
  }
})
</script>

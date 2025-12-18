<template>
  <div class="stat-card bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
    <div class="flex items-center justify-between mb-4">
      <div :class="['w-12 h-12 rounded-xl flex items-center justify-center', iconBgClass]">
        <i :class="[icon, 'text-xl', iconColorClass]"></i>
      </div>
      <span
        v-if="badge"
        :class="['text-xs font-semibold px-3 py-1 rounded-full', badgeTextClass, badgeBgClass]"
      >
        {{ badge }}
      </span>
    </div>
    <h3 class="text-3xl font-bold text-secondary-900 mb-1">{{ value }}</h3>
    <p class="text-sm text-gray-600">{{ label }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  icon: string
  value: string | number
  label: string
  badge?: string
  colorScheme?: 'primary' | 'secondary' | 'cyan' | 'orange' | 'blue'
}

const props = withDefaults(defineProps<Props>(), {
  colorScheme: 'primary'
})

const iconBgClass = computed(() => {
  const schemes = {
    primary: 'bg-primary-100',
    secondary: 'bg-secondary-100',
    cyan: 'bg-cyan-100',
    orange: 'bg-orange-100',
    blue: 'bg-blue-100'
  }
  return schemes[props.colorScheme]
})

const iconColorClass = computed(() => {
  const schemes = {
    primary: 'text-primary-500',
    secondary: 'text-secondary-700',
    cyan: 'text-cyan-600',
    orange: 'text-orange-600',
    blue: 'text-blue-600'
  }
  return schemes[props.colorScheme]
})

const badgeTextClass = computed(() => {
  const schemes = {
    primary: 'text-primary-500',
    secondary: 'text-secondary-700',
    cyan: 'text-cyan-600',
    orange: 'text-orange-600',
    blue: 'text-blue-600'
  }
  return schemes[props.colorScheme]
})

const badgeBgClass = computed(() => {
  const schemes = {
    primary: 'bg-primary-50',
    secondary: 'bg-secondary-50',
    cyan: 'bg-cyan-50',
    orange: 'bg-orange-50',
    blue: 'bg-blue-50'
  }
  return schemes[props.colorScheme]
})
</script>

<style scoped>
.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--p-primary-400), var(--p-primary-500));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover::before {
  opacity: 1;
}
</style>

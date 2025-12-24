<template>
  <Card class="stat-card">
    <template #content>
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <p class="text-sm text-gray-500 font-medium mb-1">{{ label }}</p>
          <p class="text-3xl font-bold text-secondary-900">
            <template v-if="loading">
              <ProgressSpinner
                style="width: 24px; height: 24px"
                strokeWidth="4"
              />
            </template>
            <template v-else>
              {{ formattedValue }}
            </template>
          </p>
          <p v-if="subtitle" class="text-xs text-gray-400 mt-1">{{ subtitle }}</p>
        </div>
        <div
          v-if="icon"
          :class="[
            'w-12 h-12 rounded-xl flex items-center justify-center',
            iconBgClass
          ]"
        >
          <i :class="[icon, 'text-xl', iconColorClass]" />
        </div>
      </div>

      <!-- Trend indicator -->
      <div v-if="trend !== undefined" class="mt-3 flex items-center gap-1">
        <i
          :class="[
            'pi text-sm',
            trend >= 0 ? 'pi-arrow-up text-green-500' : 'pi-arrow-down text-red-500'
          ]"
        />
        <span
          :class="[
            'text-sm font-medium',
            trend >= 0 ? 'text-green-500' : 'text-red-500'
          ]"
        >
          {{ Math.abs(trend) }}%
        </span>
        <span class="text-xs text-gray-400 ml-1">vs mois dernier</span>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
import Card from 'primevue/card'
import ProgressSpinner from 'primevue/progressspinner'

interface Props {
  label: string
  value: number | string
  subtitle?: string
  icon?: string
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger'
  loading?: boolean
  trend?: number
  format?: 'number' | 'currency' | 'percent'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  loading: false,
  format: 'number',
})

// Format value based on type
const formattedValue = computed(() => {
  if (typeof props.value === 'string') return props.value

  switch (props.format) {
    case 'currency':
      return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
      }).format(props.value)
    case 'percent':
      return `${props.value}%`
    default:
      return new Intl.NumberFormat('fr-FR').format(props.value)
  }
})

// Icon background class based on variant
const iconBgClass = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-primary-100'
    case 'success':
      return 'bg-green-100'
    case 'warning':
      return 'bg-orange-100'
    case 'danger':
      return 'bg-red-100'
    default:
      return 'bg-gray-100'
  }
})

// Icon color class based on variant
const iconColorClass = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'text-primary-600'
    case 'success':
      return 'text-green-600'
    case 'warning':
      return 'text-orange-600'
    case 'danger':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
})
</script>

<style scoped>
.stat-card {
  @apply shadow-sm border border-gray-100 hover:shadow-md transition-shadow;
}

.stat-card :deep(.p-card-body) {
  @apply p-5;
}

.stat-card :deep(.p-card-content) {
  @apply p-0;
}
</style>

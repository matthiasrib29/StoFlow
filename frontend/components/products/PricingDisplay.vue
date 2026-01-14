<template>
  <div class="pricing-display">
    <!-- Header -->
    <div class="mb-4">
      <h4 class="text-lg font-semibold text-gray-900">Pricing Suggestions</h4>
      <p class="text-sm text-gray-600">
        Based on: {{ pricing.brand }} - {{ pricing.group }}
        <span v-if="pricing.model_name"> - {{ pricing.model_name }}</span>
      </p>
    </div>

    <!-- Three Price Levels -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- Quick Sale Price -->
      <div class="border border-blue-200 rounded-lg p-4 bg-blue-50">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-blue-600 uppercase tracking-wide">Quick Sale</span>
          <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            -25%
          </span>
        </div>
        <div class="text-2xl font-bold text-blue-900">
          {{ formatPrice(pricing.quick_price) }}
        </div>
        <p class="text-xs text-blue-700 mt-1">Sell fast</p>
      </div>

      <!-- Standard Price (Recommended) -->
      <div class="border-2 border-primary-300 rounded-lg p-4 bg-primary-50 relative">
        <div class="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <span class="bg-primary-500 text-secondary-900 text-xs font-semibold px-3 py-1 rounded-full">
            Recommended
          </span>
        </div>
        <div class="flex items-center justify-between mb-2 mt-2">
          <span class="text-xs font-semibold text-primary-600 uppercase tracking-wide">Standard</span>
          <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
            Base
          </span>
        </div>
        <div class="text-2xl font-bold text-secondary-900">
          {{ formatPrice(pricing.standard_price) }}
        </div>
        <p class="text-xs text-gray-600 mt-1">Market value</p>
      </div>

      <!-- Premium Price -->
      <div class="border border-purple-200 rounded-lg p-4 bg-purple-50">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-purple-600 uppercase tracking-wide">Premium</span>
          <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            +30%
          </span>
        </div>
        <div class="text-2xl font-bold text-purple-900">
          {{ formatPrice(pricing.premium_price) }}
        </div>
        <p class="text-xs text-purple-700 mt-1">Maximum value</p>
      </div>
    </div>

    <!-- Base Price Info -->
    <div class="mt-4 p-3 bg-gray-50 rounded-md">
      <div class="flex items-center justify-between text-sm">
        <span class="text-gray-600">Base Price:</span>
        <span class="font-semibold text-gray-900">{{ formatPrice(pricing.base_price) }}</span>
      </div>
      <div v-if="hasModelCoefficient" class="flex items-center justify-between text-sm mt-1">
        <span class="text-gray-600">Model Coefficient:</span>
        <span class="font-semibold text-gray-900">×{{ formatCoefficient(pricing.model_coefficient) }}</span>
      </div>
    </div>

    <!-- Expandable Breakdown -->
    <div class="mt-4 border border-gray-200 rounded-lg">
      <button
        @click="toggleBreakdown"
        class="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50 transition-colors rounded-lg"
      >
        <span class="text-sm font-medium text-gray-900">
          View Calculation Breakdown
        </span>
        <svg
          :class="['w-5 h-5 text-gray-500 transition-transform', showBreakdown && 'rotate-180']"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </button>

      <!-- Breakdown Content (Collapsible) -->
      <div v-if="showBreakdown" class="px-4 pb-4 space-y-2">
        <div class="pt-2 border-t border-gray-200">
          <h5 class="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
            Adjustments Applied
          </h5>

          <!-- Condition Adjustment -->
          <div class="flex items-center justify-between py-1">
            <span class="text-sm text-gray-600">
              <span :class="getAdjustmentColor(pricing.adjustments.condition)" class="font-medium">
                {{ getAdjustmentIcon(pricing.adjustments.condition) }}
              </span>
              Condition
            </span>
            <span :class="['text-sm font-semibold', getAdjustmentColor(pricing.adjustments.condition)]">
              {{ formatAdjustment(pricing.adjustments.condition) }}
            </span>
          </div>

          <!-- Origin Adjustment -->
          <div class="flex items-center justify-between py-1">
            <span class="text-sm text-gray-600">
              <span :class="getAdjustmentColor(pricing.adjustments.origin)" class="font-medium">
                {{ getAdjustmentIcon(pricing.adjustments.origin) }}
              </span>
              Origin
            </span>
            <span :class="['text-sm font-semibold', getAdjustmentColor(pricing.adjustments.origin)]">
              {{ formatAdjustment(pricing.adjustments.origin) }}
            </span>
          </div>

          <!-- Decade Adjustment -->
          <div class="flex items-center justify-between py-1">
            <span class="text-sm text-gray-600">
              <span :class="getAdjustmentColor(pricing.adjustments.decade)" class="font-medium">
                {{ getAdjustmentIcon(pricing.adjustments.decade) }}
              </span>
              Decade/Vintage
            </span>
            <span :class="['text-sm font-semibold', getAdjustmentColor(pricing.adjustments.decade)]">
              {{ formatAdjustment(pricing.adjustments.decade) }}
            </span>
          </div>

          <!-- Trend Adjustment -->
          <div class="flex items-center justify-between py-1">
            <span class="text-sm text-gray-600">
              <span :class="getAdjustmentColor(pricing.adjustments.trend)" class="font-medium">
                {{ getAdjustmentIcon(pricing.adjustments.trend) }}
              </span>
              Trends
            </span>
            <span :class="['text-sm font-semibold', getAdjustmentColor(pricing.adjustments.trend)]">
              {{ formatAdjustment(pricing.adjustments.trend) }}
            </span>
          </div>

          <!-- Feature Adjustment -->
          <div class="flex items-center justify-between py-1">
            <span class="text-sm text-gray-600">
              <span :class="getAdjustmentColor(pricing.adjustments.feature)" class="font-medium">
                {{ getAdjustmentIcon(pricing.adjustments.feature) }}
              </span>
              Features
            </span>
            <span :class="['text-sm font-semibold', getAdjustmentColor(pricing.adjustments.feature)]">
              {{ formatAdjustment(pricing.adjustments.feature) }}
            </span>
          </div>

          <!-- Total Adjustment -->
          <div class="flex items-center justify-between py-2 mt-2 border-t border-gray-200">
            <span class="text-sm font-semibold text-gray-900">Total Adjustments</span>
            <span :class="['text-base font-bold', getAdjustmentColor(pricing.adjustments.total)]">
              {{ formatAdjustment(pricing.adjustments.total) }}
            </span>
          </div>

          <!-- Formula Explanation -->
          <div class="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
            <p class="font-mono">
              Standard = Base ({{ formatPrice(pricing.base_price) }})
              × Model ({{ formatCoefficient(pricing.model_coefficient) }})
              × (1 + {{ formatAdjustment(pricing.adjustments.total) }})
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PriceOutput } from '~/composables/usePricingCalculation'

interface Props {
  pricing: PriceOutput
}

const props = defineProps<Props>()

const showBreakdown = ref(false)

const toggleBreakdown = () => {
  showBreakdown.value = !showBreakdown.value
}

// Format price for display (add currency symbol)
const formatPrice = (price: string | number) => {
  const numPrice = typeof price === 'string' ? parseFloat(price) : price
  return `€${numPrice.toFixed(2)}`
}

// Format coefficient for display
const formatCoefficient = (coef: string | number) => {
  const numCoef = typeof coef === 'string' ? parseFloat(coef) : coef
  return numCoef.toFixed(2)
}

// Percentage formatter for adjustments
const formatAdjustment = (value: string | number) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  const percent = (numValue * 100).toFixed(1)
  return numValue >= 0 ? `+${percent}%` : `${percent}%`
}

// Get color class based on adjustment value
const getAdjustmentColor = (value: string | number) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (numValue > 0) return 'text-green-600'
  if (numValue < 0) return 'text-red-600'
  return 'text-gray-600'
}

// Get icon based on adjustment value
const getAdjustmentIcon = (value: string | number) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (numValue > 0) return '↑'
  if (numValue < 0) return '↓'
  return '='
}

// Check if coefficient is not 1.0
const hasModelCoefficient = computed(() => {
  const coef = typeof props.pricing.model_coefficient === 'string'
    ? parseFloat(props.pricing.model_coefficient)
    : props.pricing.model_coefficient
  return coef !== 1.0
})
</script>

<style scoped>
/* Add any component-specific styles if needed */
</style>

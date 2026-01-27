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
      <div
        class="border rounded-lg p-4 cursor-pointer transition-all"
        :class="isSelected(pricing.quick_price)
          ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-300'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'"
        @click="selectPrice(pricing.quick_price)"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Quick Sale</span>
          <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
            -25%
          </span>
        </div>
        <div class="text-2xl font-bold text-gray-900">
          {{ formatPrice(pricing.quick_price) }}
        </div>
        <p class="text-xs text-gray-500 mt-1">Vente rapide</p>
      </div>

      <!-- Standard Price (Recommended) -->
      <div
        class="border rounded-lg p-4 relative cursor-pointer transition-all"
        :class="isSelected(pricing.standard_price)
          ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-300'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'"
        @click="selectPrice(pricing.standard_price)"
      >
        <div class="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <span class="bg-gray-700 text-white text-xs font-semibold px-3 py-0.5 rounded-full">
            Recommandé
          </span>
        </div>
        <div class="flex items-center justify-between mb-2 mt-2">
          <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Standard</span>
          <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
            Base
          </span>
        </div>
        <div class="text-2xl font-bold text-gray-900">
          {{ formatPrice(pricing.standard_price) }}
        </div>
        <p class="text-xs text-gray-500 mt-1">Valeur marché</p>
      </div>

      <!-- Premium Price -->
      <div
        class="border rounded-lg p-4 cursor-pointer transition-all"
        :class="isSelected(pricing.premium_price)
          ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-300'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'"
        @click="selectPrice(pricing.premium_price)"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Premium</span>
          <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-700">
            +30%
          </span>
        </div>
        <div class="text-2xl font-bold text-gray-900">
          {{ formatPrice(pricing.premium_price) }}
        </div>
        <p class="text-xs text-gray-500 mt-1">Valeur maximum</p>
      </div>
    </div>

    <!-- Admin-only: Base Price Info + Breakdown -->
    <template v-if="isAdmin">
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
      <div v-if="showBreakdown" class="px-4 pb-4 space-y-4">
        <div class="pt-3 border-t border-gray-200 space-y-4">

          <!-- Step 1: Base Price -->
          <div>
            <h5 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Étape 1 — Prix de base
            </h5>
            <div class="p-2.5 bg-gray-50 rounded-md text-sm space-y-1.5">
              <div class="flex justify-between">
                <span class="text-gray-600">Groupe</span>
                <span class="font-medium text-gray-900">{{ pricing.brand }} × {{ pricing.group }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Prix de base du groupe</span>
                <span class="font-semibold text-gray-900">{{ formatPrice(pricing.base_price) }}</span>
              </div>
              <template v-if="hasModelCoefficient">
                <div class="flex justify-between">
                  <span class="text-gray-600">
                    Modèle <span v-if="pricing.model_name" class="font-medium">{{ pricing.model_name }}</span>
                  </span>
                  <span class="font-medium text-gray-900">×{{ formatCoefficient(pricing.model_coefficient) }}</span>
                </div>
                <div class="flex justify-between pt-1.5 border-t border-gray-200">
                  <span class="text-gray-600">Après modèle</span>
                  <span class="font-semibold text-gray-900">
                    {{ formatPrice(pricing.base_price) }} × {{ formatCoefficient(pricing.model_coefficient) }} = {{ formatPrice(priceAfterModel) }}
                  </span>
                </div>
              </template>
            </div>
          </div>

          <!-- Step 2: Condition -->
          <div>
            <h5 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Étape 2 — Condition
            </h5>
            <div class="p-2.5 bg-gray-50 rounded-md text-sm space-y-1.5">
              <div v-if="pricing.adjustments.condition_detail" class="flex justify-between">
                <span class="text-gray-600">Score condition</span>
                <span class="font-medium text-gray-900">{{ pricing.adjustments.condition_detail.score }} / 10</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Multiplicateur</span>
                <span :class="['font-semibold', getAdjustmentColor(pricing.adjustments.condition)]">
                  ×{{ formatCoefficient(pricing.condition_multiplier) }}
                </span>
              </div>
              <div class="flex justify-between pt-1.5 border-t border-gray-200">
                <span class="text-gray-600">Après condition</span>
                <span class="font-semibold text-gray-900">
                  {{ formatPrice(priceAfterModel) }} × {{ formatCoefficient(pricing.condition_multiplier) }} = {{ formatPrice(priceAfterCondition) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Step 3: Adjustments -->
          <div>
            <h5 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Étape 3 — Ajustements
            </h5>
            <div class="p-2.5 bg-gray-50 rounded-md text-sm space-y-2">

              <!-- Origin -->
              <div class="space-y-0.5">
                <div class="flex items-center justify-between">
                  <span class="text-gray-600">
                    <span :class="getAdjustmentColor(pricing.adjustments.origin)" class="font-medium">{{ getAdjustmentIcon(pricing.adjustments.origin) }}</span>
                    Origine
                  </span>
                  <span :class="['font-semibold', getAdjustmentColor(pricing.adjustments.origin)]">
                    {{ formatAdjustment(pricing.adjustments.origin) }}
                  </span>
                </div>
                <div v-if="pricing.adjustments.origin_detail" class="text-xs text-gray-400 font-mono pl-4">
                  {{ pricing.adjustments.origin_detail.actual_value || '—' }}
                  ({{ formatCoef(pricing.adjustments.origin_detail.actual_coef) }})
                  − {{ pricing.adjustments.origin_detail.expected_best || 'aucun attendu' }}
                  ({{ formatCoef(pricing.adjustments.origin_detail.expected_coef) }})
                </div>
              </div>

              <!-- Decade -->
              <div class="space-y-0.5">
                <div class="flex items-center justify-between">
                  <span class="text-gray-600">
                    <span :class="getAdjustmentColor(pricing.adjustments.decade)" class="font-medium">{{ getAdjustmentIcon(pricing.adjustments.decade) }}</span>
                    Décennie
                  </span>
                  <span :class="['font-semibold', getAdjustmentColor(pricing.adjustments.decade)]">
                    {{ formatAdjustment(pricing.adjustments.decade) }}
                  </span>
                </div>
                <div v-if="pricing.adjustments.decade_detail" class="text-xs text-gray-400 font-mono pl-4">
                  {{ pricing.adjustments.decade_detail.actual_value || '—' }}
                  ({{ formatCoef(pricing.adjustments.decade_detail.actual_coef) }})
                  − {{ pricing.adjustments.decade_detail.expected_best || 'aucun attendu' }}
                  ({{ formatCoef(pricing.adjustments.decade_detail.expected_coef) }})
                </div>
              </div>

              <!-- Trend -->
              <div class="space-y-0.5">
                <div class="flex items-center justify-between">
                  <span class="text-gray-600">
                    <span :class="getAdjustmentColor(pricing.adjustments.trend)" class="font-medium">{{ getAdjustmentIcon(pricing.adjustments.trend) }}</span>
                    Tendance
                  </span>
                  <span :class="['font-semibold', getAdjustmentColor(pricing.adjustments.trend)]">
                    {{ formatAdjustment(pricing.adjustments.trend) }}
                  </span>
                </div>
                <div v-if="pricing.adjustments.trend_detail" class="text-xs text-gray-400 font-mono pl-4">
                  {{ pricing.adjustments.trend_detail.actual_value || '—' }}
                  ({{ formatCoef(pricing.adjustments.trend_detail.actual_coef) }})
                  − {{ pricing.adjustments.trend_detail.expected_best || 'aucun attendu' }}
                  ({{ formatCoef(pricing.adjustments.trend_detail.expected_coef) }})
                </div>
              </div>

              <!-- Feature -->
              <div class="space-y-0.5">
                <div class="flex items-center justify-between">
                  <span class="text-gray-600">
                    <span :class="getAdjustmentColor(pricing.adjustments.feature)" class="font-medium">{{ getAdjustmentIcon(pricing.adjustments.feature) }}</span>
                    Caractéristiques
                  </span>
                  <span :class="['font-semibold', getAdjustmentColor(pricing.adjustments.feature)]">
                    {{ formatAdjustment(pricing.adjustments.feature) }}
                  </span>
                </div>
                <div v-if="pricing.adjustments.feature_detail" class="text-xs text-gray-400 font-mono pl-4">
                  {{ pricing.adjustments.feature_detail.actual_value || '—' }}
                  ({{ formatCoef(pricing.adjustments.feature_detail.actual_coef) }})
                  − {{ pricing.adjustments.feature_detail.expected_best || 'aucun attendu' }}
                  ({{ formatCoef(pricing.adjustments.feature_detail.expected_coef) }})
                </div>
              </div>

              <!-- Fit -->
              <div class="space-y-0.5">
                <div class="flex items-center justify-between">
                  <span class="text-gray-600">
                    <span :class="getAdjustmentColor(pricing.adjustments.fit)" class="font-medium">{{ getAdjustmentIcon(pricing.adjustments.fit) }}</span>
                    Coupe
                  </span>
                  <span :class="['font-semibold', getAdjustmentColor(pricing.adjustments.fit)]">
                    {{ formatAdjustment(pricing.adjustments.fit) }}
                  </span>
                </div>
                <div v-if="pricing.adjustments.fit_detail" class="text-xs text-gray-400 font-mono pl-4">
                  {{ pricing.adjustments.fit_detail.actual_value || '—' }}
                  ({{ formatCoef(pricing.adjustments.fit_detail.actual_coef) }})
                  − {{ pricing.adjustments.fit_detail.expected_best || 'aucun attendu' }}
                  ({{ formatCoef(pricing.adjustments.fit_detail.expected_coef) }})
                </div>
              </div>

              <!-- Total Adjustments -->
              <div class="flex items-center justify-between pt-2 mt-1 border-t border-gray-200">
                <span class="font-semibold text-gray-900">Total ajustements additifs</span>
                <span :class="['text-base font-bold', getAdjustmentColor(totalAdditiveAdj)]">
                  {{ formatAdjustment(totalAdditiveAdj) }}
                </span>
              </div>

              <!-- After adjustments -->
              <div class="flex justify-between pt-1.5 border-t border-gray-200">
                <span class="text-gray-600">Après ajustements</span>
                <span class="font-semibold text-gray-900">
                  {{ formatPrice(priceAfterCondition) }} × (1 + {{ formatAdjustment(totalAdditiveAdj) }}) = {{ formatPrice(pricing.standard_price) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Step 4: Final Formula -->
          <div>
            <h5 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Formule complète
            </h5>
            <div class="p-2.5 bg-gray-50 rounded-md text-xs text-gray-600 font-mono space-y-1">
              <p>
                Standard = Base ({{ formatPrice(pricing.base_price) }})
                × Model ({{ formatCoefficient(pricing.model_coefficient) }})
                × Condition ({{ formatCoefficient(pricing.condition_multiplier) }})
                × (1 + {{ formatAdjustment(totalAdditiveAdj) }})
              </p>
              <p class="text-gray-500">
                Quick = {{ formatPrice(pricing.standard_price) }} × 0.75 = {{ formatPrice(pricing.quick_price) }}
                · Premium = {{ formatPrice(pricing.standard_price) }} × 1.30 = {{ formatPrice(pricing.premium_price) }}
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { PriceOutput } from '~/composables/usePricingCalculation'
import { useAuthStore } from '~/stores/auth'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

interface Props {
  pricing: PriceOutput
  selectedPrice?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  selectedPrice: null
})

const emit = defineEmits<{
  'select-price': [price: number]
}>()

const toNumber = (value: string | number): number => {
  return typeof value === 'string' ? parseFloat(value) : value
}

const selectPrice = (price: string | number) => {
  emit('select-price', toNumber(price))
}

const isSelected = (price: string | number) => {
  return props.selectedPrice != null && props.selectedPrice === toNumber(price)
}

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

// Intermediate calculation amounts for step-by-step display
const priceAfterModel = computed(() => {
  return toNumber(props.pricing.base_price) * toNumber(props.pricing.model_coefficient)
})

const conditionMult = computed(() => {
  return toNumber(props.pricing.condition_multiplier)
})

const priceAfterCondition = computed(() => {
  return priceAfterModel.value * conditionMult.value
})

// Total additive adjustments (without condition, which is a multiplier)
const totalAdditiveAdj = computed(() => {
  const adj = props.pricing.adjustments
  return toNumber(adj.origin) + toNumber(adj.decade) + toNumber(adj.trend) + toNumber(adj.feature) + toNumber(adj.fit)
})

// Format a coefficient value with sign
const formatCoef = (value: string | number) => {
  const num = typeof value === 'string' ? parseFloat(value) : value
  return num >= 0 ? `+${num.toFixed(2)}` : num.toFixed(2)
}
</script>

<style scoped>
/* Add any component-specific styles if needed */
</style>

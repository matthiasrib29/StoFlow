<template>
  <div class="condition-slider">
    <div class="flex items-center justify-between mb-2">
      <label class="block text-xs font-semibold text-secondary-900">
        État du produit *
      </label>
      <span v-if="modelValue !== null" class="text-sm font-bold" :class="conditionColorClass">
        {{ modelValue }}/10 - {{ currentLabel.label }}
      </span>
    </div>

    <!-- Slider -->
    <div class="slider-container">
      <Slider
        :model-value="modelValue ?? 5"
        :min="0"
        :max="10"
        :step="1"
        class="w-full"
        :class="{ 'p-invalid': hasError }"
        @update:model-value="$emit('update:modelValue', $event)"
      />

      <!-- Labels sous le slider -->
      <div class="flex justify-between mt-1 text-[10px] text-gray-400">
        <span>Défectueux</span>
        <span>Usé</span>
        <span>Bon</span>
        <span>Très bon</span>
        <span>Neuf</span>
      </div>
    </div>

    <!-- Description de l'état actuel -->
    <p v-if="modelValue !== null" class="text-xs text-gray-500 mt-2 italic">
      {{ currentLabel.description }}
    </p>

    <!-- Message d'erreur -->
    <small v-if="hasError && errorMessage" class="p-error">
      {{ errorMessage }}
    </small>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { conditionLabels } from '~/types/product'

interface Props {
  modelValue: number | null
  hasError?: boolean
  errorMessage?: string
}

const props = withDefaults(defineProps<Props>(), {
  hasError: false,
  errorMessage: ''
})

defineEmits<{
  'update:modelValue': [value: number]
}>()

// Label actuel basé sur la valeur
const currentLabel = computed(() => {
  const value = props.modelValue ?? 5
  return conditionLabels[value] || conditionLabels[5]
})

// Couleur selon la condition
const conditionColorClass = computed(() => {
  const value = props.modelValue ?? 5

  if (value >= 9) return 'text-green-600'
  if (value >= 7) return 'text-green-500'
  if (value >= 5) return 'text-yellow-600'
  if (value >= 3) return 'text-orange-500'
  return 'text-red-500'
})
</script>

<style scoped>
.condition-slider :deep(.p-slider) {
  background: linear-gradient(to right, #ef4444, #f97316, #eab308, #22c55e, #16a34a);
  height: 8px;
  border-radius: 4px;
}

.condition-slider :deep(.p-slider-handle) {
  width: 20px;
  height: 20px;
  background: white;
  border: 3px solid #3b82f6;
  border-radius: 50%;
  margin-top: -6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.condition-slider :deep(.p-slider-handle:hover) {
  border-color: #2563eb;
  transform: scale(1.1);
}

.condition-slider :deep(.p-slider-range) {
  background: transparent;
}
</style>

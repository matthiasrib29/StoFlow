<template>
  <div class="condition-selector">
    <div class="flex items-center justify-between mb-3">
      <label class="block text-xs font-semibold text-secondary-900">
        État du produit *
      </label>
    </div>

    <!-- Condition buttons -->
    <div class="condition-buttons">
      <button
        v-for="condition in conditions"
        :key="condition.value"
        type="button"
        class="condition-btn"
        :class="{
          'selected': modelValue === condition.value,
          [condition.colorClass]: true
        }"
        @click="$emit('update:modelValue', condition.value)"
      >
        <span class="condition-label">{{ condition.label }}</span>
        <span class="condition-score">{{ condition.value }}/10</span>
      </button>
    </div>

    <!-- Description -->
    <p v-if="modelValue !== null && currentLabel.description" class="text-xs text-gray-500 mt-3 text-center italic">
      {{ currentLabel.description }}
    </p>

    <!-- Error message -->
    <small v-if="hasError && errorMessage" class="text-red-500 text-xs mt-2 block">
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

// Condition options
const conditions = [
  { value: 1, label: 'Défectueux', colorClass: 'color-red' },
  { value: 3, label: 'Usé', colorClass: 'color-orange' },
  { value: 5, label: 'Bon', colorClass: 'color-yellow' },
  { value: 7, label: 'Très bon', colorClass: 'color-lime' },
  { value: 10, label: 'Neuf', colorClass: 'color-green' }
]

// Current label based on value
const currentLabel = computed(() => {
  const value = props.modelValue ?? 5
  return conditionLabels[value] || conditionLabels[5]
})
</script>

<style scoped>
.condition-selector {
  padding: 4px 0;
}

.condition-buttons {
  display: flex;
  gap: 8px;
}

.condition-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border-radius: 10px;
  border: 2px solid transparent;
  background: #f3f4f6;
  cursor: pointer;
  transition: all 0.2s ease;
}

.condition-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.condition-label {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  transition: color 0.2s ease;
}

.condition-score {
  font-size: 10px;
  color: #9ca3af;
  margin-top: 2px;
  transition: color 0.2s ease;
}

/* Color variants */
.condition-btn.color-red:hover,
.condition-btn.color-red.selected {
  background: #fef2f2;
  border-color: #ef4444;
}
.condition-btn.color-red.selected .condition-label { color: #dc2626; }
.condition-btn.color-red.selected .condition-score { color: #ef4444; }

.condition-btn.color-orange:hover,
.condition-btn.color-orange.selected {
  background: #fff7ed;
  border-color: #f97316;
}
.condition-btn.color-orange.selected .condition-label { color: #ea580c; }
.condition-btn.color-orange.selected .condition-score { color: #f97316; }

.condition-btn.color-yellow:hover,
.condition-btn.color-yellow.selected {
  background: #fefce8;
  border-color: #eab308;
}
.condition-btn.color-yellow.selected .condition-label { color: #ca8a04; }
.condition-btn.color-yellow.selected .condition-score { color: #eab308; }

.condition-btn.color-lime:hover,
.condition-btn.color-lime.selected {
  background: #f0fdf4;
  border-color: #22c55e;
}
.condition-btn.color-lime.selected .condition-label { color: #16a34a; }
.condition-btn.color-lime.selected .condition-score { color: #22c55e; }

.condition-btn.color-green:hover,
.condition-btn.color-green.selected {
  background: #ecfdf5;
  border-color: #10b981;
}
.condition-btn.color-green.selected .condition-label { color: #059669; }
.condition-btn.color-green.selected .condition-score { color: #10b981; }

/* Selected state enhancements */
.condition-btn.selected {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.condition-btn.selected .condition-label {
  font-weight: 700;
}
</style>

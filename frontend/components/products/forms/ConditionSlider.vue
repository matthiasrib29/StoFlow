<template>
  <div>
    <label class="block text-xs font-semibold text-secondary-900 mb-2">
      État du produit *
    </label>

    <Select
      :model-value="modelValue"
      :options="conditionOptions"
      optionLabel="label"
      optionValue="value"
      placeholder="Sélectionner l'état"
      class="w-full"
      :class="{ 'p-invalid': hasError }"
      @update:model-value="$emit('update:modelValue', $event)"
    />

    <p v-if="modelValue !== null && currentDescription" class="text-xs text-gray-500 mt-2 italic">
      {{ currentDescription }}
    </p>

    <small v-if="hasError && errorMessage" class="text-red-500 text-xs mt-1 block">
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

// Options for the select dropdown (10 to 0, best to worst)
const conditionOptions = [
  { value: 10, label: '10 - Neuf' },
  { value: 9, label: '9 - Excellent' },
  { value: 8, label: '8 - Très bon' },
  { value: 7, label: '7 - Bon +' },
  { value: 6, label: '6 - Bon' },
  { value: 5, label: '5 - Assez bon' },
  { value: 4, label: '4 - Correct' },
  { value: 3, label: '3 - Usé acceptable' },
  { value: 2, label: '2 - Usé' },
  { value: 1, label: '1 - Très usé' },
  { value: 0, label: '0 - Défectueux' }
]

// Get description for current value
const currentDescription = computed(() => {
  if (props.modelValue === null) return ''
  return conditionLabels[props.modelValue]?.description || ''
})
</script>

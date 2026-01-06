<template>
  <div>
    <label class="block text-xs font-semibold mb-1 text-secondary-900 flex items-center gap-1">
      {{ label }}
      <span v-if="required">*</span>
      <i
        v-if="isValid"
        class="pi pi-check-circle text-green-500 text-xs"
      />
    </label>

    <!-- AutoComplete -->
    <AutoComplete
      v-if="type === 'autocomplete'"
      :model-value="stringValue"
      :suggestions="suggestions"
      :min-length="1"
      :placeholder="placeholder"
      class="w-full"
      :class="fieldClasses"
      :loading="loading"
      @update:model-value="handleChange"
      @complete="$emit('search', $event)"
      @blur="$emit('blur')"
    />

    <!-- Select -->
    <Select
      v-else-if="type === 'select'"
      :model-value="stringValue"
      :options="options"
      option-label="label"
      option-value="value"
      :placeholder="placeholder"
      class="w-full"
      :class="fieldClasses"
      :show-clear="showClear"
      :loading="loading"
      @update:model-value="handleChange"
      @blur="$emit('blur')"
    />

    <!-- InputText -->
    <InputText
      v-else-if="type === 'text'"
      :model-value="stringValue"
      :placeholder="placeholder"
      class="w-full"
      :class="fieldClasses"
      @update:model-value="handleChange"
      @blur="$emit('blur')"
    />

    <!-- Chips -->
    <Chips
      v-else-if="type === 'chips'"
      :model-value="arrayValue"
      :placeholder="placeholder"
      class="w-full"
      @update:model-value="handleChange"
    />

    <!-- Textarea -->
    <Textarea
      v-else-if="type === 'textarea'"
      :model-value="stringValue"
      :placeholder="placeholder"
      :rows="rows"
      class="w-full"
      @update:model-value="handleChange"
    />

    <!-- Helper text -->
    <small v-if="helperText && !hasError" class="text-xs text-gray-500">
      {{ helperText }}
    </small>

    <!-- Error message -->
    <small v-if="hasError" class="p-error block">
      {{ errorMessage }}
    </small>
  </div>
</template>

<script setup lang="ts">
import type { AttributeOption } from '~/composables/useAttributes'

type FieldType = 'autocomplete' | 'select' | 'text' | 'chips' | 'textarea'

interface Props {
  type: FieldType
  label: string
  modelValue: string | string[] | null | undefined
  placeholder?: string
  required?: boolean
  hasError?: boolean
  errorMessage?: string
  isValid?: boolean
  loading?: boolean
  showClear?: boolean
  helperText?: string
  rows?: number
  // For autocomplete
  suggestions?: string[]
  // For select
  options?: AttributeOption[]
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '...',
  required: false,
  hasError: false,
  errorMessage: '',
  isValid: false,
  loading: false,
  showClear: true,
  helperText: '',
  rows: 2,
  suggestions: () => [],
  options: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: string | string[] | null]
  'search': [event: { query: string }]
  'blur': []
}>()

const fieldClasses = computed(() => ({
  'p-invalid': props.hasError,
  'border-green-400': props.isValid
}))

// Computed values for type-safe binding to PrimeVue components
const stringValue = computed(() => {
  if (typeof props.modelValue === 'string') return props.modelValue
  return props.modelValue ?? ''
})

const arrayValue = computed(() => {
  if (Array.isArray(props.modelValue)) return props.modelValue
  return []
})

const handleChange = (value: string | string[] | null | undefined) => {
  emit('update:modelValue', value ?? null)
}
</script>

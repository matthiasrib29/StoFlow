<template>
  <div>
    <label class="block text-xs font-semibold mb-1 text-secondary-900 flex items-center gap-1">
      {{ label }}
      <span v-if="required">*</span>
      <i
        v-if="isValid"
        class="pi pi-check-circle text-green-500 text-xs"
      />
      <span v-if="maxSelection && type === 'multiselect'" class="text-gray-400 font-normal text-[10px]">
        (max {{ maxSelection }})
      </span>
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

    <!-- Select with color preview -->
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
      :filter="filterMode !== 'none'"
      :filter-placeholder="filterPlaceholder"
      @update:model-value="handleChange"
      @filter="handleFilter"
      @blur="$emit('blur')"
    >
      <template v-if="showColorPreview" #option="{ option }">
        <div
          class="flex items-center gap-2.5 -mx-3 -my-1.5 px-3 py-2 rounded-md transition-all"
          :style="getOptionBackgroundStyle(option)"
        >
          <span
            v-if="option.hex_code"
            class="w-4 h-4 rounded-full border-2 border-white/60 flex-shrink-0 shadow"
            :style="{ backgroundColor: option.hex_code }"
          />
          <span
            v-else-if="option.value === 'Multicolor'"
            class="w-4 h-4 rounded-full border-2 border-white/60 flex-shrink-0 shadow"
            style="background: conic-gradient(red, orange, yellow, green, blue, purple, red)"
          />
          <span class="font-medium text-gray-800">{{ option.label }}</span>
        </div>
      </template>
      <template v-if="showColorPreview" #value="{ value }">
        <div v-if="value" class="flex items-center gap-2">
          <span
            v-if="getColorHex(value)"
            class="w-4 h-4 rounded border border-gray-300 flex-shrink-0"
            :style="{ backgroundColor: getColorHex(value) }"
          />
          <span
            v-else-if="value === 'Multicolor'"
            class="w-4 h-4 rounded border border-gray-300 flex-shrink-0"
            style="background: linear-gradient(135deg, red, orange, yellow, green, blue, purple)"
          />
          <span>{{ getColorLabel(value) }}</span>
        </div>
        <span v-else class="text-gray-400">{{ placeholder }}</span>
      </template>
    </Select>

    <!-- MultiSelect with color preview -->
    <MultiSelect
      v-else-if="type === 'multiselect'"
      :model-value="arrayValue"
      :options="options"
      option-label="label"
      option-value="value"
      :placeholder="placeholder"
      class="w-full"
      :class="fieldClasses"
      :loading="loading"
      :filter="filterMode !== 'none'"
      :filter-placeholder="filterPlaceholder"
      :selection-limit="maxSelection"
      display="chip"
      @update:model-value="handleMultiSelectChange"
      @filter="handleFilter"
      @blur="$emit('blur')"
    >
      <template v-if="showColorPreview" #option="{ option }">
        <div
          class="flex items-center gap-2.5 -mx-3 -my-1.5 px-3 py-2 rounded-md transition-all"
          :style="getOptionBackgroundStyle(option)"
        >
          <span
            v-if="option.hex_code"
            class="w-4 h-4 rounded-full border-2 border-white/60 flex-shrink-0 shadow"
            :style="{ backgroundColor: option.hex_code }"
          />
          <span
            v-else-if="option.value === 'Multicolor'"
            class="w-4 h-4 rounded-full border-2 border-white/60 flex-shrink-0 shadow"
            style="background: conic-gradient(red, orange, yellow, green, blue, purple, red)"
          />
          <span class="font-medium text-gray-800">{{ option.label }}</span>
        </div>
      </template>
      <template v-if="showColorPreview" #chip="{ value }">
        <div class="inline-flex items-center gap-1.5 bg-gray-100 rounded-full px-2.5 py-1 mr-1">
          <span
            v-if="getColorHex(value)"
            class="w-3.5 h-3.5 rounded-full border border-gray-300 flex-shrink-0 shadow-sm"
            :style="{ backgroundColor: getColorHex(value) }"
          />
          <span
            v-else-if="value === 'Multicolor'"
            class="w-3.5 h-3.5 rounded-full border border-gray-300 flex-shrink-0 shadow-sm"
            style="background: conic-gradient(red, orange, yellow, green, blue, purple, red)"
          />
          <span class="text-xs font-medium text-gray-700">{{ getColorLabel(value) }}</span>
        </div>
      </template>
    </MultiSelect>

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
import { useDebounceFn } from '@vueuse/core'

type FieldType = 'autocomplete' | 'select' | 'multiselect' | 'text' | 'chips' | 'textarea'

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
  // For select/multiselect
  options?: AttributeOption[]
  // For searchable select
  filterMode?: 'local' | 'api' | 'none'
  filterPlaceholder?: string
  // For multiselect
  maxSelection?: number
  // For color preview
  showColorPreview?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '...',
  required: false,
  hasError: false,
  errorMessage: '',
  isValid: false,
  loading: false,
  showClear: false,
  helperText: '',
  rows: 2,
  suggestions: () => [],
  options: () => [],
  filterMode: 'none',
  filterPlaceholder: 'Rechercher...',
  maxSelection: undefined,
  showColorPreview: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string | string[] | null]
  'search': [event: { query: string }]
  'filter': [event: string]
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
  // If single string value, convert to array for multiselect
  if (typeof props.modelValue === 'string' && props.modelValue) return [props.modelValue]
  return []
})

const handleChange = (value: string | string[] | null | undefined) => {
  emit('update:modelValue', value ?? null)
}

const handleMultiSelectChange = (value: string[] | null | undefined) => {
  emit('update:modelValue', value ?? [])
}

// Handle filter events for searchable select
const handleFilter = (event: any) => {
  if (props.filterMode === 'api') {
    // API search (debounced)
    const query = typeof event === 'string' ? event : event.value || event.query || ''
    debouncedApiFilter(query)
  }
  // Local filtering is handled automatically by PrimeVue
}

// Debounced API filter (300ms delay)
const debouncedApiFilter = useDebounceFn((query: string) => {
  emit('filter', query)
}, 300)

// Helper functions for color preview
const getColorHex = (value: string): string | null => {
  const option = props.options?.find(o => o.value === value)
  return option?.hex_code || null
}

const getColorLabel = (value: string): string => {
  const option = props.options?.find(o => o.value === value)
  return option?.label || value
}

// Get background style with color at 25% opacity
const getOptionBackgroundStyle = (option: any): Record<string, string> => {
  if (option.hex_code) {
    return { backgroundColor: `${option.hex_code}30` } // 30 = ~19% opacity in hex
  }
  if (option.value === 'Multicolor') {
    return {
      background: 'linear-gradient(90deg, rgba(255,0,0,0.2), rgba(255,165,0,0.2), rgba(255,255,0,0.2), rgba(0,128,0,0.2), rgba(0,0,255,0.2), rgba(128,0,128,0.2))'
    }
  }
  return {}
}
</script>

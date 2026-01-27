<template>
  <div class="form-field-spacing">
    <!-- First row: Category (Wizard), Brand, Gender -->
    <div class="form-field-spacing">
      <!-- Category Wizard -->
      <div>
        <label class="block text-xs font-semibold mb-2 text-secondary-900 flex items-center gap-1">
          Catégorie
          <span class="text-red-500">*</span>
          <i
            v-if="validation?.isFieldValid?.('category')"
            class="pi pi-check-circle text-green-500 text-xs"
          />
        </label>
        <ProductsFormsCharacteristicsCategoryWizard
          :categories="options.categories"
          :genders="options.genders"
          :current-gender="currentGender"
          :model-value="category"
          @update:model-value="handleCategoryChange"
        />
        <small v-if="validation?.hasError('category') && validation?.getError('category')" class="p-error block mt-1">
          {{ validation?.getError('category') }}
        </small>
      </div>

      <!-- Brand (full width since gender is now auto-extracted from category) -->
      <ProductsFormsCharacteristicsAttributeField
        type="select"
        label="Marque"
        :model-value="brand"
        :options="filteredOptions.brands"
        filter-mode="api"
        filter-placeholder="Rechercher une marque..."
        placeholder="Ex: Nike, Levi's..."
        :required="true"
        :show-clear="false"
        :has-error="validation?.hasError('brand')"
        :error-message="validation?.getError('brand')"
        :is-valid="validation?.isFieldValid?.('brand')"
        :loading="loading.brands"
        @update:model-value="handleBrandChange"
        @filter="$emit('filterBrands', $event)"
        @blur="validation?.touch('brand')"
      />

      <!-- Model Reference -->
      <ProductsFormsCharacteristicsAttributeField
        type="text"
        label="Référence modèle"
        :model-value="model"
        placeholder="Ex: 501-0115, Air Max 90..."
        @update:model-value="$emit('update:model', $event)"
      />
    </div>

    <!-- Condition Slider -->
    <ProductsFormsConditionSlider
      :model-value="condition"
      :has-error="validation?.hasError('condition')"
      :error-message="validation?.getError('condition')"
      @update:model-value="$emit('update:condition', $event)"
    />

    <!-- Second row: Size, Color, Material -->
    <UiFormSection :columns="3" variant="flat">
      <!-- Size Original (optional) -->
      <ProductsFormsCharacteristicsAttributeField
        type="text"
        label="Taille (étiquette)"
        :model-value="sizeOriginal"
        placeholder="Ex: W32/L34, 42 EUR, XL..."
        helper-text="Taille exacte sur l'étiquette du vêtement"
        @update:model-value="handleSizeOriginalChange"
      />

      <!-- Size Normalized (required) -->
      <UiFormField
        label="Taille standardisée"
        :required="true"
        :has-error="validation?.hasError('size_normalized')"
        :error-message="validation?.getError('size_normalized')"
        :is-valid="validation?.isFieldValid?.('size_normalized')"
        :helper-text="suggestedSize && !suggestedSizeMatch
          ? `Taille suggérée (${suggestedSize}) non disponible dans les tailles standard`
          : 'Équivalent standard (S, M, L...)'
        "
      >
        <Select
          :model-value="sizeNormalized"
          :options="sortedSizes"
          option-label="label"
          option-value="value"
          placeholder="Sélectionner..."
          class="w-full"
          :loading="loading.sizes"
          filter
          filter-placeholder="Rechercher..."
          @update:model-value="handleSizeNormalizedChange"
        >
          <template #option="slotProps">
            <div class="flex items-center gap-2">
              <span>{{ slotProps.option.label }}</span>
              <span
                v-if="suggestedSize && slotProps.option.value.toLowerCase() === suggestedSize.toLowerCase()"
                class="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium"
              >
                Suggérée
              </span>
            </div>
          </template>
        </Select>
      </UiFormField>

      <!-- Color (multiselect with max 2) -->
      <ProductsFormsCharacteristicsAttributeField
        type="multiselect"
        label="Couleur"
        :model-value="colorArray"
        :options="filteredOptions.colors"
        filter-mode="local"
        filter-placeholder="Rechercher une couleur..."
        placeholder="Ex: Bleu, Noir..."
        :required="true"
        :max-selection="2"
        :show-color-preview="true"
        :has-error="validation?.hasError('color')"
        :error-message="validation?.getError('color')"
        :is-valid="validation?.isFieldValid?.('color')"
        :loading="loading.colors"
        @update:model-value="handleColorChange"
        @filter="$emit('filterColors', $event)"
        @blur="validation?.touch('color')"
      />

      <!-- Material (multiselect with max 3) -->
      <ProductsFormsCharacteristicsAttributeField
        type="multiselect"
        label="Matière"
        :model-value="materialArray"
        :options="filteredOptions.materials"
        filter-mode="local"
        filter-placeholder="Rechercher une matière..."
        placeholder="Ex: Coton, Denim..."
        :required="true"
        :max-selection="3"
        :has-error="validation?.hasError('material')"
        :error-message="validation?.getError('material')"
        :is-valid="validation?.isFieldValid?.('material')"
        :loading="loading.materials"
        @update:model-value="handleMaterialChange"
        @filter="$emit('filterMaterials', $event)"
        @blur="validation?.touch('material')"
      />
    </UiFormSection>
  </div>
</template>

<script setup lang="ts">
import type { AttributeOption, CategoryOption } from '~/composables/useAttributes'
import type { ProductAttributesLoading } from '~/composables/useProductAttributes'

interface ValidationObject {
  hasError: (field: string) => boolean
  getError: (field: string) => string
  isFieldValid?: (field: string) => boolean
  touch: (field: string) => void
  validateDebounced?: (field: string, value: string) => void
}

interface Props {
  // Values
  category: string
  currentGender?: string | null
  brand: string
  model: string | null
  condition: number | null
  sizeOriginal: string
  sizeNormalized: string | null
  color: string
  material: string
  // Suggested size from measurements
  suggestedSize?: string | null
  // Options
  options: {
    categories: CategoryOption[]
    genders: AttributeOption[]
    sizes: AttributeOption[]
  }
  // Filtered options for searchable select
  filteredOptions?: {
    brands: AttributeOption[]
    colors: AttributeOption[]
    materials: AttributeOption[]
  }
  // Loading states
  loading: ProductAttributesLoading
  // Validation
  validation?: ValidationObject
}

const props = withDefaults(defineProps<Props>(), {
  filteredOptions: () => ({
    brands: [],
    colors: [],
    materials: []
  })
})

const emit = defineEmits<{
  'update:category': [value: string]
  'update:brand': [value: string]
  'update:model': [value: string | null]
  // 'update:gender' removed - gender is auto-extracted from category
  'update:condition': [value: number]
  'update:sizeOriginal': [value: string]
  'update:sizeNormalized': [value: string | null]
  'update:color': [value: string]
  'update:material': [value: string]
  'filterBrands': [query: string]
  'filterColors': [query: string]
  'filterMaterials': [query: string]
}>()

// --- Suggested size auto-fill logic ---

// Track manual selection to prevent auto-fill override
const userManuallySelectedSize = ref(false)

// Check if suggested size exists in available options
const suggestedSizeMatch = computed(() => {
  if (!props.suggestedSize || !props.options.sizes?.length) return null
  return props.options.sizes.find(
    (s) => s.value.toLowerCase() === props.suggestedSize!.toLowerCase()
  ) ?? null
})

// Size sort order: literal sizes first, then W sizes
const LITERAL_SIZE_ORDER = [
  'XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL', '4XL',
  'one-size', 'TAILLE UNIQUE'
]

const sizeSortKey = (value: string): [number, number, number] => {
  // Group 0: literal letter sizes (XXS, XS, S, M, L...)
  const literalIndex = LITERAL_SIZE_ORDER.indexOf(value.toUpperCase())
  if (literalIndex !== -1) return [0, literalIndex, 0]

  // Group 1: numeric sizes (34, 36, 38...)
  if (/^\d+$/.test(value)) return [1, parseInt(value), 0]

  // Group 2: W sizes (W32, W32/L34...)
  const wMatch = value.match(/^W(\d+)(?:\/L(\d+))?$/)
  if (wMatch) {
    const w = parseInt(wMatch[1])
    const l = wMatch[2] ? parseInt(wMatch[2]) : 0
    return [2, w, l]
  }

  // Group 3: everything else
  return [3, 0, 0]
}

// Sorted sizes: suggested first, then literal, then W sizes
const sortedSizes = computed(() => {
  if (!props.options.sizes?.length) return props.options.sizes

  const sorted = [...props.options.sizes].sort((a, b) => {
    const keyA = sizeSortKey(a.value)
    const keyB = sizeSortKey(b.value)
    for (let i = 0; i < 3; i++) {
      if (keyA[i] !== keyB[i]) return keyA[i] - keyB[i]
    }
    return 0
  })

  // Move suggested size to the top if it exists
  if (suggestedSizeMatch.value) {
    const matchValue = suggestedSizeMatch.value.value
    const rest = sorted.filter((s) => s.value !== matchValue)
    return [suggestedSizeMatch.value, ...rest]
  }

  return sorted
})

// Auto-fill when suggestedSize changes (only if user hasn't manually selected)
watch(() => props.suggestedSize, (newSuggested) => {
  if (userManuallySelectedSize.value || !newSuggested) return
  if (suggestedSizeMatch.value) {
    emit('update:sizeNormalized', suggestedSizeMatch.value.value)
  }
})

// Handle manual selection
const handleSizeNormalizedChange = (value: string | null) => {
  userManuallySelectedSize.value = true
  emit('update:sizeNormalized', value)
}

// Don't auto-fill over existing size on edit mode
onMounted(() => {
  if (props.sizeNormalized) {
    userManuallySelectedSize.value = true
  }
})

// Convert color string to array for multiselect
// Backend stores as comma-separated string, frontend uses array
const colorArray = computed(() => {
  if (!props.color) return []
  // If already contains comma, split it
  if (props.color.includes(',')) {
    return props.color.split(',').map(c => c.trim()).filter(Boolean)
  }
  // Single color
  return [props.color]
})

// Convert material string to array for multiselect
const materialArray = computed(() => {
  if (!props.material) return []
  if (props.material.includes(',')) {
    return props.material.split(',').map(m => m.trim()).filter(Boolean)
  }
  return [props.material]
})

// Handlers with validation
const handleCategoryChange = (value: string | string[] | null) => {
  const val = (typeof value === 'string' ? value : '') || ''
  emit('update:category', val)
  props.validation?.validateDebounced?.('category', val)
}

const handleBrandChange = (value: string | string[] | null) => {
  const val = (typeof value === 'string' ? value : '') || ''
  emit('update:brand', val)
  props.validation?.validateDebounced?.('brand', val)
}

// handleGenderChange removed - gender is auto-extracted from category

const handleSizeOriginalChange = (value: string | string[] | null) => {
  const val = (typeof value === 'string' ? value : '') || ''
  emit('update:sizeOriginal', val)
  props.validation?.validateDebounced?.('size_original', val)
}

const handleColorChange = (value: string | string[] | null) => {
  // Convert array to comma-separated string for backend storage
  let val = ''
  if (Array.isArray(value)) {
    val = value.join(', ')
  } else if (typeof value === 'string') {
    val = value
  }
  emit('update:color', val)
  props.validation?.validateDebounced?.('color', val)
}

const handleMaterialChange = (value: string | string[] | null) => {
  // Convert array to comma-separated string for backend storage
  let val = ''
  if (Array.isArray(value)) {
    val = value.join(', ')
  } else if (typeof value === 'string') {
    val = value
  }
  emit('update:material', val)
  props.validation?.validateDebounced?.('material', val)
}
</script>

<template>
  <div class="bg-gray-50 rounded-lg p-4 space-y-4">
    <h4 class="text-xs font-semibold text-gray-600 uppercase">Obligatoires</h4>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- Category -->
      <ProductsFormsCharacteristicsAttributeField
        type="autocomplete"
        label="Catégorie"
        :model-value="category"
        :suggestions="suggestions.categories"
        placeholder="Sélectionner..."
        :required="true"
        :has-error="validation?.hasError('category')"
        :error-message="validation?.getError('category')"
        :is-valid="validation?.isFieldValid?.('category')"
        :loading="loading.categories"
        @update:model-value="handleCategoryChange"
        @search="$emit('searchCategories', $event)"
        @blur="validation?.touch('category')"
      />

      <!-- Brand -->
      <ProductsFormsCharacteristicsAttributeField
        type="autocomplete"
        label="Marque"
        :model-value="brand"
        :suggestions="suggestions.brands"
        placeholder="Ex: Nike, Levi's..."
        :required="true"
        :has-error="validation?.hasError('brand')"
        :error-message="validation?.getError('brand')"
        :is-valid="validation?.isFieldValid?.('brand')"
        :loading="loading.brands"
        @update:model-value="handleBrandChange"
        @search="$emit('searchBrands', $event)"
        @blur="validation?.touch('brand')"
      />

      <!-- Gender -->
      <ProductsFormsCharacteristicsAttributeField
        type="select"
        label="Genre"
        :model-value="gender"
        :options="options.genders"
        placeholder="Sélectionner..."
        :required="true"
        :has-error="validation?.hasError('gender')"
        :error-message="validation?.getError('gender')"
        :is-valid="validation?.isFieldValid?.('gender')"
        :loading="loading.genders"
        :show-clear="false"
        @update:model-value="handleGenderChange"
        @blur="validation?.touch('gender')"
      />
    </div>

    <!-- Condition Slider -->
    <ProductsFormsConditionSlider
      :model-value="condition"
      :has-error="validation?.hasError('condition')"
      :error-message="validation?.getError('condition')"
      @update:model-value="$emit('update:condition', $event)"
    />

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- Size Original -->
      <ProductsFormsCharacteristicsAttributeField
        type="text"
        label="Taille (étiquette)"
        :model-value="sizeOriginal"
        placeholder="Ex: W32/L34, 42 EUR, XL..."
        :required="true"
        :has-error="validation?.hasError('size_original')"
        :error-message="validation?.getError('size_original')"
        :is-valid="validation?.isFieldValid?.('size_original')"
        helper-text="Taille exacte sur l'étiquette du vêtement"
        @update:model-value="handleSizeOriginalChange"
        @blur="validation?.touch('size_original')"
      />

      <!-- Size Normalized -->
      <div>
        <label class="block text-xs font-semibold mb-1 text-secondary-900">Taille standardisée</label>
        <Select
          :model-value="sizeNormalized"
          :options="options.sizes"
          option-label="label"
          option-value="value"
          placeholder="Sélectionner..."
          class="w-full"
          show-clear
          :loading="loading.sizes"
          @update:model-value="$emit('update:sizeNormalized', $event)"
        />
        <small class="text-xs text-gray-500">Équivalent standard (S, M, L...)</small>
      </div>

      <!-- Color -->
      <ProductsFormsCharacteristicsAttributeField
        type="autocomplete"
        label="Couleur"
        :model-value="color"
        :suggestions="suggestions.colors"
        placeholder="Ex: Bleu, Noir..."
        :required="true"
        :has-error="validation?.hasError('color')"
        :error-message="validation?.getError('color')"
        :is-valid="validation?.isFieldValid?.('color')"
        :loading="loading.colors"
        @update:model-value="handleColorChange"
        @search="$emit('searchColors', $event)"
        @blur="validation?.touch('color')"
      />

      <!-- Material -->
      <ProductsFormsCharacteristicsAttributeField
        type="autocomplete"
        label="Matière"
        :model-value="material"
        :suggestions="suggestions.materials"
        placeholder="Ex: Coton, Denim..."
        :required="true"
        :has-error="validation?.hasError('material')"
        :error-message="validation?.getError('material')"
        :is-valid="validation?.isFieldValid?.('material')"
        :loading="loading.materials"
        @update:model-value="handleMaterialChange"
        @search="$emit('searchMaterials', $event)"
        @blur="validation?.touch('material')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AttributeOption } from '~/composables/useAttributes'
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
  brand: string
  gender: string
  condition: number | null
  sizeOriginal: string
  sizeNormalized: string | null
  color: string
  material: string
  // Options
  options: {
    genders: AttributeOption[]
    sizes: AttributeOption[]
  }
  // Suggestions
  suggestions: {
    categories: string[]
    brands: string[]
    colors: string[]
    materials: string[]
  }
  // Loading states
  loading: ProductAttributesLoading
  // Validation
  validation?: ValidationObject
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:category': [value: string]
  'update:brand': [value: string]
  'update:gender': [value: string]
  'update:condition': [value: number]
  'update:sizeOriginal': [value: string]
  'update:sizeNormalized': [value: string | null]
  'update:color': [value: string]
  'update:material': [value: string]
  'searchCategories': [event: { query: string }]
  'searchBrands': [event: { query: string }]
  'searchColors': [event: { query: string }]
  'searchMaterials': [event: { query: string }]
}>()

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

const handleGenderChange = (value: string | string[] | null) => {
  const val = (typeof value === 'string' ? value : '') || ''
  emit('update:gender', val)
  props.validation?.validateDebounced?.('gender', val)
}

const handleSizeOriginalChange = (value: string | string[] | null) => {
  const val = (typeof value === 'string' ? value : '') || ''
  emit('update:sizeOriginal', val)
  props.validation?.validateDebounced?.('size_original', val)
}

const handleColorChange = (value: string | string[] | null) => {
  const val = (typeof value === 'string' ? value : '') || ''
  emit('update:color', val)
  props.validation?.validateDebounced?.('color', val)
}

const handleMaterialChange = (value: string | string[] | null) => {
  const val = (typeof value === 'string' ? value : '') || ''
  emit('update:material', val)
  props.validation?.validateDebounced?.('material', val)
}
</script>

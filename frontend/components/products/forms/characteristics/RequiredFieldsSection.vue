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
      <UiFormField
        label="Taille standardisée"
        helper-text="Équivalent standard (S, M, L...)"
      >
        <Select
          :model-value="sizeNormalized"
          :options="options.sizes"
          option-label="label"
          option-value="value"
          placeholder="Sélectionner..."
          class="w-full"
          :loading="loading.sizes"
          filter
          filter-placeholder="Rechercher..."
          @update:model-value="$emit('update:sizeNormalized', $event)"
        />
      </UiFormField>

      <!-- Color -->
      <ProductsFormsCharacteristicsAttributeField
        type="select"
        label="Couleur"
        :model-value="color"
        :options="filteredOptions.colors"
        filter-mode="local"
        filter-placeholder="Rechercher une couleur..."
        placeholder="Ex: Bleu, Noir..."
        :required="true"
        :show-clear="false"
        :has-error="validation?.hasError('color')"
        :error-message="validation?.getError('color')"
        :is-valid="validation?.isFieldValid?.('color')"
        :loading="loading.colors"
        @update:model-value="handleColorChange"
        @filter="$emit('filterColors', $event)"
        @blur="validation?.touch('color')"
      />

      <!-- Material -->
      <ProductsFormsCharacteristicsAttributeField
        type="select"
        label="Matière"
        :model-value="material"
        :options="filteredOptions.materials"
        filter-mode="local"
        filter-placeholder="Rechercher une matière..."
        placeholder="Ex: Coton, Denim..."
        :required="true"
        :show-clear="false"
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
  brand: string
  model: string | null
  // gender is auto-extracted from category, no longer a prop
  condition: number | null
  sizeOriginal: string
  sizeNormalized: string | null
  color: string
  material: string
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

<template>
  <form class="space-y-4" @submit.prevent="handleSubmit">
    <!-- AI Fill Section -->
    <ProductsFormsProductFormAISection
      :product-id="productId"
      :has-images="hasImages"
      :is-analyzing="isAnalyzingImages"
      :is-generating="isGeneratingDescription"
      @analyze="analyzeAndFillForm"
    />

    <!-- Basic Info: Title, Description, Price, Stock -->
    <ProductsFormsProductFormBasicInfo
      :title="modelValue.title"
      :description="modelValue.description"
      :price="modelValue.price"
      :stock-quantity="modelValue.stock_quantity"
      :product-id="productId"
      :is-generating="isGeneratingDescription"
      :calculated-price="calculatedPrice"
      :validation="validation"
      @update:title="handleFieldUpdate('title', $event)"
      @update:description="handleFieldUpdate('description', $event)"
      @update:price="updateField('price', $event)"
      @update:stock-quantity="updateField('stock_quantity', $event)"
      @generate-description="generateDescription"
    />

    <!-- Brand & Category -->
    <ProductsFormsProductFormBrandCategory
      :brand="modelValue.brand"
      :category="modelValue.category"
      :categories="categories"
      :brand-suggestions="brandSuggestionLabels"
      :loading-categories="loadingCategories"
      :validation="validation"
      @update:brand="handleFieldUpdate('brand', $event)"
      @update:category="handleFieldUpdate('category', $event)"
      @search-brand="handleBrandSearch"
    />

    <!-- Attributes (Condition, Size, Color, Material, etc.) -->
    <ProductsFormsProductFormAttributes
      :condition="modelValue.condition"
      :label-size="modelValue.label_size"
      :color="modelValue.color"
      :material="modelValue.material"
      :fit="modelValue.fit"
      :gender="modelValue.gender"
      :season="modelValue.season"
      :conditions="conditions"
      :genders="genders"
      :seasons="seasons"
      :loading-conditions="loadingConditions"
      :loading-genders="loadingGenders"
      :loading-seasons="loadingSeasons"
      :validation="validation"
      @update:condition="updateField('condition', $event)"
      @update:label-size="updateField('label_size', $event)"
      @update:color="updateField('color', $event)"
      @update:material="updateField('material', $event)"
      @update:fit="updateField('fit', $event)"
      @update:gender="updateField('gender', $event)"
      @update:season="updateField('season', $event)"
    />

    <!-- Dimensions -->
    <ProductsFormsProductFormDimensions
      :dim1="modelValue.dim1"
      :dim2="modelValue.dim2"
      :dim3="modelValue.dim3"
      :dim4="modelValue.dim4"
      :dim5="modelValue.dim5"
      :dim6="modelValue.dim6"
      :validation="validation"
      @update:dim1="updateField('dim1', $event)"
      @update:dim2="updateField('dim2', $event)"
      @update:dim3="updateField('dim3', $event)"
      @update:dim4="updateField('dim4', $event)"
      @update:dim5="updateField('dim5', $event)"
      @update:dim6="updateField('dim6', $event)"
    />

    <!-- Actions -->
    <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
      <Button
        type="button"
        label="Annuler"
        icon="pi pi-times"
        class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
        @click="$emit('cancel')"
      />
      <Button
        type="submit"
        :label="submitLabel"
        icon="pi pi-check"
        class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold"
        :loading="isSubmitting"
      />
    </div>
  </form>
</template>

<script setup lang="ts">
import type { AttributeOption } from '~/composables/useAttributes'
import { useLocaleStore } from '~/stores/locale'
import { useProductFormAI } from '~/composables/useProductFormAI'

interface ProductFormData {
  title: string
  description: string
  price: number | null
  brand: string
  category: string
  condition: string
  label_size: string
  color: string
  material?: string | null
  fit?: string | null
  gender?: string | null
  season?: string | null
  dim1?: number | null
  dim2?: number | null
  dim3?: number | null
  dim4?: number | null
  dim5?: number | null
  dim6?: number | null
  stock_quantity: number
}

interface Props {
  modelValue: ProductFormData
  isSubmitting?: boolean
  submitLabel?: string
  productId?: number
  hasImages?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSubmitting: false,
  submitLabel: 'Créer le produit',
  productId: undefined,
  hasImages: false
})

const emit = defineEmits<{
  'update:modelValue': [value: ProductFormData]
  submit: []
  cancel: []
}>()

// Composables
const {
  categories,
  conditions,
  genders,
  seasons,
  fetchAllAttributes,
  searchBrands,
  loadingCategories,
  loadingConditions,
  loadingGenders,
  loadingSeasons,
  clearCache
} = useAttributes()

const localeStore = useLocaleStore()
const validation = useProductFormValidation()
const { showWarn } = useAppToast()

// AI composable
const productIdRef = computed(() => props.productId)
const hasImagesRef = computed(() => props.hasImages)

const updateField = (field: keyof ProductFormData, value: any) => {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

const {
  isGeneratingDescription,
  isAnalyzingImages,
  generateDescription,
  analyzeAndFillForm,
} = useProductFormAI(productIdRef, hasImagesRef, updateField)

// Brand suggestions
const brandSuggestions = ref<AttributeOption[]>([])
const brandSuggestionLabels = computed(() => brandSuggestions.value.map(b => b.label))

// Calculated price (placeholder)
const calculatedPrice = computed(() => {
  if (props.modelValue.price) return null
  return null // TODO: Implement price calculation API
})

// Load attributes
const loadAllAttributes = async () => {
  await fetchAllAttributes(localeStore.locale)
}

onMounted(() => {
  loadAllAttributes()
})

watch(() => localeStore.locale, async () => {
  clearCache()
  await loadAllAttributes()
})

// Field update with validation
const handleFieldUpdate = (field: keyof ProductFormData, value: any) => {
  updateField(field, value)
  if (validation.touched.value.has(field)) {
    validation.validateAndSetError(field, value)
  }
}

// Form submit
const handleSubmit = () => {
  const isValid = validation.validateForm(props.modelValue)

  if (!isValid) {
    validation.touchAll(props.modelValue)
    showWarn('Formulaire invalide', 'Veuillez corriger les erreurs avant de continuer')
    return
  }

  emit('submit')
}

// Brand search
const handleBrandSearch = async (event: { query: string }) => {
  const results = await searchBrands(event.query)
  brandSuggestions.value = results
}
</script>

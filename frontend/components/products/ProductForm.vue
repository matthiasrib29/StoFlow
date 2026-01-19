<template>
  <form class="form-section-spacing" @submit.prevent="handleSubmit">
    <!-- ===== INDICATEUR AUTO-SAVE ===== -->
    <div v-if="productId && autoSave" class="flex items-center gap-2 text-xs mb-2">
      <i
        v-if="autoSave.isSaving.value"
        class="pi pi-spin pi-spinner text-primary-500"
      />
      <i
        v-else-if="autoSave.saveError.value"
        class="pi pi-exclamation-triangle text-error-500"
      />
      <i
        v-else-if="autoSave.lastSaved.value"
        class="pi pi-check-circle text-success-500"
      />
      <span
        :class="{
          'text-primary-600': autoSave.isSaving.value,
          'text-error-600': autoSave.saveError.value,
          'text-success-600': autoSave.lastSaved.value
        }"
      >
        {{ autoSave.statusText.value }}
      </span>
    </div>

    <!-- ===== SECTION 1: CARACTÉRISTIQUES ===== -->
    <div id="section-characteristics">
      <ProductsFormsProductFormCharacteristics
        :category="modelValue.category"
        :brand="modelValue.brand"
        :condition="modelValue.condition"
        :size-original="modelValue.size_original"
        :size-normalized="modelValue.size_normalized"
        :color="modelValue.color"
        :material="modelValue.material"
        :fit="modelValue.fit"
        :season="modelValue.season"
        :sport="modelValue.sport"
        :neckline="modelValue.neckline"
        :length="modelValue.length"
        :pattern="modelValue.pattern"
        :rise="modelValue.rise"
        :closure="modelValue.closure"
        :sleeve-length="modelValue.sleeve_length"
        :stretch="modelValue.stretch"
        :lining="modelValue.lining"
        :origin="modelValue.origin"
        :decade="modelValue.decade"
        :trend="modelValue.trend"
        :condition-sup="modelValue.condition_sup"
        :location="modelValue.location"
        :model="modelValue.model"
        :unique-feature="modelValue.unique_feature"
        :marking="modelValue.marking"
        :validation="validation"
        @update:category="handleCategoryChange($event)"
        @update:brand="updateField('brand', $event)"
        @update:condition="updateField('condition', $event)"
        @update:size-original="updateField('size_original', $event)"
        @update:size-normalized="updateField('size_normalized', $event)"
        @update:color="updateField('color', $event)"
        @update:material="updateField('material', $event)"
        @update:fit="updateField('fit', $event)"
        @update:season="updateField('season', $event)"
        @update:sport="updateField('sport', $event)"
        @update:neckline="updateField('neckline', $event)"
        @update:length="updateField('length', $event)"
        @update:pattern="updateField('pattern', $event)"
        @update:rise="updateField('rise', $event)"
        @update:closure="updateField('closure', $event)"
        @update:sleeve-length="updateField('sleeve_length', $event)"
        @update:stretch="updateField('stretch', $event)"
        @update:lining="updateField('lining', $event)"
        @update:origin="updateField('origin', $event)"
        @update:decade="updateField('decade', $event)"
        @update:trend="updateField('trend', $event)"
        @update:condition-sup="updateField('condition_sup', $event)"
        @update:location="updateField('location', $event)"
        @update:model="updateField('model', $event)"
        @update:unique-feature="updateField('unique_feature', $event)"
        @update:marking="updateField('marking', $event)"
      />
    </div>

    <!-- ===== SECTION 2: MESURES ===== -->
    <div id="section-measures">
      <ProductsFormsProductFormMeasures
        :category="modelValue.category"
        :dim1="modelValue.dim1"
        :dim2="modelValue.dim2"
        :dim3="modelValue.dim3"
        :dim4="modelValue.dim4"
        :dim5="modelValue.dim5"
        :dim6="modelValue.dim6"
        @update:dim1="updateField('dim1', $event)"
        @update:dim2="updateField('dim2', $event)"
        @update:dim3="updateField('dim3', $event)"
        @update:dim4="updateField('dim4', $event)"
        @update:dim5="updateField('dim5', $event)"
        @update:dim6="updateField('dim6', $event)"
      />
    </div>

    <!-- ===== SECTION 3: INFORMATIONS PRODUIT (Titre, Description) ===== -->
    <div id="section-info">
      <ProductsFormsProductFormInfo
        :title="modelValue.title"
        :description="modelValue.description"
        :validation="validation"
        :product-id="productId"
        :brand="modelValue.brand"
        :category="modelValue.category"
        :gender="modelValue.gender"
        :size-normalized="modelValue.size_normalized"
        :colors="modelValue.color ? [modelValue.color] : undefined"
        :material="modelValue.material"
        :fit="modelValue.fit"
        :condition="modelValue.condition"
        :decade="modelValue.decade"
        :rise="modelValue.rise"
        :closure="modelValue.closure"
        :unique-feature="modelValue.unique_feature"
        :pattern="modelValue.pattern"
        :trend="modelValue.trend"
        :season="modelValue.season"
        :origin="modelValue.origin"
        :condition-sup="modelValue.condition_sup"
        @update:title="updateField('title', $event)"
        @update:description="updateField('description', $event)"
      />
    </div>

  </form>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ProductFormData } from '~/types/product'

interface Props {
  modelValue: ProductFormData
  isSubmitting?: boolean
  submitLabel?: string
  productId?: number
}

const props = withDefaults(defineProps<Props>(), {
  isSubmitting: false,
  submitLabel: 'Créer le produit',
  productId: undefined
})

const emit = defineEmits<{
  'update:modelValue': [value: ProductFormData]
  submit: []
  cancel: []
}>()

// Validation du formulaire
const validation = useProductFormValidation()
const { showWarn, showError, showSuccess } = useAppToast()
const { post } = useApi()

// Load product attributes to extract gender from category
const { options: attributeOptions } = useProductAttributes()

// Auto-save (uniquement en mode édition)
const autoSave = props.productId ? useAutoSave({
  productId: props.productId,
  debounceMs: 2000
}) : null

// Flash animation pour champs remplis par IA
const aiModifiedFields = ref<Set<string>>(new Set())

const flashField = (fieldName: string) => {
  aiModifiedFields.value.add(fieldName)
  setTimeout(() => {
    aiModifiedFields.value.delete(fieldName)
  }, 2000)
}

const isFieldFlashing = (fieldName: string) => {
  return aiModifiedFields.value.has(fieldName)
}

provide('isFieldFlashing', isFieldFlashing)

// Local form state to avoid race conditions when multiple fields update simultaneously
const localForm = ref<ProductFormData>({ ...props.modelValue })

// Sync local form with prop when prop changes from parent
watch(() => props.modelValue, (newVal) => {
  // Only update if the prop is different (to avoid loops)
  if (JSON.stringify(newVal) !== JSON.stringify(localForm.value)) {
    localForm.value = { ...newVal }
  }
}, { deep: true })

// Trigger auto-save when form changes (only in edit mode)
watch(() => props.modelValue, (newValue) => {
  if (autoSave && props.productId) {
    autoSave.triggerSave(newValue)
  }
}, { deep: true })

// Mettre à jour un champ
const updateField = <K extends keyof ProductFormData>(field: K, value: ProductFormData[K]) => {
  // Update local state first (synchronously)
  localForm.value = {
    ...localForm.value,
    [field]: value
  }

  // Emit the updated form
  emit('update:modelValue', { ...localForm.value })

  // Valider le champ si déjà touché
  if (validation.touched.value.has(field as string)) {
    validation.validateAndSetError(field as string, value)
  }
}

// Handle category change and auto-extract gender from category
const handleCategoryChange = (categoryValue: string) => {
  // Update category field
  updateField('category', categoryValue)

  // Auto-extract gender from category
  if (categoryValue && attributeOptions.categories.length > 0) {
    const selectedCategory = attributeOptions.categories.find(c => c.value === categoryValue)
    if (selectedCategory && selectedCategory.genders && selectedCategory.genders.length > 0) {
      // Get first gender from the category's genders array
      const genderValue = selectedCategory.genders[0]
      updateField('gender', genderValue)
    }
  }
}

// Soumettre le formulaire
const handleSubmit = () => {
  // Valider tous les champs obligatoires
  const requiredFields = ['title', 'description', 'category', 'brand', 'condition', 'size_original', 'color', 'gender', 'material']
  let isValid = true

  for (const field of requiredFields) {
    const value = props.modelValue[field as keyof ProductFormData]
    if (!value && value !== 0) {
      validation.touch(field)
      validation.validateAndSetError(field, value)
      isValid = false
    }
  }

  if (!isValid) {
    showWarn('Formulaire invalide', 'Veuillez remplir tous les champs obligatoires')
    return
  }

  emit('submit')
}

</script>

<template>
  <form class="space-y-6" @submit.prevent="handleSubmit">
    <!-- ===== BOUTON REMPLIR AVEC IA ===== -->
    <div
      v-if="productId && hasImages"
      class="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-lg p-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="bg-primary-100 rounded-full p-2">
            <i class="pi pi-sparkles text-primary-600 text-lg" />
          </div>
          <div>
            <h4 class="text-sm font-semibold text-primary-900">Remplissage automatique</h4>
            <p class="text-xs text-primary-700">Analysez les images pour remplir le formulaire</p>
          </div>
        </div>
        <Button
          type="button"
          label="Remplir avec l'IA"
          icon="pi pi-sparkles"
          class="p-button-primary"
          :loading="isAnalyzingImages"
          :disabled="isAnalyzingImages || isGeneratingDescription"
          @click="analyzeAndFillForm"
        />
      </div>
    </div>

    <!-- ===== SECTION 1: INFORMATIONS PRODUIT ===== -->
    <ProductsFormsProductFormInfo
      :title="modelValue.title"
      :description="modelValue.description"
      :price="modelValue.price"
      :stock-quantity="modelValue.stock_quantity"
      :product-id="productId"
      :is-generating-description="isGeneratingDescription"
      :validation="validation"
      @update:title="updateField('title', $event)"
      @update:description="updateField('description', $event)"
      @update:price="updateField('price', $event)"
      @update:stock-quantity="updateField('stock_quantity', $event)"
      @generate-description="generateDescription"
    />

    <!-- ===== SECTION 2: CARACTÉRISTIQUES ===== -->
    <ProductsFormsProductFormCharacteristics
      :category="modelValue.category"
      :brand="modelValue.brand"
      :condition="modelValue.condition"
      :size-original="modelValue.size_original"
      :size-normalized="modelValue.size_normalized"
      :color="modelValue.color"
      :gender="modelValue.gender"
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
      :origin="modelValue.origin"
      :decade="modelValue.decade"
      :trend="modelValue.trend"
      :condition-sup="modelValue.condition_sup"
      :location="modelValue.location"
      :model="modelValue.model"
      :unique-feature="modelValue.unique_feature"
      :marking="modelValue.marking"
      :validation="validation"
      @update:category="updateField('category', $event)"
      @update:brand="updateField('brand', $event)"
      @update:condition="updateField('condition', $event)"
      @update:size-original="updateField('size_original', $event)"
      @update:size-normalized="updateField('size_normalized', $event)"
      @update:color="updateField('color', $event)"
      @update:gender="updateField('gender', $event)"
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
      @update:origin="updateField('origin', $event)"
      @update:decade="updateField('decade', $event)"
      @update:trend="updateField('trend', $event)"
      @update:condition-sup="updateField('condition_sup', $event)"
      @update:location="updateField('location', $event)"
      @update:model="updateField('model', $event)"
      @update:unique-feature="updateField('unique_feature', $event)"
      @update:marking="updateField('marking', $event)"
    />

    <!-- ===== SECTION 3: MESURES & TARIFICATION ===== -->
    <ProductsFormsProductFormMeasures
      :category="modelValue.category"
      :dim1="modelValue.dim1"
      :dim2="modelValue.dim2"
      :dim3="modelValue.dim3"
      :dim4="modelValue.dim4"
      :dim5="modelValue.dim5"
      :dim6="modelValue.dim6"
      :pricing-rarity="modelValue.pricing_rarity"
      :pricing-quality="modelValue.pricing_quality"
      :pricing-style="modelValue.pricing_style"
      :pricing-details="modelValue.pricing_details"
      @update:dim1="updateField('dim1', $event)"
      @update:dim2="updateField('dim2', $event)"
      @update:dim3="updateField('dim3', $event)"
      @update:dim4="updateField('dim4', $event)"
      @update:dim5="updateField('dim5', $event)"
      @update:dim6="updateField('dim6', $event)"
      @update:pricing-rarity="updateField('pricing_rarity', $event)"
      @update:pricing-quality="updateField('pricing_quality', $event)"
      @update:pricing-style="updateField('pricing_style', $event)"
      @update:pricing-details="updateField('pricing_details', $event)"
    />

    <!-- ===== ACTIONS ===== -->
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
import { ref } from 'vue'
import type { ProductFormData } from '~/types/product'

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
  'submit': []
  'cancel': []
}>()

// Validation du formulaire
const validation = useProductFormValidation()
const { showSuccess, showError, showWarn } = useAppToast()

// API pour la génération IA
const { post } = useApi()

// États
const isGeneratingDescription = ref(false)
const isAnalyzingImages = ref(false)

// Mettre à jour un champ
const updateField = <K extends keyof ProductFormData>(field: K, value: ProductFormData[K]) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })

  // Valider le champ si déjà touché
  if (validation.touched.value.has(field as string)) {
    validation.validateAndSetError(field as string, value)
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

// Générer une description avec l'IA
const generateDescription = async () => {
  if (!props.productId) {
    showError('Erreur', 'Sauvegardez d\'abord le produit avant de générer une description')
    return
  }

  isGeneratingDescription.value = true

  try {
    const response = await post<{ description: string }>(
      `/products/${props.productId}/generate-description`
    )

    if (response?.description) {
      updateField('description', response.description)
      showSuccess('Description générée', 'La description a été générée par l\'IA')
    }
  } catch (error: any) {
    const message = error?.data?.detail || error?.message || 'Erreur lors de la génération'

    if (message.includes('Crédits IA insuffisants') || error?.status === 402) {
      showError('Crédits insuffisants', 'Vous n\'avez plus de crédits IA.')
    } else {
      showError('Erreur', message)
    }
  } finally {
    isGeneratingDescription.value = false
  }
}

// Interface pour la réponse de l'analyse d'images
interface VisionAnalysisResponse {
  attributes: Partial<ProductFormData> & { confidence?: number }
  model: string
  images_analyzed: number
  tokens_used: number
  cost: number
  processing_time_ms: number
}

// Analyser les images et remplir le formulaire avec l'IA
const analyzeAndFillForm = async () => {
  if (!props.productId) {
    showError('Erreur', 'Sauvegardez d\'abord le produit')
    return
  }

  if (!props.hasImages) {
    showError('Erreur', 'Ajoutez des images au produit')
    return
  }

  isAnalyzingImages.value = true

  try {
    const response = await post<VisionAnalysisResponse>(
      `/products/${props.productId}/analyze-images`
    )

    if (response?.attributes) {
      const attrs = response.attributes
      let fieldsUpdated = 0

      // Mapper les champs de l'API vers le formulaire
      const fieldMappings: Array<[keyof typeof attrs, keyof ProductFormData]> = [
        ['title', 'title'],
        ['description', 'description'],
        ['price', 'price'],
        ['category', 'category'],
        ['brand', 'brand'],
        ['condition', 'condition'],
        ['color', 'color'],
        ['material', 'material'],
        ['gender', 'gender'],
        ['season', 'season'],
        ['fit', 'fit'],
        ['pattern', 'pattern'],
        ['neckline', 'neckline'],
        ['sport', 'sport'],
        ['unique_feature', 'unique_feature'],
        ['marking', 'marking']
      ]

      for (const [apiField, formField] of fieldMappings) {
        const value = attrs[apiField]
        if (value !== null && value !== undefined) {
          updateField(formField, value as any)
          fieldsUpdated++
        }
      }

      // Gérer size_original (peut venir de 'size' ou 'label_size' de l'API)
      const sizeValue = (attrs as any).size || (attrs as any).label_size || (attrs as any).size_original
      if (sizeValue) {
        updateField('size_original', sizeValue)
        fieldsUpdated++
      }

      const confidence = attrs.confidence ? Math.round(attrs.confidence * 100) : 0
      showSuccess(
        'Formulaire rempli',
        `${response.images_analyzed} image(s) analysée(s), ${fieldsUpdated} champ(s) rempli(s) (confiance: ${confidence}%)`
      )
    }
  } catch (error: any) {
    const message = error?.data?.detail || error?.message || 'Erreur lors de l\'analyse'

    if (message.includes('Crédits IA insuffisants') || error?.status === 402) {
      showError('Crédits insuffisants', 'Vous n\'avez plus de crédits IA.')
    } else if (message.includes('pas d\'images')) {
      showError('Pas d\'images', 'Ajoutez des images au produit.')
    } else {
      showError('Erreur', message)
    }
  } finally {
    isAnalyzingImages.value = false
  }
}
</script>

<template>
  <div class="pb-24">
    <div class="p-6">
      <!-- Page Header -->
      <div class="mb-3">
        <h1 class="text-2xl font-bold text-secondary-900">Créer un produit</h1>
      </div>

      <!-- Photo Section Title -->
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-base font-bold text-secondary-900 flex items-center gap-2">
          <i class="pi pi-images"/>
          Photos du produit * <span class="font-normal text-sm text-gray-500">(min. 1)</span>
          <span class="text-sm font-normal text-gray-400">{{ photos.length }}/20</span>
        </h3>

        <Button
          v-if="photos.length > 0"
          label="Ajouter"
          icon="pi pi-plus"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          size="small"
          :disabled="photos.length >= 20"
          @click="openPhotoSelector"
        />
      </div>

      <!-- Photos Section -->
      <div class="mb-4">
        <ProductsPhotoUploader ref="photoUploader" v-model:photos="photos" />
      </div>

      <!-- AI Auto-fill Section (visible when photos exist) -->
      <div
        v-if="photos.length > 0"
        class="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-lg p-4 mb-4"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="bg-primary-100 rounded-full p-2">
              <i class="pi pi-sparkles text-primary-600 text-lg" />
            </div>
            <div>
              <h4 class="text-sm font-semibold text-primary-900">Remplissage automatique</h4>
              <p class="text-xs text-primary-700">L'IA analyse vos photos et remplit le formulaire</p>
            </div>
          </div>
          <Button
            type="button"
            label="Remplir avec l'IA"
            icon="pi pi-sparkles"
            class="bg-primary-500 hover:bg-primary-600 text-white border-0 font-semibold"
            :loading="isAnalyzingImages"
            :disabled="isAnalyzingImages"
            @click="analyzeImagesAndFill"
          />
        </div>
      </div>

      <!-- Form Section -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <ProductsProductForm
          :model-value="form"
          :is-submitting="isSubmitting"
          @update:model-value="handleFormUpdate"
          @submit="handleSubmit"
        />
      </div>
    </div>

    <!-- Sticky Footer -->
    <div class="fixed bottom-0 left-0 right-0 md:left-64 bg-white/95 backdrop-blur-sm border-t border-gray-200 p-4 z-40 shadow-lg">
      <div class="flex items-center justify-between max-w-4xl mx-auto">
        <div class="flex items-center gap-4">
          <!-- Progress indicator -->
          <div class="flex items-center gap-2 text-sm">
            <i class="pi pi-check-circle" :class="formProgress >= 100 ? 'text-green-500' : 'text-gray-400'" />
            <span class="text-gray-500">{{ filledRequiredCount }}/{{ totalRequiredCount }}</span>
            <!-- Show missing fields -->
            <span v-if="missingFields.length > 0 || photos.length === 0" class="text-orange-500 flex items-center gap-1">
              <i class="pi pi-exclamation-triangle text-xs" />
              <span class="text-xs">
                Manque :
                <span
                  v-if="missingFields.length > 0"
                  v-tooltip.top="missingFields.length > 3 ? missingFields.join(', ') : undefined"
                  :class="{ 'cursor-help': missingFields.length > 3 }"
                >
                  {{ missingFields.slice(0, 3).join(', ') }}
                  <span v-if="missingFields.length > 3" class="underline decoration-dotted">+{{ missingFields.length - 3 }}</span>
                </span>
                <template v-if="missingFields.length > 0 && photos.length === 0">, </template>
                <template v-if="photos.length === 0">Photo</template>
              </span>
            </span>
            <!-- All complete -->
            <span v-else class="text-green-500 flex items-center gap-1 text-xs">
              <i class="pi pi-check text-xs" />
              Complet
            </span>
          </div>
          <!-- Draft saved indicator -->
          <div v-if="hasDraft && lastSaved" class="flex items-center gap-2 text-xs text-gray-400">
            <i class="pi pi-save" />
            <span>Brouillon {{ formatLastSaved() }}</span>
            <button
              class="text-red-400 hover:text-red-500 underline transition-colors"
              title="Effacer le brouillon"
              @click="handleClearDraft"
            >
              Effacer
            </button>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <Button
            type="button"
            label="Annuler"
            icon="pi pi-times"
            class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
            @click="$router.push('/dashboard/products')"
          />
          <Button
            type="button"
            label="Créer le produit"
            icon="pi pi-check"
            class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold"
            :loading="isSubmitting"
            :disabled="!canSubmit"
            @click="handleSubmit"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useProductsStore } from '~/stores/products'
import { useProductDraft } from '~/composables/useProductDraft'
import { type ProductFormData, defaultProductFormData } from '~/types/product'
import { productLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()
const productsStore = useProductsStore()
const { showSuccess, showError, showWarn, showInfo } = useAppToast()

// Auto-save draft functionality
const { saveDraft, debouncedSave, loadDraft, clearDraft, hasDraft, lastSaved, formatLastSaved } = useProductDraft()

// Form data with complete ProductFormData interface
const form = ref<ProductFormData>({ ...defaultProductFormData })

// Photos management
interface Photo {
  file: File
  preview: string
}

const photos = ref<Photo[]>([])
const isSubmitting = ref(false)
const isAnalyzingImages = ref(false)

// API composable
const { post } = useApi()

// Required fields for progress calculation
const requiredFields = ['title', 'description', 'category', 'brand', 'condition', 'size_original', 'color', 'gender', 'material'] as const
const totalRequiredCount = requiredFields.length

// Human-readable field names
const fieldLabels: Record<string, string> = {
  title: 'Titre',
  description: 'Description',
  category: 'Catégorie',
  brand: 'Marque',
  condition: 'État',
  size_original: 'Taille',
  color: 'Couleur',
  gender: 'Genre',
  material: 'Matière'
}

// Calculate filled required fields
const filledRequiredCount = computed(() => {
  return requiredFields.filter(field => {
    const value = form.value[field]
    return value !== null && value !== undefined && value !== ''
  }).length
})

// Get missing required fields (human-readable)
const missingFields = computed(() => {
  return requiredFields.filter(field => {
    const value = form.value[field]
    return value === null || value === undefined || value === ''
  }).map(field => fieldLabels[field] || field)
})

// Calculate form progress percentage (including photos)
const formProgress = computed(() => {
  const fieldsProgress = (filledRequiredCount.value / totalRequiredCount) * 90 // 90% for fields
  const photosProgress = photos.value.length > 0 ? 10 : 0 // 10% for photos
  return Math.round(fieldsProgress + photosProgress)
})

// Can submit: all required fields filled + at least 1 photo
const canSubmit = computed(() => {
  return filledRequiredCount.value === totalRequiredCount && photos.value.length > 0
})

// Reference to PhotoUploader component
const photoUploader = ref<{ openFileSelector: () => void } | null>(null)

// Method to open photo selector
const openPhotoSelector = () => {
  if (photoUploader.value) {
    photoUploader.value.openFileSelector()
  }
}

// ====== AI IMAGE ANALYSIS ======

/**
 * Analyse les images uploadées avec l'IA et remplit le formulaire
 */
const analyzeImagesAndFill = async () => {
  if (photos.value.length === 0) {
    showWarn('Pas de photos', 'Ajoutez au moins une photo pour utiliser l\'IA', 3000)
    return
  }

  isAnalyzingImages.value = true

  try {
    // Créer FormData avec les fichiers
    const formData = new FormData()
    for (const photo of photos.value) {
      formData.append('files', photo.file)
    }

    // Appeler l'endpoint d'analyse directe
    const response = await post<{
      attributes: {
        title?: string | null
        description?: string | null
        price?: number | null
        category?: string | null
        brand?: string | null
        condition?: number | null
        size?: string | null
        label_size?: string | null
        color?: string | null
        material?: string | null
        fit?: string | null
        gender?: string | null
        season?: string | null
        sport?: string | null
        neckline?: string | null
        length?: string | null
        pattern?: string | null
        rise?: string | null
        closure?: string | null
        sleeve_length?: string | null
        origin?: string | null
        decade?: string | null
        trend?: string | null
        model?: string | null
        unique_feature?: string | null
        marking?: string | null
        condition_sup?: string | null
        confidence?: number
      }
      images_analyzed: number
      tokens_used: number
    }>('/products/analyze-images-direct', formData)

    if (response?.attributes) {
      fillFormWithAIResults(response.attributes)
      showSuccess(
        'Analyse terminée',
        `${response.images_analyzed} image(s) analysée(s). Formulaire pré-rempli avec confiance ${Math.round((response.attributes.confidence || 0) * 100)}%`,
        4000
      )
    }
  } catch (error: any) {
    productLogger.error('AI analysis error', { error: error.message })

    // Gérer les erreurs spécifiques
    if (error?.statusCode === 402) {
      showError(
        'Crédits insuffisants',
        'Vous n\'avez plus de crédits IA. Passez à un abonnement supérieur.',
        5000
      )
    } else {
      showError(
        'Erreur d\'analyse',
        error.message || 'Impossible d\'analyser les images. Réessayez plus tard.',
        5000
      )
    }
  } finally {
    isAnalyzingImages.value = false
  }
}

/**
 * Remplit le formulaire avec les résultats de l'IA
 */
const fillFormWithAIResults = (attrs: Record<string, any>) => {
  // Mappings: attribut API -> champ formulaire
  const mappings: [string, keyof ProductFormData][] = [
    ['title', 'title'],
    ['description', 'description'],
    ['price', 'price'],
    ['category', 'category'],
    ['brand', 'brand'],
    ['condition', 'condition'],
    ['color', 'color'],
    ['material', 'material'],
    ['fit', 'fit'],
    ['gender', 'gender'],
    ['season', 'season'],
    ['sport', 'sport'],
    ['neckline', 'neckline'],
    ['length', 'length'],
    ['pattern', 'pattern'],
    ['rise', 'rise'],
    ['closure', 'closure'],
    ['sleeve_length', 'sleeve_length'],
    ['origin', 'origin'],
    ['decade', 'decade'],
    ['trend', 'trend'],
    ['model', 'model'],
  ]

  let fieldsUpdated = 0

  for (const [apiField, formField] of mappings) {
    if (attrs[apiField] !== null && attrs[apiField] !== undefined) {
      // @ts-expect-error - Dynamic key access
      form.value[formField] = attrs[apiField]
      fieldsUpdated++
    }
  }

  // Gérer size_original (peut venir de 'size' ou 'label_size')
  if (attrs.size || attrs.label_size) {
    form.value.size_original = attrs.size || attrs.label_size
    fieldsUpdated++
  }

  // Gérer les arrays: condition_sup, unique_feature, marking
  if (attrs.condition_sup) {
    const items = attrs.condition_sup.split(',').map((s: string) => s.trim()).filter(Boolean)
    if (items.length > 0) {
      form.value.condition_sup = items
      fieldsUpdated++
    }
  }

  if (attrs.unique_feature) {
    const items = attrs.unique_feature.split(',').map((s: string) => s.trim()).filter(Boolean)
    if (items.length > 0) {
      form.value.unique_feature = items
      fieldsUpdated++
    }
  }

  if (attrs.marking) {
    form.value.marking = attrs.marking
    fieldsUpdated++
  }

  productLogger.debug(`Filled ${fieldsUpdated} fields from AI analysis`)
}

// Handle form updates from ProductForm
const handleFormUpdate = (newForm: ProductFormData) => {
  form.value = newForm
}

const handleSubmit = async () => {
  // Validation: Vérifier qu'au moins 1 photo est ajoutée
  if (photos.value.length === 0) {
    showWarn(
      'Photo manquante',
      'Veuillez ajouter au moins 1 photo pour le produit',
      3000
    )
    return
  }

  isSubmitting.value = true

  try {
    // Préparer les données pour l'API (mapper size_original vers le format attendu par le backend)
    const productData = {
      title: form.value.title,
      description: form.value.description,
      price: form.value.price,
      category: form.value.category,
      condition: form.value.condition,
      brand: form.value.brand || null,
      size_original: form.value.size_original || null,
      size_normalized: form.value.size_normalized || null,
      color: form.value.color || null,
      material: form.value.material || null,
      fit: form.value.fit || null,
      gender: form.value.gender || null,
      season: form.value.season || null,
      sport: form.value.sport || null,
      neckline: form.value.neckline || null,
      length: form.value.length || null,
      pattern: form.value.pattern || null,
      rise: form.value.rise || null,
      closure: form.value.closure || null,
      sleeve_length: form.value.sleeve_length || null,
      origin: form.value.origin || null,
      decade: form.value.decade || null,
      trend: form.value.trend || null,
      condition_sup: form.value.condition_sup || null,
      location: form.value.location || null,
      model: form.value.model || null,
      unique_feature: form.value.unique_feature || null,
      marking: form.value.marking || null,
      dim1: form.value.dim1 || null,
      dim2: form.value.dim2 || null,
      dim3: form.value.dim3 || null,
      dim4: form.value.dim4 || null,
      dim5: form.value.dim5 || null,
      dim6: form.value.dim6 || null,
      pricing_rarity: form.value.pricing_rarity || null,
      pricing_quality: form.value.pricing_quality || null,
      pricing_style: form.value.pricing_style || null,
      pricing_details: form.value.pricing_details || null,
      pricing_edit: form.value.pricing_edit || null,
      stock_quantity: form.value.stock_quantity
    }

    // Créer le produit via API
    const newProduct = await productsStore.createProduct(productData)

    // Upload images si le produit est créé avec succès
    if (newProduct && photos.value.length > 0 && newProduct.id) {
      try {
        for (let i = 0; i < photos.value.length; i++) {
          const photo = photos.value[i]
          if (photo) {
            await productsStore.uploadProductImage(newProduct.id, photo.file, i)
          }
        }

        showSuccess(
          'Produit créé',
          `${form.value.title} a été créé avec ${photos.value.length} image(s)`,
          3000
        )
      } catch (imageError: any) {
        showWarn(
          'Produit créé',
          `${form.value.title} créé, mais erreur upload images: ${imageError.message}`,
          5000
        )
      }
    } else if (newProduct) {
      showSuccess(
        'Produit créé',
        `${form.value.title} a été créé avec succès`,
        3000
      )
    }

    // Clear draft on success
    clearDraft()

    // Redirect to products list
    router.push('/dashboard/products')
  } catch (error: any) {
    productLogger.error('Error creating product', { error: error.message })
    showError(
      'Erreur',
      error.message || 'Impossible de créer le produit',
      5000
    )
  } finally {
    isSubmitting.value = false
  }
}

// ====== AUTO-SAVE DRAFT ======

// Handle clear draft button
const handleClearDraft = () => {
  clearDraft()
  form.value = { ...defaultProductFormData }
  photos.value = []
  showInfo('Brouillon effacé', 'Le formulaire a été réinitialisé', 2000)
}

// Watch form changes and auto-save (debounced 2s)
watch(form, () => {
  debouncedSave(form.value, photos.value)
}, { deep: true })

// Also save when photos change
watch(photos, () => {
  debouncedSave(form.value, photos.value)
}, { deep: true })

// Restore draft on mount
onMounted(() => {
  const draft = loadDraft()
  if (draft) {
    // Restore form data
    form.value = { ...defaultProductFormData, ...draft.formData }
    showInfo(
      'Brouillon restauré',
      `Votre travail précédent a été récupéré${draft.photoCount > 0 ? ' (les photos devront être ré-uploadées)' : ''}`,
      4000
    )
  }
})

// Cleanup on unmount
onUnmounted(() => {
  photos.value.forEach(photo => {
    URL.revokeObjectURL(photo.preview)
  })
})
</script>

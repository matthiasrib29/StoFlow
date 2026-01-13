<template>
  <div class="p-6">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <ProgressSpinner />
    </div>

    <!-- Product not found -->
    <div v-else-if="!product" class="text-center py-20">
      <i class="pi pi-exclamation-circle text-gray-300 text-6xl mb-4"/>
      <h2 class="text-2xl font-bold text-secondary-900 mb-2">Produit introuvable</h2>
      <p class="text-gray-600 mb-6">Ce produit n'existe pas ou a été supprimé</p>
      <Button
        label="Retour aux produits"
        icon="pi pi-arrow-left"
        class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
        @click="$router.push('/dashboard/products')"
      />
    </div>

    <!-- Edit Form -->
    <div v-else>
      <PageHeader
        title="Modifier le produit"
        :subtitle="product.title"
      >
        <template #actions>
          <Button
            label="Retour"
            icon="pi pi-arrow-left"
            class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
            @click="$router.push('/dashboard/products')"
          />
        </template>
      </PageHeader>

      <!-- Photo Section Title -->
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-base font-bold text-secondary-900 flex items-center gap-2">
          <i class="pi pi-images"/>
          Photos du produit
          <span class="text-sm font-normal text-gray-400">{{ existingImages.length + newPhotos.length }}/20</span>
        </h3>

        <Button
          v-if="existingImages.length > 0 || newPhotos.length > 0"
          label="Ajouter"
          icon="pi pi-plus"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          size="small"
          :disabled="existingImages.length + newPhotos.length >= 20"
          @click="openPhotoSelector"
        />
      </div>

      <!-- Photos Section -->
      <div class="mb-4">
        <ProductsPhotoUploader
          ref="photoUploader"
          v-model:photos="newPhotos"
          v-model:existing-images="existingImages"
          @remove-existing="removeExistingImage"
          @reorder="handleReorder"
        />
      </div>

      <!-- AI Auto-fill Section (visible when photos exist) -->
      <ProductsAiAutoFillSection
        v-if="existingImages.length > 0 || newPhotos.length > 0"
        :ai-credits-remaining="aiCreditsRemaining"
        :loading="isAnalyzingImages"
        @analyze="analyzeImagesAndFill"
      />

      <!-- Form Section -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <ProductsProductForm
          v-model="form"
          :is-submitting="isSubmitting"
          :product-id="id"
          submit-label="Enregistrer les modifications"
          @submit="handleSubmit"
          @cancel="$router.push('/dashboard/products')"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useProductsStore, type Product } from '~/stores/products'
import { type ProductFormData, defaultProductFormData } from '~/types/product'
import { productLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

const route = useRoute()
const router = useRouter()
const { showSuccess, showError, showWarn, showInfo } = useAppToast()
const productsStore = useProductsStore()
const { post } = useApi()

const id = parseInt(route.params.id as string)

// State
const loading = ref(true)
const product = ref<Product | null>(null)
const isSubmitting = ref(false)
const isAnalyzingImages = ref(false)

// AI Credits
const { aiCreditsRemaining, fetchAICredits } = useAiCredits()

// Form data with complete ProductFormData interface
const form = ref<ProductFormData>({ ...defaultProductFormData })

// Photos management
interface Photo {
  file: File
  preview: string
}

interface ExistingImage {
  id: number
  url: string
  position: number
}

const newPhotos = ref<Photo[]>([])
const existingImages = ref<ExistingImage[]>([])
const imagesToDelete = ref<number[]>([])

// Reference to PhotoUploader component
const photoUploader = ref<{ openFileSelector: () => void } | null>(null)

// Method to open photo selector
const openPhotoSelector = () => {
  if (photoUploader.value) {
    photoUploader.value.openFileSelector()
  }
}

// Remove existing image
const removeExistingImage = (imageId: number) => {
  existingImages.value = existingImages.value.filter(img => img.id !== imageId)
  imagesToDelete.value.push(imageId)
}

// Track if images were reordered
const imagesReordered = ref(false)

// Handle reorder event from PhotoUploader
const handleReorder = (_order: { existingImages: ExistingImage[], photos: Photo[] }) => {
  imagesReordered.value = true
}

// ====== AI IMAGE ANALYSIS ======

/**
 * Analyse les images avec l'IA et remplit le formulaire
 */
const analyzeImagesAndFill = async () => {
  // Vérifier qu'il y a des images
  if (existingImages.value.length === 0 && newPhotos.value.length === 0) {
    showWarn('Pas de photos', 'Ajoutez au moins une photo pour utiliser l\'IA', 3000)
    return
  }

  isAnalyzingImages.value = true

  try {
    // Créer FormData avec les fichiers
    const formData = new FormData()

    // Pour les images existantes, on utilise l'endpoint avec product_id
    // Pour les nouvelles photos, on les envoie directement
    if (newPhotos.value.length > 0) {
      // Analyser les nouvelles photos
      for (const photo of newPhotos.value) {
        formData.append('files', photo.file)
      }
    } else if (existingImages.value.length > 0 && product.value) {
      // Utiliser l'endpoint qui analyse les images existantes du produit
      const response = await post<{
        attributes: Record<string, any>
        images_analyzed: number
        tokens_used: number
      }>(`/products/${product.value.id}/analyze-images`)

      if (response?.attributes) {
        fillFormWithAIResults(response.attributes)
        showSuccess(
          'Analyse terminée',
          `${response.images_analyzed} image(s) analysée(s). Formulaire pré-rempli.`,
          4000
        )
      }
      return
    }

    // Appeler l'endpoint d'analyse directe pour les nouvelles photos
    const response = await post<{
      attributes: Record<string, any>
      images_analyzed: number
      tokens_used: number
    }>('/products/analyze-images-direct', formData)

    if (response?.attributes) {
      fillFormWithAIResults(response.attributes)
      showSuccess(
        'Analyse terminée',
        `${response.images_analyzed} image(s) analysée(s). Formulaire pré-rempli.`,
        4000
      )
    }
  } catch (error: any) {
    productLogger.error('AI analysis error', { error: error.message })

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
    await fetchAICredits()
  }
}

/**
 * Remplit le formulaire avec les résultats de l'IA
 */
const fillFormWithAIResults = (attrs: Record<string, any>) => {
  const mappings: [string, keyof ProductFormData][] = [
    ['category', 'category'],
    ['brand', 'brand'],
    ['condition', 'condition'],
    ['label_size', 'size_original'],
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
    ['stretch', 'stretch'],
    ['lining', 'lining'],
    ['origin', 'origin'],
    ['decade', 'decade'],
    ['trend', 'trend'],
    ['model', 'model']
  ]

  for (const [aiKey, formKey] of mappings) {
    const value = attrs[aiKey]
    if (value !== null && value !== undefined) {
      (form.value as any)[formKey] = value
    }
  }

  // Handle array fields (backend already converts to arrays)
  const arrayFields = ['condition_sup', 'unique_feature', 'marking'] as const
  for (const field of arrayFields) {
    if (attrs[field] && Array.isArray(attrs[field]) && attrs[field].length > 0) {
      (form.value as any)[field] = attrs[field]
    }
  }

  // Handle color (backend returns array, form expects first value as string)
  if (attrs.color && Array.isArray(attrs.color) && attrs.color.length > 0) {
    form.value.color = attrs.color[0]
  }

  // Handle material (backend returns array, form expects first value as string)
  if (attrs.material && Array.isArray(attrs.material) && attrs.material.length > 0) {
    form.value.material = attrs.material[0]
  }

  productLogger.info('Form filled with AI results', { attrs })
}

// Fetch product on mount
onMounted(async () => {
  // Fetch AI credits for display
  await fetchAICredits()

  try {
    loading.value = true

    // Charger le produit depuis l'API
    product.value = await productsStore.fetchProduct(id)

    if (product.value) {
      // Pré-remplir le formulaire avec les données existantes
      form.value = {
        // Section 1: Infos de base
        title: product.value.title || '',
        description: product.value.description || '',
        price: product.value.price !== null ? parseFloat(product.value.price) : null,
        stock_quantity: product.value.stock_quantity || 1,

        // Section 2: Caractéristiques obligatoires
        category: product.value.category || '',
        brand: product.value.brand || '',
        condition: product.value.condition ?? null,
        size_original: product.value.size_original || '',
        size_normalized: product.value.size_normalized || null,
        color: product.value.color || '',
        gender: product.value.gender || '',
        material: product.value.material || '',

        // Section 2: Caractéristiques optionnelles - Vêtements
        fit: product.value.fit || null,
        season: product.value.season || null,
        sport: product.value.sport || null,
        neckline: product.value.neckline || null,
        length: product.value.length || null,
        pattern: product.value.pattern || null,
        rise: product.value.rise || null,
        closure: product.value.closure || null,
        sleeve_length: product.value.sleeve_length || null,
        stretch: product.value.stretch || null,
        lining: product.value.lining || null,

        // Section 2: Vintage & Tendance
        origin: product.value.origin || null,
        decade: product.value.decade || null,
        trend: product.value.trend || null,

        // Section 2: Détails
        condition_sup: product.value.condition_sup || null,
        location: product.value.location || null,
        model: product.value.model || null,
        unique_feature: product.value.unique_feature || null,
        marking: product.value.marking || null,

        // Section 3: Dimensions
        dim1: product.value.dim1 || null,
        dim2: product.value.dim2 || null,
        dim3: product.value.dim3 || null,
        dim4: product.value.dim4 || null,
        dim5: product.value.dim5 || null,
        dim6: product.value.dim6 || null,

        // Section 3: Pricing
        pricing_rarity: product.value.pricing_rarity || null,
        pricing_quality: product.value.pricing_quality || null,
        pricing_style: product.value.pricing_style || null,
        pricing_details: product.value.pricing_details || null,
        pricing_edit: product.value.pricing_edit || null
      }

      // Charger les images existantes (JSONB: {url, order, created_at})
      if (product.value.images && product.value.images.length > 0) {
        existingImages.value = product.value.images
          .sort((a: any, b: any) => a.order - b.order)
          .map((img: any, index: number) => ({
            id: index,
            url: img.url,
            position: img.order
          }))
      }
    }
  } catch (error) {
    productLogger.error('Erreur chargement produit', { error })
    showError('Erreur', 'Impossible de charger le produit', 5000)
  } finally {
    loading.value = false
  }
})

const handleSubmit = async () => {
  // Validation: Vérifier que le produit existe
  if (!product.value) {
    showError('Erreur', 'Produit introuvable', 3000)
    return
  }

  // Validation: Vérifier qu'au moins 1 image existe
  if (existingImages.value.length === 0 && newPhotos.value.length === 0) {
    showWarn(
      'Photo manquante',
      'Veuillez conserver ou ajouter au moins 1 photo pour le produit',
      3000
    )
    return
  }

  isSubmitting.value = true

  try {
    // Préparer les données pour l'API
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
      stretch: form.value.stretch || null,
      lining: form.value.lining || null,
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

    // Mettre à jour le produit via API
    await productsStore.updateProduct(product.value.id, productData)

    // Supprimer les images marquées pour suppression
    for (const imageId of imagesToDelete.value) {
      try {
        await productsStore.deleteProductImage(product.value.id, imageId)
      } catch (e) {
        productLogger.error('Error deleting image', { error: e })
      }
    }

    // Réorganiser les images existantes si l'ordre a changé
    if (imagesReordered.value && existingImages.value.length > 0) {
      try {
        const imageOrder: Record<number, number> = {}
        existingImages.value.forEach((img, index) => {
          imageOrder[img.id] = index
        })
        await productsStore.reorderProductImages(product.value.id, imageOrder)
      } catch (e) {
        productLogger.error('Error reordering images', { error: e })
      }
    }

    // Upload nouvelles photos
    if (newPhotos.value.length > 0) {
      const startPosition = existingImages.value.length
      for (let i = 0; i < newPhotos.value.length; i++) {
        const photo = newPhotos.value[i]
        if (photo) {
          await productsStore.uploadProductImage(product.value.id, photo.file, startPosition + i)
        }
      }
    }

    showSuccess(
      'Produit modifié',
      `${form.value.title} a été mis à jour avec succès`,
      3000
    )

    router.push('/dashboard/products')
  } catch (error: any) {
    productLogger.error('Error updating product', { error: error.message })
    showError('Erreur', error.message || 'Impossible de modifier le produit', 5000)
  } finally {
    isSubmitting.value = false
  }
}

// Cleanup on unmount
onUnmounted(() => {
  newPhotos.value.forEach(photo => {
    URL.revokeObjectURL(photo.preview)
  })
})
</script>

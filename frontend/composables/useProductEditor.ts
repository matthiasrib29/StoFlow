/**
 * Product Editor Orchestrator Composable
 *
 * Main composable that orchestrates all product editing functionality.
 * Composes useProductImages, useProductAIAnalysis, usePricingCalculation,
 * and useProductDraft to provide a unified interface for create/edit pages.
 *
 * Created: 2026-01-13
 * Phase: Product Editor Unification
 */

import { useProductsStore, type Product } from '~/stores/products'
import { useProductImages, type UnifiedImage } from '~/composables/useProductImages'
import { useProductAIAnalysis } from '~/composables/useProductAIAnalysis'
import { usePricingCalculation, type PriceInput } from '~/composables/usePricingCalculation'
import { useProductDraft } from '~/composables/useProductDraft'
import { type ProductFormData, defaultProductFormData } from '~/types/product'
import { productLogger } from '~/utils/logger'

export type EditorMode = 'create' | 'edit'

export interface UseProductEditorOptions {
  mode: EditorMode
  productId?: number
}

// Required fields for validation
const REQUIRED_FIELDS = [
  'title',
  'description',
  'category',
  'brand',
  'condition',
  'size_original',
  'color',
  'gender',
  'material'
] as const

// Human-readable field names
const FIELD_LABELS: Record<string, string> = {
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

/**
 * Product Editor Orchestrator
 *
 * @example
 * ```typescript
 * // Create mode
 * const editor = useProductEditor({ mode: 'create' })
 *
 * // Edit mode
 * const editor = useProductEditor({ mode: 'edit', productId: 123 })
 * await editor.loadProduct()
 *
 * // Use in template
 * <ProductsPhotoUploader v-model:photos="editor.images.photos" />
 * <ProductsProductForm v-model="editor.form" />
 * ```
 */
export function useProductEditor(options: UseProductEditorOptions) {
  const { mode, productId } = options

  const router = useRouter()
  const productsStore = useProductsStore()
  const { showSuccess, showError, showWarn, showInfo } = useAppToast()

  // Compose sub-composables
  const images = useProductImages({ maxPhotos: 20 })
  const ai = useProductAIAnalysis()
  const pricing = usePricingCalculation()

  // Draft management (only in create mode)
  const draft = mode === 'create' ? useProductDraft() : null

  // AI Credits
  const { aiCreditsRemaining, fetchAICredits } = useAiCredits()

  // Core state
  const form = ref<ProductFormData>({ ...defaultProductFormData })
  const product = ref<Product | null>(null)
  const isLoading = ref(false)
  const isSubmitting = ref(false)
  const isPublishing = ref(false)

  // Scroll state for sticky photos
  const isScrolled = ref(false)

  // ============ COMPUTED ============

  const filledRequiredCount = computed(() => {
    return REQUIRED_FIELDS.filter(field => {
      const value = form.value[field]
      return value !== null && value !== undefined && value !== ''
    }).length
  })

  const totalRequiredCount = REQUIRED_FIELDS.length

  const missingFields = computed(() => {
    return REQUIRED_FIELDS.filter(field => {
      const value = form.value[field]
      return value === null || value === undefined || value === ''
    }).map(field => FIELD_LABELS[field] || field)
  })

  const formProgress = computed(() => {
    const fieldsProgress = (filledRequiredCount.value / totalRequiredCount) * 90
    const photosProgress = images.hasImages.value ? 10 : 0
    return Math.round(fieldsProgress + photosProgress)
  })

  // Can publish: all required fields filled + at least one image
  const canPublish = computed(() => {
    return filledRequiredCount.value === totalRequiredCount && images.hasImages.value
  })

  // Can save as draft: at least one image OR some content in the form
  const canSaveDraft = computed(() => {
    const hasAnyContent = form.value.title || form.value.description || form.value.brand || form.value.category
    return images.hasImages.value || hasAnyContent
  })

  // Alias for backwards compatibility
  const canSubmit = canPublish

  // Form sections for progress bar
  const formSections = computed(() => {
    const infoFields = ['title', 'description', 'price'] as const
    const charFields = ['category', 'brand', 'condition', 'size_original', 'color', 'gender', 'material'] as const
    const measuresFields = ['dim1', 'dim2', 'dim3'] as const

    return [
      {
        id: 'info',
        label: 'Infos',
        filled: infoFields.filter(f => form.value[f]).length,
        total: 3,
        isComplete: ['title', 'description'].every(f => form.value[f as keyof ProductFormData])
      },
      {
        id: 'characteristics',
        label: 'Caractéristiques',
        filled: charFields.filter(f => {
          const val = form.value[f]
          return val !== null && val !== undefined && val !== ''
        }).length,
        total: charFields.length,
        isComplete: charFields.every(f => {
          const val = form.value[f]
          return val !== null && val !== undefined && val !== ''
        })
      },
      {
        id: 'measures',
        label: 'Mesures',
        filled: measuresFields.filter(f => form.value[f]).length,
        total: 3,
        isComplete: false
      }
    ]
  })

  // ============ METHODS ============

  /**
   * Load product data (edit mode only)
   */
  const loadProduct = async (): Promise<Product | null> => {
    if (mode !== 'edit' || !productId) {
      productLogger.warn('loadProduct called in create mode or without productId')
      return null
    }

    isLoading.value = true

    try {
      product.value = await productsStore.fetchProduct(productId)

      if (product.value) {
        // Fill form with product data
        fillFormFromProduct(product.value)

        // Initialize images from product
        images.initFromExisting(product.value.images)
      }

      return product.value
    } catch (error: any) {
      productLogger.error('Error loading product', { error: error.message })
      showError('Erreur', 'Impossible de charger le produit', 5000)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fill form from product data
   */
  const fillFormFromProduct = (prod: Product) => {
    form.value = {
      title: prod.title || '',
      description: prod.description || '',
      price: prod.price !== null ? Number(prod.price) : null,
      stock_quantity: prod.stock_quantity || 1,

      category: prod.category || '',
      brand: prod.brand || '',
      condition: prod.condition ?? null,
      size_original: prod.size_original || '',
      size_normalized: prod.size_normalized || null,
      color: prod.color || '',
      gender: prod.gender || '',
      material: prod.material || '',

      fit: prod.fit || null,
      season: prod.season || null,
      sport: prod.sport || null,
      neckline: prod.neckline || null,
      length: prod.length || null,
      pattern: prod.pattern || null,
      rise: prod.rise || null,
      closure: prod.closure || null,
      sleeve_length: prod.sleeve_length || null,
      stretch: prod.stretch || null,
      lining: prod.lining || null,

      origin: prod.origin || null,
      decade: prod.decade || null,
      trend: prod.trend || null,

      condition_sup: prod.condition_sup || null,
      location: prod.location || null,
      model: prod.model || null,
      unique_feature: prod.unique_feature || null,
      marking: prod.marking || null,

      dim1: prod.dim1 || null,
      dim2: prod.dim2 || null,
      dim3: prod.dim3 || null,
      dim4: prod.dim4 || null,
      dim5: prod.dim5 || null,
      dim6: prod.dim6 || null,

      pricing_rarity: prod.pricing_rarity || null,
      pricing_quality: prod.pricing_quality || null,
      pricing_style: prod.pricing_style || null,
      pricing_details: prod.pricing_details || null,
      pricing_edit: prod.pricing_edit || null
    }
  }

  /**
   * Handle form update from ProductForm component
   */
  const handleFormUpdate = (newForm: ProductFormData) => {
    form.value = newForm
  }

  /**
   * Analyze images with AI and fill form
   */
  const analyzeWithAI = async () => {
    const { files, hasExistingOnly } = images.getFilesForAnalysis()

    try {
      const result = await ai.analyze(files, productId, hasExistingOnly)

      if (result?.attributes) {
        ai.fillFormWithResults(result.attributes, form)
        ai.showAnalysisSuccess(result.images_analyzed, result.attributes.confidence)

        // Auto-calculate price after AI fill (create mode)
        if (mode === 'create') {
          await calculatePrice()
        }
      }
    } finally {
      // Refresh AI credits
      await fetchAICredits()
    }
  }

  /**
   * Calculate suggested price
   */
  const calculatePrice = async () => {
    if (!form.value.brand || !form.value.category) {
      productLogger.debug('Missing required fields for pricing: brand or category')
      return
    }

    try {
      const priceInput: PriceInput = {
        brand: form.value.brand,
        category: form.value.category,
        materials: form.value.material ? [form.value.material] : [],
        model_name: form.value.model || undefined,
        condition_score: form.value.condition || 5,
        supplements: form.value.condition_sup || [],
        condition_sensitivity: 1.0,
        actual_origin: form.value.origin || '',
        expected_origins: ['france', 'italie', 'usa', 'japon'],
        actual_decade: form.value.decade || '',
        expected_decades: ['1990s', '2000s', '2010s'],
        actual_trends: form.value.trend ? [form.value.trend] : [],
        expected_trends: ['vintage', 'streetwear', 'minimalist'],
        actual_features: form.value.unique_feature || [],
        expected_features: ['limited edition', 'collaboration', 'rare color']
      }

      await pricing.calculatePrice(priceInput)
      productLogger.debug('Pricing calculated', { result: pricing.priceResult.value })
    } catch (error: any) {
      productLogger.error('Pricing calculation error', { error: error.message })
    }
  }

  /**
   * Submit the form (create or update product)
   * @param status - 'draft' or 'published' (default: 'published')
   */
  const handleSubmit = async (status: 'draft' | 'published' = 'published'): Promise<Product | null> => {
    // Validation for publish
    if (status === 'published' && !images.hasImages.value) {
      showWarn(
        'Photo manquante',
        mode === 'create'
          ? 'Veuillez ajouter au moins 1 photo pour publier le produit'
          : 'Veuillez conserver ou ajouter au moins 1 photo pour publier le produit',
        3000
      )
      return null
    }

    // Validation for draft - at least need some content
    if (status === 'draft' && !canSaveDraft.value) {
      showWarn(
        'Contenu manquant',
        'Veuillez ajouter au moins une photo ou remplir quelques champs pour sauvegarder un brouillon',
        3000
      )
      return null
    }

    if (mode === 'edit' && !product.value) {
      showError('Erreur', 'Produit introuvable', 3000)
      return null
    }

    isSubmitting.value = true
    isPublishing.value = status === 'published'

    try {
      // Prepare product data with status
      const productData = prepareProductData(status)

      if (mode === 'create') {
        return await createProduct(productData, status)
      } else {
        return await updateProduct(productData, status)
      }
    } catch (error: any) {
      productLogger.error(`Error ${mode === 'create' ? 'creating' : 'updating'} product`, { error: error.message })
      showError('Erreur', error.message || `Impossible de ${mode === 'create' ? 'créer' : 'modifier'} le produit`, 5000)
      return null
    } finally {
      isSubmitting.value = false
      isPublishing.value = false
    }
  }

  /**
   * Save as draft
   */
  const handleSaveDraft = async (): Promise<Product | null> => {
    return handleSubmit('draft')
  }

  /**
   * Publish product
   */
  const handlePublish = async (): Promise<Product | null> => {
    return handleSubmit('published')
  }

  /**
   * Prepare product data for API
   */
  const prepareProductData = (status: 'draft' | 'published' = 'published') => {
    return {
      title: form.value.title,
      description: form.value.description,
      price: form.value.price,
      status,
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
  }

  /**
   * Create new product
   */
  const createProduct = async (productData: ReturnType<typeof prepareProductData>, status: 'draft' | 'published'): Promise<Product | null> => {
    const newProduct = await productsStore.createProduct(productData)

    if (newProduct && newProduct.id) {
      // Upload images
      const imageChanges = images.getChanges()

      const statusLabel = status === 'draft' ? 'en brouillon' : ''
      const titlePrefix = status === 'draft' ? 'Brouillon sauvegardé' : 'Produit créé'

      if (imageChanges.toUpload.length > 0) {
        try {
          for (const img of imageChanges.toUpload) {
            await productsStore.uploadProductImage(newProduct.id, img.file, img.position)
          }

          showSuccess(
            titlePrefix,
            `${form.value.title || 'Produit'} a été ${status === 'draft' ? 'sauvegardé' : 'créé'} avec ${imageChanges.toUpload.length} image(s)`,
            3000
          )
        } catch (imageError: any) {
          showWarn(
            titlePrefix,
            `${form.value.title || 'Produit'} ${status === 'draft' ? 'sauvegardé' : 'créé'}, mais erreur upload images: ${imageError.message}`,
            5000
          )
        }
      } else {
        showSuccess(titlePrefix, `${form.value.title || 'Produit'} a été ${status === 'draft' ? 'sauvegardé en brouillon' : 'créé avec succès'}`, 3000)
      }

      // Clear draft on success
      if (draft) {
        draft.clearDraft()
      }

      return newProduct
    }

    return null
  }

  /**
   * Update existing product
   */
  const updateProduct = async (productData: ReturnType<typeof prepareProductData>, status: 'draft' | 'published'): Promise<Product | null> => {
    if (!product.value) return null

    const prodId = product.value.id
    await productsStore.updateProduct(prodId, productData)

    // Handle image changes
    const imageChanges = images.getChanges()

    // Delete removed images
    for (const imageId of imageChanges.toDelete) {
      try {
        await productsStore.deleteProductImage(prodId, imageId)
      } catch (e) {
        productLogger.error('Error deleting image', { error: e })
      }
    }

    // Reorder existing images
    if (imageChanges.toReorder.length > 0) {
      try {
        const imageOrder: Record<number, number> = {}
        imageChanges.toReorder.forEach(item => {
          imageOrder[item.id] = item.position
        })
        await productsStore.reorderProductImages(prodId, imageOrder)
      } catch (e) {
        productLogger.error('Error reordering images', { error: e })
      }
    }

    // Upload new photos
    if (imageChanges.toUpload.length > 0) {
      for (const img of imageChanges.toUpload) {
        await productsStore.uploadProductImage(prodId, img.file, img.position)
      }
    }

    const titlePrefix = status === 'draft' ? 'Brouillon sauvegardé' : 'Produit modifié'
    showSuccess(titlePrefix, `${form.value.title} a été ${status === 'draft' ? 'sauvegardé en brouillon' : 'mis à jour avec succès'}`, 3000)
    return product.value
  }

  /**
   * Navigate to section (for progress bar)
   */
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(`section-${sectionId}`)
    if (element) {
      const offset = 80
      const elementPosition = element.getBoundingClientRect().top
      const offsetPosition = elementPosition + window.pageYOffset - offset

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      })
    }
  }

  /**
   * Clear draft and reset form (create mode only)
   */
  const clearDraftAndReset = () => {
    if (draft) {
      draft.clearDraft()
    }
    form.value = { ...defaultProductFormData }
    images.reset()
    pricing.reset()
    showInfo('Brouillon effacé', 'Le formulaire a été réinitialisé', 2000)
  }

  /**
   * Initialize (load draft in create mode, fetch AI credits)
   */
  const initialize = async () => {
    await fetchAICredits()

    if (mode === 'create' && draft) {
      const savedDraft = draft.loadDraft()
      if (savedDraft) {
        form.value = { ...defaultProductFormData, ...savedDraft.formData }
        showInfo(
          'Brouillon restauré',
          `Votre travail précédent a été récupéré${savedDraft.photoCount > 0 ? ' (les photos devront être ré-uploadées)' : ''}`,
          4000
        )
      }
    }
  }

  /**
   * Save draft (debounced, create mode only)
   */
  const saveDraft = () => {
    if (draft) {
      draft.debouncedSave(form.value, images.photos.value)
    }
  }

  /**
   * Cleanup on unmount
   */
  const cleanup = () => {
    images.cleanup()
  }

  // Setup scroll detection for sticky photos
  const { y: scrollY } = useScroll(window)
  watch(scrollY, (newY) => {
    isScrolled.value = newY > 100
  })

  // Auto-save draft on form/photos change (create mode only)
  if (mode === 'create') {
    watch(form, saveDraft, { deep: true })
    watch(() => images.photos.value, saveDraft, { deep: true })
  }

  return {
    // Mode
    mode,
    productId,

    // Core state
    form,
    product,
    isLoading,
    isSubmitting,
    isPublishing,
    isScrolled,

    // Sub-composables
    images,
    ai,
    pricing,
    draft,

    // AI Credits
    aiCreditsRemaining,

    // Computed
    filledRequiredCount,
    totalRequiredCount,
    missingFields,
    formProgress,
    canSubmit,
    canPublish,
    canSaveDraft,
    formSections,

    // Methods
    loadProduct,
    handleFormUpdate,
    analyzeWithAI,
    calculatePrice,
    handleSubmit,
    handleSaveDraft,
    handlePublish,
    scrollToSection,
    clearDraftAndReset,
    initialize,
    cleanup
  }
}

/**
 * Composable for AI image analysis
 *
 * Extracts AI analysis logic from create/edit pages for reuse.
 * Handles image analysis requests and form filling with results.
 *
 * Created: 2026-01-13
 * Phase: Product Editor Unification
 */

import type { ProductFormData } from '~/types/product'
import { productLogger } from '~/utils/logger'

// AI Analysis response interface
export interface AIAnalysisResponse {
  attributes: AIAttributes
  images_analyzed: number
  tokens_used: number
}

// AI extracted attributes
export interface AIAttributes {
  title?: string | null
  description?: string | null
  price?: number | null
  category?: string | null
  brand?: string | null
  condition?: number | null
  label_size?: string | null
  color?: string[] | null
  material?: string[] | null
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
  stretch?: string | null
  lining?: string | null
  origin?: string | null
  decade?: string | null
  trend?: string | null
  model?: string | null
  unique_feature?: string[] | null
  marking?: string[] | null
  condition_sup?: string[] | null
  confidence?: number
}

/**
 * AI Image Analysis composable
 *
 * @example
 * ```typescript
 * const ai = useProductAIAnalysis()
 *
 * // Analyze new photos
 * const result = await ai.analyzePhotos(files)
 * ai.fillFormWithResults(result.attributes, form)
 *
 * // Analyze existing product images
 * const result = await ai.analyzeExistingImages(productId)
 * ai.fillFormWithResults(result.attributes, form)
 * ```
 */
export function useProductAIAnalysis() {
  const { post } = useApi()
  const { showSuccess, showError, showWarn } = useAppToast()

  // State
  const isAnalyzing = ref(false)
  const lastAnalysisResult = ref<AIAnalysisResponse | null>(null)
  const error = ref<string | null>(null)

  /**
   * Analyze new photos (uploaded files)
   */
  const analyzePhotos = async (files: File[]): Promise<AIAnalysisResponse | null> => {
    if (files.length === 0) {
      showWarn('Pas de photos', 'Ajoutez au moins une photo pour utiliser l\'IA', 3000)
      return null
    }

    isAnalyzing.value = true
    error.value = null

    try {
      const formData = new FormData()
      for (const file of files) {
        formData.append('files', file)
      }

      const response = await post<AIAnalysisResponse>('/products/analyze-images-direct', formData)

      if (response) {
        lastAnalysisResult.value = response
        return response
      }

      return null
    } catch (err: any) {
      handleAnalysisError(err)
      throw err
    } finally {
      isAnalyzing.value = false
    }
  }

  /**
   * Analyze existing product images (already uploaded to server)
   */
  const analyzeExistingImages = async (productId: number): Promise<AIAnalysisResponse | null> => {
    isAnalyzing.value = true
    error.value = null

    try {
      const response = await post<AIAnalysisResponse>(`/products/${productId}/analyze-images`)

      if (response) {
        lastAnalysisResult.value = response
        return response
      }

      return null
    } catch (err: any) {
      handleAnalysisError(err)
      throw err
    } finally {
      isAnalyzing.value = false
    }
  }

  /**
   * Main analysis method - decides between direct upload or existing images
   */
  const analyze = async (
    files: File[],
    productId?: number,
    hasExistingOnly: boolean = false
  ): Promise<AIAnalysisResponse | null> => {
    // If we have new files, analyze them directly
    if (files.length > 0) {
      return await analyzePhotos(files)
    }

    // If we only have existing images and a product ID, analyze those
    if (hasExistingOnly && productId) {
      return await analyzeExistingImages(productId)
    }

    showWarn('Pas de photos', 'Ajoutez au moins une photo pour utiliser l\'IA', 3000)
    return null
  }

  /**
   * Fill form with AI analysis results
   */
  const fillFormWithResults = (attrs: AIAttributes, form: Ref<ProductFormData>): number => {
    // Simple field mappings (API field -> form field)
    const simpleMappings: [keyof AIAttributes, keyof ProductFormData][] = [
      ['title', 'title'],
      ['description', 'description'],
      ['price', 'price'],
      ['category', 'category'],
      ['brand', 'brand'],
      ['condition', 'condition'],
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

    let fieldsUpdated = 0

    // Apply simple mappings
    for (const [aiField, formField] of simpleMappings) {
      const value = attrs[aiField]
      if (value !== null && value !== undefined) {
        (form.value as any)[formField] = value
        fieldsUpdated++
      }
    }

    // Handle label_size -> size_original mapping
    if (attrs.label_size) {
      form.value.size_original = attrs.label_size
      fieldsUpdated++
    }

    // Handle array fields (backend already converts to arrays)
    const arrayFields: (keyof AIAttributes)[] = ['condition_sup', 'unique_feature', 'marking']
    for (const field of arrayFields) {
      const value = attrs[field]
      if (value && Array.isArray(value) && value.length > 0) {
        (form.value as any)[field] = value
        fieldsUpdated++
      }
    }

    // Handle color (backend returns array, form expects comma-separated string)
    if (attrs.color && Array.isArray(attrs.color) && attrs.color.length > 0) {
      form.value.color = attrs.color.join(', ')
      fieldsUpdated++
    }

    // Handle material (backend returns array, form expects comma-separated string)
    if (attrs.material && Array.isArray(attrs.material) && attrs.material.length > 0) {
      form.value.material = attrs.material.join(', ')
      fieldsUpdated++
    }

    productLogger.debug(`Filled ${fieldsUpdated} fields from AI analysis`)
    return fieldsUpdated
  }

  /**
   * Handle analysis errors
   */
  const handleAnalysisError = (err: any) => {
    productLogger.error('AI analysis error', { error: err.message })

    if (err?.statusCode === 402) {
      error.value = 'Crédits insuffisants'
      showError(
        'Crédits insuffisants',
        'Vous n\'avez plus de crédits IA. Passez à un abonnement supérieur.',
        5000
      )
    } else {
      error.value = err.message || 'Erreur d\'analyse'
      showError(
        'Erreur d\'analyse',
        err.message || 'Impossible d\'analyser les images. Réessayez plus tard.',
        5000
      )
    }
  }

  /**
   * Show success message after analysis
   */
  const showAnalysisSuccess = (imagesAnalyzed: number, confidence?: number) => {
    const confidenceText = confidence
      ? ` avec confiance ${Math.round(confidence * 100)}%`
      : ''

    showSuccess(
      'Analyse terminée',
      `${imagesAnalyzed} image(s) analysée(s). Formulaire pré-rempli${confidenceText}`,
      4000
    )
  }

  /**
   * Reset state
   */
  const reset = () => {
    isAnalyzing.value = false
    lastAnalysisResult.value = null
    error.value = null
  }

  return {
    // State
    isAnalyzing: readonly(isAnalyzing),
    lastAnalysisResult: readonly(lastAnalysisResult),
    error: readonly(error),

    // Methods
    analyzePhotos,
    analyzeExistingImages,
    analyze,
    fillFormWithResults,
    showAnalysisSuccess,
    reset
  }
}

interface VisionAnalysisResponse {
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
    condition_sup?: string | null
    unique_feature?: string | null
    marking?: string | null
    confidence?: number
  }
  model: string
  images_analyzed: number
  tokens_used: number
  cost: number
  processing_time_ms: number
}

export function useProductFormAI(
  productId: Ref<number | undefined>,
  hasImages: Ref<boolean>,
  updateField: (field: string, value: any) => void
) {
  const { post } = useApi()
  const { showSuccess, showError } = useAppToast()

  const isGeneratingDescription = ref(false)
  const isAnalyzingImages = ref(false)

  const generateDescription = async () => {
    if (!productId.value) {
      showError('Erreur', 'Sauvegardez d\'abord le produit avant de générer une description')
      return
    }

    isGeneratingDescription.value = true

    try {
      const response = await post<{ description: string }>(
        `/products/${productId.value}/generate-description`
      )

      if (response?.description) {
        updateField('description', response.description)
        showSuccess('Description générée', 'La description a été générée par l\'IA')
      }
    } catch (error: any) {
      const message = error?.data?.detail || error?.message || 'Erreur lors de la génération'

      if (message.includes('Crédits IA insuffisants') || error?.status === 402) {
        showError('Crédits insuffisants', 'Vous n\'avez plus de crédits IA. Upgradez votre abonnement.')
      } else {
        showError('Erreur', message)
      }
    } finally {
      isGeneratingDescription.value = false
    }
  }

  const analyzeAndFillForm = async () => {
    if (!productId.value) {
      showError('Erreur', 'Sauvegardez d\'abord le produit avant d\'analyser les images')
      return
    }

    if (!hasImages.value) {
      showError('Erreur', 'Ajoutez des images au produit avant de lancer l\'analyse')
      return
    }

    isAnalyzingImages.value = true

    try {
      const response = await post<VisionAnalysisResponse>(
        `/products/${productId.value}/analyze-images`
      )

      if (response?.attributes) {
        const attrs = response.attributes
        let fieldsUpdated = 0

        // Auto-fill all non-null fields
        if (attrs.title) { updateField('title', attrs.title); fieldsUpdated++ }
        if (attrs.description) { updateField('description', attrs.description); fieldsUpdated++ }
        if (attrs.price) { updateField('price', attrs.price); fieldsUpdated++ }
        if (attrs.category) { updateField('category', attrs.category); fieldsUpdated++ }
        if (attrs.brand) { updateField('brand', attrs.brand); fieldsUpdated++ }
        if (attrs.condition !== null && attrs.condition !== undefined) {
          updateField('condition', String(attrs.condition))
          fieldsUpdated++
        }
        if (attrs.color) { updateField('color', attrs.color); fieldsUpdated++ }
        if (attrs.material) { updateField('material', attrs.material); fieldsUpdated++ }
        if (attrs.size) { updateField('size', attrs.size); fieldsUpdated++ }
        if (attrs.label_size) { updateField('label_size', attrs.label_size); fieldsUpdated++ }
        if (attrs.gender) { updateField('gender', attrs.gender); fieldsUpdated++ }
        if (attrs.season) { updateField('season', attrs.season); fieldsUpdated++ }
        if (attrs.fit) { updateField('fit', attrs.fit); fieldsUpdated++ }
        if (attrs.pattern) { updateField('pattern', attrs.pattern); fieldsUpdated++ }
        if (attrs.neckline) { updateField('neckline', attrs.neckline); fieldsUpdated++ }
        if (attrs.unique_feature) { updateField('unique_feature', attrs.unique_feature); fieldsUpdated++ }
        if (attrs.marking) { updateField('marking', attrs.marking); fieldsUpdated++ }

        const confidence = attrs.confidence ? Math.round(attrs.confidence * 100) : 0
        showSuccess(
          'Formulaire rempli',
          `${response.images_analyzed} image(s) analysée(s), ${fieldsUpdated} champ(s) rempli(s) (confiance: ${confidence}%)`
        )
      }
    } catch (error: any) {
      const message = error?.data?.detail || error?.message || 'Erreur lors de l\'analyse'

      if (message.includes('Crédits IA insuffisants') || error?.status === 402) {
        showError('Crédits insuffisants', 'Vous n\'avez plus de crédits IA. Upgradez votre abonnement.')
      } else if (message.includes('pas d\'images')) {
        showError('Pas d\'images', 'Ajoutez des images au produit avant de lancer l\'analyse.')
      } else {
        showError('Erreur', message)
      }
    } finally {
      isAnalyzingImages.value = false
    }
  }

  return {
    isGeneratingDescription,
    isAnalyzingImages,
    generateDescription,
    analyzeAndFillForm,
  }
}

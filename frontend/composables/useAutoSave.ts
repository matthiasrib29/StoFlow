import { ref, computed } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import type { ProductFormData } from '~/types/product'

export interface AutoSaveOptions {
  productId: number
  debounceMs?: number
  onSuccess?: () => void
  onError?: (error: Error) => void
}

export function useAutoSave(options: AutoSaveOptions) {
  const { patch } = useApi()
  const { showSuccess, showError } = useAppToast()

  const isSaving = ref(false)
  const lastSaved = ref<Date | null>(null)
  const saveError = ref<Error | null>(null)

  const saveProduct = async (formData: Partial<ProductFormData>) => {
    if (!options.productId) return

    isSaving.value = true
    saveError.value = null

    try {
      await patch(`/api/products/${options.productId}`, formData)

      lastSaved.value = new Date()
      showSuccess('Sauvegardé', 'Modifications enregistrées', 2000)

      options.onSuccess?.()
    } catch (error: any) {
      saveError.value = error
      showError('Erreur de sauvegarde', error.message, 4000)
      options.onError?.(error)
    } finally {
      isSaving.value = false
    }
  }

  const debouncedSave = useDebounceFn((formData: Partial<ProductFormData>) => {
    saveProduct(formData)
  }, options.debounceMs || 2000)

  const triggerSave = (formData: Partial<ProductFormData>) => {
    const cleanData = Object.fromEntries(
      Object.entries(formData).filter(([_, v]) => v !== null && v !== undefined)
    )
    debouncedSave(cleanData)
  }

  const statusText = computed(() => {
    if (isSaving.value) return 'Sauvegarde...'
    if (saveError.value) return 'Erreur'
    if (lastSaved.value) {
      const elapsed = Date.now() - lastSaved.value.getTime()
      if (elapsed < 60000) return 'Sauvegardé'
      return `Sauvegardé il y a ${Math.floor(elapsed / 60000)}min`
    }
    return 'Non sauvegardé'
  })

  return {
    isSaving,
    lastSaved,
    saveError,
    statusText,
    triggerSave
  }
}

import { ref } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import type { ProductFormData } from '~/types/product'

const STORAGE_KEY = 'stoflow_product_draft'
const EXPIRY_DAYS = 7

interface Photo {
  file?: File
  preview: string
}

interface DraftData {
  formData: ProductFormData
  // Store only previews, not File objects (can't serialize)
  photoCount: number
  savedAt: string
  expiresAt: string
}

/**
 * Composable for auto-saving product form drafts to localStorage
 *
 * Features:
 * - Auto-save with debounce (2s)
 * - Restore on page load
 * - 7 days expiration
 * - Clear draft functionality
 *
 * @example
 * ```typescript
 * const { saveDraft, loadDraft, clearDraft, hasDraft, lastSaved } = useProductDraft()
 *
 * // Restore on mount
 * onMounted(() => {
 *   const draft = loadDraft()
 *   if (draft) {
 *     formData.value = draft.formData
 *   }
 * })
 *
 * // Auto-save on changes
 * watch(formData, () => debouncedSave(), { deep: true })
 * ```
 */
export function useProductDraft() {
  const hasDraft = ref(false)
  const lastSaved = ref<Date | null>(null)

  /**
   * Add days to a date
   */
  const addDays = (date: Date, days: number): Date => {
    const result = new Date(date)
    result.setDate(result.getDate() + days)
    return result
  }

  /**
   * Save draft to localStorage
   */
  const saveDraft = (formData: ProductFormData, photos: Photo[] = []): void => {
    try {
      const draft: DraftData = {
        formData,
        photoCount: photos.length,
        savedAt: new Date().toISOString(),
        expiresAt: addDays(new Date(), EXPIRY_DAYS).toISOString()
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(draft))
      lastSaved.value = new Date()
      hasDraft.value = true
    } catch (error) {
      console.warn('[useProductDraft] Failed to save draft:', error)
    }
  }

  /**
   * Debounced save (2 seconds)
   */
  const debouncedSave = useDebounceFn((formData: ProductFormData, photos: Photo[] = []) => {
    saveDraft(formData, photos)
  }, 2000)

  /**
   * Load draft from localStorage
   * Returns null if no draft or expired
   */
  const loadDraft = (): { formData: ProductFormData; photoCount: number } | null => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) {
        hasDraft.value = false
        return null
      }

      const draft: DraftData = JSON.parse(raw)

      // Check expiration
      if (new Date(draft.expiresAt) < new Date()) {
        clearDraft()
        return null
      }

      hasDraft.value = true
      lastSaved.value = new Date(draft.savedAt)

      return {
        formData: draft.formData,
        photoCount: draft.photoCount
      }
    } catch (error) {
      console.warn('[useProductDraft] Failed to load draft:', error)
      return null
    }
  }

  /**
   * Clear draft from localStorage
   */
  const clearDraft = (): void => {
    try {
      localStorage.removeItem(STORAGE_KEY)
      hasDraft.value = false
      lastSaved.value = null
    } catch (error) {
      console.warn('[useProductDraft] Failed to clear draft:', error)
    }
  }

  /**
   * Check if a draft exists (without loading it)
   */
  const checkHasDraft = (): boolean => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return false

      const draft: DraftData = JSON.parse(raw)
      if (new Date(draft.expiresAt) < new Date()) {
        clearDraft()
        return false
      }

      hasDraft.value = true
      return true
    } catch {
      return false
    }
  }

  /**
   * Format last saved time for display
   */
  const formatLastSaved = (): string => {
    if (!lastSaved.value) return ''

    const now = new Date()
    const diff = now.getTime() - lastSaved.value.getTime()
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)

    if (seconds < 60) return 'à l\'instant'
    if (minutes < 60) return `il y a ${minutes} min`

    return lastSaved.value.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return {
    // State
    hasDraft,
    lastSaved,

    // Methods
    saveDraft,
    debouncedSave,
    loadDraft,
    clearDraft,
    checkHasDraft,
    formatLastSaved
  }
}

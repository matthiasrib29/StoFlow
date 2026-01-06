import { ref, computed, readonly, type Ref } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import type { ProductFormData } from '~/types/product'

// Re-export ProductFormData for backwards compatibility
export type { ProductFormData } from '~/types/product'

/**
 * Composable pour la validation du formulaire produit
 *
 * Gère la validation des champs obligatoires et des formats
 * avec affichage d'erreurs contextuelles en français.
 *
 * @example
 * ```typescript
 * const validation = useProductFormValidation()
 *
 * // Marquer un champ comme touché au blur
 * validation.touch('title')
 *
 * // Valider un champ
 * if (validation.hasError('title')) {
 *   const error = validation.getError('title')
 * }
 *
 * // Valider le formulaire complet
 * if (validation.validateForm(formData)) {
 *   // Soumettre
 * }
 * ```
 */
export function useProductFormValidation() {
  // État des erreurs : Map<champ, message>
  const errors = ref<Map<string, string>>(new Map())

  // Champs qui ont été touchés par l'utilisateur
  const touched = ref<Set<string>>(new Set())

  // Champs qui sont valides et remplis
  const validFields = ref<Set<string>>(new Set())

  /**
   * Marquer un champ comme touché
   */
  const touch = (field: string): void => {
    touched.value.add(field)
  }

  /**
   * Valider un champ individuel
   * @returns Message d'erreur ou null si valide
   */
  const validateField = (field: keyof ProductFormData | string, value: any): string | null => {
    // Champs obligatoires (mis à jour pour le nouveau formulaire)
    const requiredFields = [
      'title',
      'description',
      'category',
      'brand',
      'condition',
      'size_original',
      'color',
      'gender',
      'material'
    ]

    if (requiredFields.includes(field)) {
      if (value === null || value === undefined) {
        return 'Ce champ est requis'
      }
      if (typeof value === 'string' && value.trim() === '') {
        return 'Ce champ est requis'
      }
      // Condition peut être 0 (valide)
      if (field === 'condition' && typeof value === 'number' && value < 0) {
        return 'Ce champ est requis'
      }
    }

    // Validation spécifique par type de champ

    // Condition : nombre 0-10
    if (field === 'condition') {
      if (value !== null && value !== undefined) {
        if (typeof value !== 'number') {
          return 'L\'état doit être un nombre'
        }
        if (value < 0 || value > 10) {
          return 'L\'état doit être entre 0 et 10'
        }
      }
    }

    // Prix : nombre positif ou null
    if (field === 'price') {
      if (value !== null) {
        if (typeof value !== 'number') {
          return 'Le prix doit être un nombre'
        }
        if (value < 0) {
          return 'Le prix doit être un nombre positif'
        }
        if (value > 999999) {
          return 'Le prix est trop élevé (max: 999999)'
        }
      }
    }

    // Stock : entier positif obligatoire
    if (field === 'stock_quantity') {
      if (value === null || value === undefined) {
        return 'Le stock est requis'
      }
      if (typeof value !== 'number') {
        return 'Le stock doit être un nombre'
      }
      if (value < 0) {
        return 'Le stock doit être positif ou zéro'
      }
      if (!Number.isInteger(value)) {
        return 'Le stock doit être un nombre entier'
      }
      if (value > 10000) {
        return 'Le stock est trop élevé (max: 10000)'
      }
    }

    // Dimensions : nombres positifs optionnels
    if (field.startsWith('dim')) {
      if (value !== null && value !== undefined) {
        if (typeof value !== 'number') {
          return 'La dimension doit être un nombre'
        }
        if (value < 0) {
          return 'La dimension doit être positive'
        }
        if (value > 500) {
          return 'La dimension est trop élevée (max: 500cm)'
        }
      }
    }

    // Titre : longueur min/max
    if (field === 'title') {
      if (typeof value === 'string') {
        const trimmed = value.trim()
        if (trimmed.length < 3) {
          return 'Le titre doit contenir au moins 3 caractères'
        }
        if (trimmed.length > 500) {
          return 'Le titre est trop long (max: 500 caractères)'
        }
      }
    }

    // Description : longueur min/max
    if (field === 'description') {
      if (typeof value === 'string') {
        const trimmed = value.trim()
        if (trimmed.length < 10) {
          return 'La description doit contenir au moins 10 caractères'
        }
        if (trimmed.length > 5000) {
          return 'La description est trop longue (max: 5000 caractères)'
        }
      }
    }

    // Taille : longueur max
    if (field === 'size_original') {
      if (typeof value === 'string' && value.length > 100) {
        return 'La taille est trop longue (max: 100 caractères)'
      }
    }

    return null
  }

  /**
   * Valider le formulaire complet
   * @returns true si valide, false sinon
   */
  const validateForm = (formData: ProductFormData): boolean => {
    const newErrors = new Map<string, string>()

    // Valider tous les champs
    const fields = Object.keys(formData) as Array<keyof ProductFormData>

    fields.forEach(field => {
      const error = validateField(field, formData[field])
      if (error) {
        newErrors.set(field, error)
      }
    })

    errors.value = newErrors
    return newErrors.size === 0
  }

  /**
   * Valider un champ et mettre à jour les erreurs
   */
  const validateAndSetError = (field: keyof ProductFormData | string, value: any): void => {
    const error = validateField(field, value)

    if (error) {
      errors.value.set(field, error)
      validFields.value.delete(field)
    } else {
      errors.value.delete(field)
      // Mark as valid only if the field has a value
      const hasValue = value !== null && value !== undefined && value !== ''
      if (hasValue) {
        validFields.value.add(field)
      } else {
        validFields.value.delete(field)
      }
    }
  }

  /**
   * Validation avec debounce (300ms) pour éviter trop de validations
   */
  const debouncedValidate = useDebounceFn((field: string, value: any) => {
    validateAndSetError(field, value)
  }, 300)

  /**
   * Valider un champ avec debounce (pour utiliser sur @input)
   */
  const validateDebounced = (field: keyof ProductFormData | string, value: any): void => {
    touched.value.add(field)
    debouncedValidate(field, value)
  }

  /**
   * Vérifier si un champ est valide ET rempli (pour afficher checkmark)
   */
  const isFieldValid = (field: string): boolean => {
    return validFields.value.has(field) && !errors.value.has(field)
  }

  /**
   * Obtenir le message d'erreur d'un champ
   */
  const getError = (field: string): string | undefined => {
    return errors.value.get(field)
  }

  /**
   * Vérifier si un champ a une erreur ET a été touché
   */
  const hasError = (field: string): boolean => {
    return touched.value.has(field) && errors.value.has(field)
  }

  /**
   * Vérifier si le formulaire est valide (aucune erreur)
   */
  const isValid = computed(() => errors.value.size === 0)

  /**
   * Réinitialiser la validation
   */
  const reset = (): void => {
    errors.value.clear()
    touched.value.clear()
    validFields.value.clear()
  }

  /**
   * Marquer tous les champs comme touchés
   * Utile pour afficher toutes les erreurs lors du submit
   */
  const touchAll = (formData: ProductFormData): void => {
    const fields = Object.keys(formData)
    fields.forEach(field => touched.value.add(field))
  }

  return {
    // État (readonly pour éviter modifications externes)
    errors: readonly(errors) as Readonly<Ref<Map<string, string>>>,
    touched: readonly(touched) as Readonly<Ref<Set<string>>>,
    validFields: readonly(validFields) as Readonly<Ref<Set<string>>>,
    isValid,

    // Méthodes
    touch,
    touchAll,
    validateField,
    validateForm,
    validateAndSetError,
    validateDebounced,
    getError,
    hasError,
    isFieldValid,
    reset
  }
}

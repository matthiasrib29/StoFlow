import type { Ref } from 'vue'
import type { AttributeOption } from '~/composables/useAttributes'

/**
 * Composable pour charger des attributs de manière générique
 *
 * Élimine la duplication des blocs try/finally identiques
 * pour le chargement d'attributs (colors, materials, fits, etc.)
 *
 * @example
 * ```typescript
 * const { loadMultipleAttributes } = useAttributeLoader()
 *
 * await loadMultipleAttributes([
 *   { type: 'colors', targetRef: colors, loadingRef: loadingColors },
 *   { type: 'materials', targetRef: materials, loadingRef: loadingMaterials }
 * ], 'fr')
 * ```
 */
export function useAttributeLoader() {
  const { fetchAttribute } = useAttributes()

  /**
   * Charger un attribut avec gestion de l'état de chargement
   *
   * @param attributeType - Type d'attribut ('colors', 'materials', 'fits', etc.)
   * @param lang - Langue pour les labels
   * @param targetRef - Ref où stocker les données chargées
   * @param loadingRef - Ref pour l'état de chargement
   */
  const loadAttribute = async <T = AttributeOption>(
    attributeType: string,
    lang: string,
    targetRef: Ref<T[]>,
    loadingRef: Ref<boolean>
  ): Promise<void> => {
    loadingRef.value = true
    try {
      const data = await fetchAttribute<T>(attributeType, lang)
      targetRef.value = data
    } catch (error) {
      console.error(`Error loading ${attributeType}:`, error)
      targetRef.value = []
    } finally {
      loadingRef.value = false
    }
  }

  /**
   * Charger plusieurs attributs en parallèle
   *
   * @param attributes - Tableau de configurations d'attributs
   * @param lang - Langue pour les labels
   */
  const loadMultipleAttributes = async <T = AttributeOption>(
    attributes: Array<{
      type: string
      targetRef: Ref<T[]>
      loadingRef: Ref<boolean>
    }>,
    lang: string
  ): Promise<void> => {
    await Promise.all(
      attributes.map(attr =>
        loadAttribute(attr.type, lang, attr.targetRef, attr.loadingRef)
      )
    )
  }

  return {
    loadAttribute,
    loadMultipleAttributes
  }
}

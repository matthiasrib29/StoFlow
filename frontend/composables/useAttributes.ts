/**
 * Composable pour récupérer les attributs de produits
 *
 * Ce composable gère les appels API pour récupérer :
 * - Catégories
 * - Conditions (états)
 * - Genres
 * - Saisons
 * - Marques
 *
 * Les données sont mises en cache côté client pour éviter
 * des appels répétés au backend.
 */

export interface AttributeOption {
  value: string
  label: string
}

export interface CategoryOption extends AttributeOption {
  parent?: string | null
  default_gender?: string | null
}

export interface ConditionOption extends AttributeOption {
  coefficient: number
  vinted_id?: number | null
  ebay_condition?: string | null
}

export const useAttributes = () => {
  const config = useRuntimeConfig()
  const apiUrl = config.public.apiUrl || 'http://localhost:8000'

  // États réactifs pour les données
  const categories = ref<CategoryOption[]>([])
  const conditions = ref<ConditionOption[]>([])
  const genders = ref<AttributeOption[]>([])
  const seasons = ref<AttributeOption[]>([])
  const brands = ref<AttributeOption[]>([])

  // États de chargement
  const loadingCategories = ref(false)
  const loadingConditions = ref(false)
  const loadingGenders = ref(false)
  const loadingSeasons = ref(false)
  const loadingBrands = ref(false)

  /**
   * Fonction générique pour récupérer n'importe quel type d'attribut
   */
  const fetchAttribute = async <T = AttributeOption>(
    attributeType: string,
    lang: string = 'en',
    search?: string,
    limit: number = 100
  ): Promise<T[]> => {
    try {
      const response = await $fetch<T[]>(
        `${apiUrl}/api/attributes/${attributeType}`,
        {
          params: {
            lang,
            search,
            limit
          }
        }
      )
      return response
    } catch (error) {
      console.error(`Error fetching ${attributeType}:`, error)
      return []
    }
  }

  /**
   * Récupère les catégories depuis l'API
   */
  const fetchCategories = async (lang: string = 'en') => {
    if (categories.value.length > 0) return categories.value

    loadingCategories.value = true
    try {
      const response = await fetchAttribute<CategoryOption>('categories', lang)
      categories.value = response
      return response
    } finally {
      loadingCategories.value = false
    }
  }

  /**
   * Récupère les conditions depuis l'API
   */
  const fetchConditions = async (lang: string = 'en') => {
    if (conditions.value.length > 0) return conditions.value

    loadingConditions.value = true
    try {
      const response = await fetchAttribute<ConditionOption>('conditions', lang)
      conditions.value = response
      return response
    } finally {
      loadingConditions.value = false
    }
  }

  /**
   * Récupère les genres depuis l'API
   */
  const fetchGenders = async (lang: string = 'en') => {
    if (genders.value.length > 0) return genders.value

    loadingGenders.value = true
    try {
      const response = await fetchAttribute('genders', lang)
      genders.value = response
      return response
    } finally {
      loadingGenders.value = false
    }
  }

  /**
   * Récupère les saisons depuis l'API
   */
  const fetchSeasons = async (lang: string = 'en') => {
    if (seasons.value.length > 0) return seasons.value

    loadingSeasons.value = true
    try {
      const response = await fetchAttribute('seasons', lang)
      seasons.value = response
      return response
    } finally {
      loadingSeasons.value = false
    }
  }

  /**
   * Récupère les marques depuis l'API
   */
  const fetchBrands = async (search?: string, limit: number = 100) => {
    loadingBrands.value = true
    try {
      const response = await fetchAttribute('brands', 'en', search, limit)
      brands.value = response
      return response
    } finally {
      loadingBrands.value = false
    }
  }

  /**
   * Recherche des marques pour l'autocomplétion (sans mettre en cache)
   * Retourne directement les résultats sans les stocker dans brands
   */
  const searchBrands = async (query: string, limit: number = 20): Promise<AttributeOption[]> => {
    if (!query || query.length < 1) {
      return []
    }

    try {
      const response = await $fetch<AttributeOption[]>(
        `${apiUrl}/api/attributes/brands`,
        {
          params: {
            search: query,
            limit
          }
        }
      )
      return response
    } catch (error) {
      console.error('Error searching brands:', error)
      return []
    }
  }

  /**
   * Charge tous les attributs en une seule fois
   */
  const fetchAllAttributes = async (lang: string = 'en') => {
    await Promise.all([
      fetchCategories(lang),
      fetchConditions(lang),
      fetchGenders(lang),
      fetchSeasons(lang)
    ])
  }

  /**
   * Réinitialise le cache des attributs
   */
  const clearCache = () => {
    categories.value = []
    conditions.value = []
    genders.value = []
    seasons.value = []
    brands.value = []
  }

  return {
    // États
    categories,
    conditions,
    genders,
    seasons,
    brands,

    // États de chargement
    loadingCategories,
    loadingConditions,
    loadingGenders,
    loadingSeasons,
    loadingBrands,

    // Méthodes spécifiques
    fetchCategories,
    fetchConditions,
    fetchGenders,
    fetchSeasons,
    fetchBrands,
    searchBrands,
    fetchAllAttributes,
    clearCache,

    // Méthode générique (pour nouveaux attributs sans méthode dédiée)
    fetchAttribute
  }
}

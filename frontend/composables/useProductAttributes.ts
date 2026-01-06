/**
 * Composable for managing product form attributes
 *
 * Handles loading all attributes needed for ProductFormCharacteristics:
 * - Required: categories, brands, colors, materials, genders, sizes
 * - Clothing: fits, seasons, sports, necklines, lengths, patterns, rises, closures, sleeve_lengths
 * - Vintage: origins, decades, trends
 */

import type { AttributeOption } from '~/composables/useAttributes'
import { useLocaleStore } from '~/stores/locale'

export interface ProductAttributesState {
  // Required field options
  genders: AttributeOption[]
  sizes: AttributeOption[]
  // Clothing options
  fits: AttributeOption[]
  seasons: AttributeOption[]
  sports: AttributeOption[]
  necklines: AttributeOption[]
  lengths: AttributeOption[]
  patterns: AttributeOption[]
  rises: AttributeOption[]
  closures: AttributeOption[]
  sleeveLengths: AttributeOption[]
  // Vintage options
  origins: AttributeOption[]
  decades: AttributeOption[]
  trends: AttributeOption[]
  // Raw data for autocomplete
  categories: AttributeOption[]
  colors: AttributeOption[]
  materials: AttributeOption[]
}

export interface ProductAttributesLoading {
  categories: boolean
  brands: boolean
  colors: boolean
  materials: boolean
  genders: boolean
  sizes: boolean
}

export const useProductAttributes = () => {
  const localeStore = useLocaleStore()
  const { fetchAttribute, searchBrands } = useAttributes()

  // Loading states
  const loading = reactive<ProductAttributesLoading>({
    categories: false,
    brands: false,
    colors: false,
    materials: false,
    genders: false,
    sizes: false
  })

  // All options
  const options = reactive<ProductAttributesState>({
    genders: [],
    sizes: [],
    fits: [],
    seasons: [],
    sports: [],
    necklines: [],
    lengths: [],
    patterns: [],
    rises: [],
    closures: [],
    sleeveLengths: [],
    origins: [],
    decades: [],
    trends: [],
    categories: [],
    colors: [],
    materials: []
  })

  // Suggestions for autocomplete
  const suggestions = reactive({
    categories: [] as string[],
    brands: [] as string[],
    colors: [] as string[],
    materials: [] as string[]
  })

  /**
   * Load all attributes from API
   */
  const loadAllAttributes = async () => {
    const lang = localeStore.locale
    loading.sizes = true

    const [
      genders, sizes, fits, seasons, sports, necklines, lengths,
      patterns, rises, closures, sleeves, origins, decades, trends,
      categories, colors, materials
    ] = await Promise.all([
      fetchAttribute('genders', lang),
      fetchAttribute('sizes', lang),
      fetchAttribute('fits', lang),
      fetchAttribute('seasons', lang),
      fetchAttribute('sports', lang),
      fetchAttribute('necklines', lang),
      fetchAttribute('lengths', lang),
      fetchAttribute('patterns', lang),
      fetchAttribute('rises', lang),
      fetchAttribute('closures', lang),
      fetchAttribute('sleeve_lengths', lang),
      fetchAttribute('origins', lang),
      fetchAttribute('decades', lang),
      fetchAttribute('trends', lang),
      fetchAttribute('categories', lang),
      fetchAttribute('colors', lang),
      fetchAttribute('materials', lang)
    ])

    // Assign to reactive state
    options.genders = genders
    options.sizes = sizes
    options.fits = fits
    options.seasons = seasons
    options.sports = sports
    options.necklines = necklines
    options.lengths = lengths
    options.patterns = patterns
    options.rises = rises
    options.closures = closures
    options.sleeveLengths = sleeves
    options.origins = origins
    options.decades = decades
    options.trends = trends
    options.categories = categories
    options.colors = colors
    options.materials = materials

    loading.sizes = false
  }

  /**
   * Search categories locally
   */
  const searchCategories = (query: string) => {
    const q = query.toLowerCase()
    suggestions.categories = options.categories
      .filter(c => c.label.toLowerCase().includes(q))
      .map(c => c.label)
      .slice(0, 10)
  }

  /**
   * Search brands from API
   */
  const searchBrandsAsync = async (query: string) => {
    loading.brands = true
    try {
      const results = await searchBrands(query)
      suggestions.brands = results.map(b => b.label)
    } finally {
      loading.brands = false
    }
  }

  /**
   * Search colors locally
   */
  const searchColors = (query: string) => {
    const q = query.toLowerCase()
    suggestions.colors = options.colors
      .filter(c => c.label.toLowerCase().includes(q))
      .map(c => c.label)
      .slice(0, 10)
  }

  /**
   * Search materials locally
   */
  const searchMaterials = (query: string) => {
    const q = query.toLowerCase()
    suggestions.materials = options.materials
      .filter(m => m.label.toLowerCase().includes(q))
      .map(m => m.label)
      .slice(0, 10)
  }

  // Watch locale changes and reload
  watch(() => localeStore.locale, () => {
    loadAllAttributes()
  })

  return {
    options,
    loading,
    suggestions,
    loadAllAttributes,
    searchCategories,
    searchBrandsAsync,
    searchColors,
    searchMaterials
  }
}

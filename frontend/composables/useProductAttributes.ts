/**
 * Composable for managing product form attributes
 *
 * Handles loading all attributes needed for ProductFormCharacteristics:
 * - Required: categories, brands, colors, materials, genders, sizes
 * - Clothing: fits, seasons, sports, necklines, lengths, patterns, rises, closures, sleeve_lengths
 * - Vintage: origins, decades, trends
 */

import type { AttributeOption, CategoryOption } from '~/composables/useAttributes'
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
  // Raw data for autocomplete/wizard
  categories: CategoryOption[]
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

  // Filtered options for searchable select
  const filteredOptions = reactive({
    categories: [] as CategoryOption[],
    brands: [] as AttributeOption[],
    colors: [] as AttributeOption[],
    materials: [] as AttributeOption[]
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

    // Initialize filtered options with top 50 items for better UX
    filteredOptions.categories = options.categories.slice(0, 50)
    filteredOptions.colors = options.colors.slice(0, 50)
    filteredOptions.materials = options.materials.slice(0, 50)

    // Load popular brands on initialization
    try {
      filteredOptions.brands = await searchBrands('', 20)
    } catch (error) {
      console.error('Failed to load popular brands', error)
      filteredOptions.brands = []
    }

    loading.sizes = false
  }

  /**
   * Filter categories locally
   * NOTE: No longer used - CategoryWizard handles category selection
   */
  // const filterCategories = (query: string) => {
  //   if (!query) {
  //     filteredOptions.categories = options.categories.slice(0, 50)
  //     return
  //   }
  //   const q = query.toLowerCase()
  //   filteredOptions.categories = options.categories
  //     .filter(c => c.label.toLowerCase().includes(q))
  //     .slice(0, 50)
  // }

  /**
   * Filter brands from API (debounced in component)
   * Shows popular brands when query is empty
   */
  const filterBrands = async (query: string) => {
    loading.brands = true
    try {
      // Load brands even with empty query (API will return popular brands)
      const results = await searchBrands(query || '', 20)
      filteredOptions.brands = results
    } catch (error) {
      console.error('Brand filter failed', error)
      filteredOptions.brands = []
    } finally {
      loading.brands = false
    }
  }

  /**
   * Filter colors locally
   */
  const filterColors = (query: string) => {
    if (!query) {
      filteredOptions.colors = options.colors.slice(0, 50)
      return
    }
    const q = query.toLowerCase()
    filteredOptions.colors = options.colors
      .filter(c => c.label.toLowerCase().includes(q))
      .slice(0, 50)
  }

  /**
   * Filter materials locally
   */
  const filterMaterials = (query: string) => {
    if (!query) {
      filteredOptions.materials = options.materials.slice(0, 50)
      return
    }
    const q = query.toLowerCase()
    filteredOptions.materials = options.materials
      .filter(m => m.label.toLowerCase().includes(q))
      .slice(0, 50)
  }

  // Watch locale changes and reload
  watch(() => localeStore.locale, () => {
    loadAllAttributes()
  })

  return {
    options,
    loading,
    filteredOptions,
    loadAllAttributes,
    // filterCategories, // No longer used - CategoryWizard handles this
    filterBrands,
    filterColors,
    filterMaterials
  }
}

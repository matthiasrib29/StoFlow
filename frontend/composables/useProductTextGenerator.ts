/**
 * Composable for Product Text Generator
 *
 * Provides methods for generating SEO titles and descriptions for products.
 * Integrates with backend API and manages user settings.
 *
 * Created: 2026-01-13
 */

import { ref, computed, readonly } from 'vue'
import type { ComputedRef, Ref } from 'vue'
import type {
  TitleFormat,
  DescriptionStyle,
  TextPreviewInput,
  TextGeneratorOutput,
  TextGeneratorSettings,
  SelectOption,
} from '~/types/textGenerator'
import {
  TITLE_FORMAT_LABELS,
  DESCRIPTION_STYLE_LABELS,
} from '~/types/textGenerator'
import { apiLogger } from '~/utils/logger'

export interface UseProductTextGeneratorReturn {
  // State (readonly)
  titles: Readonly<Ref<Record<string, string>>>
  descriptions: Readonly<Ref<Record<string, string>>>
  loading: Readonly<Ref<boolean>>
  error: Readonly<Ref<string | null>>
  settings: Readonly<Ref<TextGeneratorSettings | null>>
  // Computed
  hasResults: ComputedRef<boolean>
  titleFormatOptions: ComputedRef<SelectOption<TitleFormat>[]>
  descriptionStyleOptions: ComputedRef<SelectOption<DescriptionStyle>[]>
  // Methods
  generate: (productId: number, options?: { titleFormat?: TitleFormat; descriptionStyle?: DescriptionStyle }) => Promise<void>
  preview: (attributes: TextPreviewInput) => Promise<void>
  loadSettings: () => Promise<void>
  saveSettings: (settings: Partial<TextGeneratorSettings>) => Promise<void>
  clearResults: () => void
}

export function useProductTextGenerator(): UseProductTextGeneratorReturn {
  const { post, get, patch } = useApi()

  // State
  const titles = ref<Record<string, string>>({})
  const descriptions = ref<Record<string, string>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)
  const settings = ref<TextGeneratorSettings | null>(null)

  // Computed
  const hasResults = computed(() => {
    return Object.keys(titles.value).length > 0 || Object.keys(descriptions.value).length > 0
  })

  const titleFormatOptions = computed<SelectOption<TitleFormat>[]>(() => {
    return (Object.entries(TITLE_FORMAT_LABELS) as [string, string][]).map(([value, label]) => ({
      value: Number(value) as TitleFormat,
      label,
    }))
  })

  const descriptionStyleOptions = computed<SelectOption<DescriptionStyle>[]>(() => {
    return (Object.entries(DESCRIPTION_STYLE_LABELS) as [string, string][]).map(([value, label]) => ({
      value: Number(value) as DescriptionStyle,
      label,
    }))
  })

  /**
   * Generate titles and descriptions from an existing product
   */
  const generate = async (
    productId: number,
    options?: { titleFormat?: TitleFormat; descriptionStyle?: DescriptionStyle }
  ): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      apiLogger.debug('Generating text for product', { productId, options })

      const result = await post<TextGeneratorOutput>('/products/text/generate', {
        product_id: productId,
        title_format: options?.titleFormat,
        description_style: options?.descriptionStyle,
      })

      titles.value = result.titles
      descriptions.value = result.descriptions

      apiLogger.info('Text generated successfully', { productId, titlesCount: Object.keys(result.titles).length })
    }
    catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to generate text'
      error.value = message
      apiLogger.error('Failed to generate text', { productId, error: message })
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Preview titles and descriptions from raw attributes (before product save)
   */
  const preview = async (attributes: TextPreviewInput): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      apiLogger.debug('Previewing text from attributes', { attributes })

      const result = await post<TextGeneratorOutput>('/products/text/preview', attributes)

      titles.value = result.titles
      descriptions.value = result.descriptions

      apiLogger.info('Text preview generated', { titlesCount: Object.keys(result.titles).length })
    }
    catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to preview text'
      error.value = message
      apiLogger.error('Failed to preview text', { error: message })
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Load user's default text generator settings
   */
  const loadSettings = async (): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      apiLogger.debug('Loading text generator settings')

      const result = await get<TextGeneratorSettings>('/users/me/settings/text-generator')

      settings.value = result

      apiLogger.debug('Settings loaded', { settings: result })
    }
    catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to load settings'
      error.value = message
      apiLogger.error('Failed to load settings', { error: message })
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Save user's default text generator settings
   */
  const saveSettings = async (newSettings: Partial<TextGeneratorSettings>): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      apiLogger.debug('Saving text generator settings', { newSettings })

      const result = await patch<TextGeneratorSettings>('/users/me/settings/text-generator', newSettings)

      settings.value = result

      apiLogger.info('Settings saved successfully')
    }
    catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to save settings'
      error.value = message
      apiLogger.error('Failed to save settings', { error: message })
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Clear all generated results
   */
  const clearResults = (): void => {
    titles.value = {}
    descriptions.value = {}
    error.value = null
  }

  return {
    // State (readonly)
    titles: readonly(titles),
    descriptions: readonly(descriptions),
    loading: readonly(loading),
    error: readonly(error),
    settings: readonly(settings),
    // Computed
    hasResults,
    titleFormatOptions,
    descriptionStyleOptions,
    // Methods
    generate,
    preview,
    loadSettings,
    saveSettings,
    clearResults,
  }
}

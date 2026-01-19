/**
 * Text Generator Types
 *
 * TypeScript interfaces for the text generation feature.
 * Matches the backend schemas from backend/schemas/text_generator.py
 *
 * Created: 2026-01-13
 */

// Title format options (1-5)
export type TitleFormat = 1 | 2 | 3 | 4 | 5

export const TITLE_FORMAT_LABELS: Record<TitleFormat, string> = {
  1: 'Minimaliste',
  2: 'Standard Vinted',
  3: 'SEO & Mots-clés',
  4: 'Vintage & Collectionneur',
  5: 'Technique & Professionnel',
}

// Description style options (1-5)
export type DescriptionStyle = 1 | 2 | 3 | 4 | 5

export const DESCRIPTION_STYLE_LABELS: Record<DescriptionStyle, string> = {
  1: 'Catalogue Structuré',
  2: 'Descriptif Rédigé',
  3: 'Fiche Technique',
  4: 'Vendeur Pro',
  5: 'Visuel Emoji',
}

// API input for generate (existing product)
export interface TextGenerateInput {
  product_id: number
  title_format?: TitleFormat
  description_style?: DescriptionStyle
}

// API input for preview (raw attributes)
export interface TextPreviewInput {
  brand?: string
  model?: string
  category?: string
  gender?: string
  size_normalized?: string
  colors?: string[]
  material?: string
  fit?: string
  condition?: number
  decade?: string
  rise?: string
  closure?: string
  unique_feature?: string[]
  pattern?: string
  trend?: string
  season?: string
  origin?: string
  condition_sup?: string[]
  neckline?: string
  sleeve_length?: string
  lining?: string
  stretch?: string
  sport?: string
  length?: string
  marking?: string
  location?: string
  dim1?: number
  dim2?: number
  dim3?: number
  dim4?: number
  dim5?: number
  dim6?: number
}

// API output
export interface TextGeneratorOutput {
  titles: Record<string, string>
  descriptions: Record<string, string>
}

// User settings
export interface TextGeneratorSettings {
  default_title_format: TitleFormat | null
  default_description_style: DescriptionStyle | null
}

// Options for select dropdowns
export interface SelectOption<T> {
  value: T
  label: string
}

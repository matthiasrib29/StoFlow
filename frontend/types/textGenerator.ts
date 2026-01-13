/**
 * Text Generator Types
 *
 * TypeScript interfaces for the text generation feature.
 * Matches the backend schemas from backend/schemas/text_generator.py
 *
 * Created: 2026-01-13
 */

// Title format options (1-3)
export type TitleFormat = 1 | 2 | 3

export const TITLE_FORMAT_LABELS: Record<TitleFormat, string> = {
  1: 'Ultra Complete',
  2: 'Technical',
  3: 'Style & Trend',
}

// Description style options (1-3)
export type DescriptionStyle = 1 | 2 | 3

export const DESCRIPTION_STYLE_LABELS: Record<DescriptionStyle, string> = {
  1: 'Professional',
  2: 'Storytelling',
  3: 'Minimalist',
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

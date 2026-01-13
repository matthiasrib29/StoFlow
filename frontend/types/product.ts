/**
 * Product Types
 *
 * Type definitions for product-related data structures.
 * Aligned with backend schemas (product_schemas.py).
 */

/**
 * Complete product form data interface.
 * Matches all fields from backend ProductCreate schema.
 */
export interface ProductFormData {
  // === SECTION 1: Infos de base ===
  title: string
  description: string
  price: number | null
  stock_quantity: number

  // === SECTION 2: Caractéristiques ===
  // Obligatoires
  category: string
  brand: string
  condition: number | null          // Note 0-10
  size_original: string             // Texte libre / autocomplete
  size_normalized: string | null    // FK vers sizes.name_en
  color: string
  gender: string
  material: string

  // Optionnels - Vêtements
  fit: string | null
  season: string | null
  sport: string | null
  neckline: string | null
  length: string | null
  pattern: string | null
  rise: string | null
  closure: string | null
  sleeve_length: string | null
  stretch: string | null
  lining: string | null

  // Optionnels - Vintage/Tendance
  origin: string | null
  decade: string | null
  trend: string | null

  // Texte libre
  condition_sup: string[] | null
  location: string | null
  model: string | null
  unique_feature: string[] | null
  marking: string | null

  // === SECTION 3: Mesures & Prix ===
  // Dimensions (en cm)
  dim1: number | null   // Tour de poitrine/Épaules
  dim2: number | null   // Longueur totale
  dim3: number | null   // Longueur manche
  dim4: number | null   // Tour de taille
  dim5: number | null   // Tour de hanches
  dim6: number | null   // Entrejambe

  // Pricing
  pricing_rarity: string | null
  pricing_quality: string | null
  pricing_style: string | null
  pricing_details: string | null
  pricing_edit: string | null
}

/**
 * Default values for a new product form.
 */
export const defaultProductFormData: ProductFormData = {
  // Section 1
  title: '',
  description: '',
  price: null,
  stock_quantity: 1,

  // Section 2 - Obligatoires
  category: '',
  brand: '',
  condition: null,
  size_original: '',
  size_normalized: null,
  color: '',
  gender: '',
  material: '',

  // Section 2 - Optionnels vêtements
  fit: null,
  season: null,
  sport: null,
  neckline: null,
  length: null,
  pattern: null,
  rise: null,
  closure: null,
  sleeve_length: null,
  stretch: null,
  lining: null,

  // Section 2 - Vintage/Tendance
  origin: null,
  decade: null,
  trend: null,

  // Section 2 - Texte libre
  condition_sup: null,
  location: null,
  model: null,
  unique_feature: null,
  marking: null,

  // Section 3 - Dimensions
  dim1: null,
  dim2: null,
  dim3: null,
  dim4: null,
  dim5: null,
  dim6: null,

  // Section 3 - Pricing
  pricing_rarity: null,
  pricing_quality: null,
  pricing_style: null,
  pricing_details: null,
  pricing_edit: null
}

/**
 * Condition labels for the slider.
 * Maps condition note (0-10) to human-readable labels.
 */
export const conditionLabels: Record<number, { label: string; description: string }> = {
  0: { label: 'Défectueux', description: 'Non fonctionnel ou très endommagé' },
  1: { label: 'Très usé', description: 'Usure importante visible' },
  2: { label: 'Usé', description: 'Signes d\'usure évidents' },
  3: { label: 'Usé acceptable', description: 'Usure modérée' },
  4: { label: 'Correct', description: 'Quelques défauts mineurs' },
  5: { label: 'Assez bon', description: 'État acceptable' },
  6: { label: 'Bon', description: 'Légères traces d\'utilisation' },
  7: { label: 'Bon +', description: 'Très peu de traces' },
  8: { label: 'Très bon', description: 'Quasi neuf, infimes traces' },
  9: { label: 'Excellent', description: 'Comme neuf' },
  10: { label: 'Neuf', description: 'Jamais porté, avec étiquettes' }
}

/**
 * Category types for dynamic dimension display.
 */
export type CategoryType = 'tops' | 'bottoms' | 'dresses' | 'shoes' | 'accessories' | 'other'

/**
 * Mapping of categories to dimension fields to display.
 */
export const categoryDimensions: Record<CategoryType, (keyof ProductFormData)[]> = {
  tops: ['dim1', 'dim2', 'dim3'],           // Poitrine, Longueur, Manches
  bottoms: ['dim4', 'dim5', 'dim6'],        // Taille, Hanches, Entrejambe
  dresses: ['dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim6'],  // Toutes
  shoes: [],                                 // Aucune
  accessories: [],                           // Aucune
  other: ['dim1', 'dim2']                   // Basiques
}

/**
 * Dimension field labels and descriptions.
 */
export const dimensionLabels: Record<string, { label: string; placeholder: string }> = {
  dim1: { label: 'Tour de poitrine', placeholder: 'cm' },
  dim2: { label: 'Longueur totale', placeholder: 'cm' },
  dim3: { label: 'Longueur manches', placeholder: 'cm' },
  dim4: { label: 'Tour de taille', placeholder: 'cm' },
  dim5: { label: 'Tour de hanches', placeholder: 'cm' },
  dim6: { label: 'Entrejambe', placeholder: 'cm' }
}

/**
 * Keywords to detect category type from category name.
 */
export const categoryKeywords: Record<CategoryType, string[]> = {
  tops: ['t-shirt', 'shirt', 'chemise', 'polo', 'pull', 'sweater', 'hoodie', 'sweat', 'veste', 'jacket', 'blazer', 'coat', 'manteau', 'top', 'blouse', 'cardigan'],
  bottoms: ['jean', 'jeans', 'pantalon', 'pants', 'trousers', 'short', 'shorts', 'bermuda', 'jogger', 'legging', 'skirt', 'jupe'],
  dresses: ['robe', 'dress', 'combinaison', 'jumpsuit', 'romper', 'overall', 'salopette'],
  shoes: ['shoe', 'chaussure', 'sneaker', 'basket', 'boot', 'botte', 'sandale', 'sandal', 'mocassin', 'loafer', 'escarpin', 'heel'],
  accessories: ['accessoire', 'accessory', 'sac', 'bag', 'ceinture', 'belt', 'chapeau', 'hat', 'casquette', 'cap', 'écharpe', 'scarf', 'gant', 'glove', 'lunette', 'glasses', 'bijou', 'jewelry', 'montre', 'watch'],
  other: []
}

/**
 * Detect category type from category name.
 */
export function detectCategoryType(categoryName: string): CategoryType {
  const lowerName = categoryName.toLowerCase()

  for (const [type, keywords] of Object.entries(categoryKeywords) as [CategoryType, string[]][]) {
    if (keywords.some(keyword => lowerName.includes(keyword))) {
      return type
    }
  }

  return 'other'
}

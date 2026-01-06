<template>
  <div class="space-y-6">
    <h3 class="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1.5 uppercase tracking-wide">
      <i class="pi pi-tag text-xs" />
      Caractéristiques
    </h3>

    <!-- Required Fields Section -->
    <ProductsFormsCharacteristicsRequiredFieldsSection
      :category="category"
      :brand="brand"
      :gender="gender"
      :condition="condition"
      :size-original="sizeOriginal"
      :size-normalized="sizeNormalized"
      :color="color"
      :material="material"
      :options="{ genders: options.genders, sizes: options.sizes }"
      :suggestions="suggestions"
      :loading="loading"
      :validation="validation"
      @update:category="$emit('update:category', $event)"
      @update:brand="$emit('update:brand', $event)"
      @update:gender="$emit('update:gender', $event)"
      @update:condition="$emit('update:condition', $event)"
      @update:size-original="$emit('update:size-original', $event)"
      @update:size-normalized="$emit('update:size-normalized', $event)"
      @update:color="$emit('update:color', $event)"
      @update:material="$emit('update:material', $event)"
      @search-categories="searchCategories($event.query)"
      @search-brands="searchBrandsAsync($event.query)"
      @search-colors="searchColors($event.query)"
      @search-materials="searchMaterials($event.query)"
    />

    <!-- Clothing Attributes Section -->
    <ProductsFormsCharacteristicsCollapsibleSection
      title="Attributs vêtements"
      icon="pi-palette"
      :filled-count="clothingFilledCount"
    >
      <ProductsFormsCharacteristicsClothingAttributesSection
        :fit="fit"
        :season="season"
        :sport="sport"
        :neckline="neckline"
        :length="length"
        :pattern="pattern"
        :rise="rise"
        :closure="closure"
        :sleeve-length="sleeveLength"
        :options="clothingOptions"
        @update:fit="$emit('update:fit', $event)"
        @update:season="$emit('update:season', $event)"
        @update:sport="$emit('update:sport', $event)"
        @update:neckline="$emit('update:neckline', $event)"
        @update:length="$emit('update:length', $event)"
        @update:pattern="$emit('update:pattern', $event)"
        @update:rise="$emit('update:rise', $event)"
        @update:closure="$emit('update:closure', $event)"
        @update:sleeve-length="$emit('update:sleeveLength', $event)"
      />
    </ProductsFormsCharacteristicsCollapsibleSection>

    <!-- Vintage & Trend Section -->
    <ProductsFormsCharacteristicsCollapsibleSection
      title="Vintage & Tendance"
      icon="pi-clock"
      :filled-count="vintageFilledCount"
    >
      <ProductsFormsCharacteristicsVintageAttributesSection
        :origin="origin"
        :decade="decade"
        :trend="trend"
        :options="vintageOptions"
        @update:origin="$emit('update:origin', $event)"
        @update:decade="$emit('update:decade', $event)"
        @update:trend="$emit('update:trend', $event)"
      />
    </ProductsFormsCharacteristicsCollapsibleSection>

    <!-- Details Section -->
    <ProductsFormsCharacteristicsCollapsibleSection
      title="Détails supplémentaires"
      icon="pi-list"
      :filled-count="detailsFilledCount"
    >
      <ProductsFormsCharacteristicsDetailsSection
        :location="location"
        :model="model"
        :condition-sup="conditionSup"
        :unique-feature="uniqueFeature"
        :marking="marking"
        @update:location="$emit('update:location', $event)"
        @update:model="$emit('update:model', $event)"
        @update:condition-sup="$emit('update:conditionSup', $event)"
        @update:unique-feature="$emit('update:uniqueFeature', $event)"
        @update:marking="$emit('update:marking', $event)"
      />
    </ProductsFormsCharacteristicsCollapsibleSection>
  </div>
</template>

<script setup lang="ts">
interface ValidationObject {
  hasError: (field: string) => boolean
  getError: (field: string) => string
  isFieldValid?: (field: string) => boolean
  touch: (field: string) => void
  validateDebounced?: (field: string, value: string) => void
}

interface Props {
  // Required
  category: string
  brand: string
  condition: number | null
  sizeOriginal: string
  sizeNormalized: string | null
  color: string
  gender: string
  material: string
  // Clothing
  fit: string | null
  season: string | null
  sport: string | null
  neckline: string | null
  length: string | null
  pattern: string | null
  rise: string | null
  closure: string | null
  sleeveLength: string | null
  // Vintage
  origin: string | null
  decade: string | null
  trend: string | null
  // Details
  conditionSup: string[] | null
  location: string | null
  model: string | null
  uniqueFeature: string[] | null
  marking: string | null
  // Validation
  validation?: ValidationObject
}

const props = withDefaults(defineProps<Props>(), {
  validation: undefined
})

defineEmits<{
  'update:category': [value: string]
  'update:brand': [value: string]
  'update:condition': [value: number]
  'update:size-original': [value: string]
  'update:size-normalized': [value: string | null]
  'update:color': [value: string]
  'update:gender': [value: string]
  'update:material': [value: string]
  'update:fit': [value: string | null]
  'update:season': [value: string | null]
  'update:sport': [value: string | null]
  'update:neckline': [value: string | null]
  'update:length': [value: string | null]
  'update:pattern': [value: string | null]
  'update:rise': [value: string | null]
  'update:closure': [value: string | null]
  'update:sleeveLength': [value: string | null]
  'update:origin': [value: string | null]
  'update:decade': [value: string | null]
  'update:trend': [value: string | null]
  'update:conditionSup': [value: string[] | null]
  'update:location': [value: string | null]
  'update:model': [value: string | null]
  'update:uniqueFeature': [value: string[] | null]
  'update:marking': [value: string | null]
}>()

// Use the product attributes composable
const {
  options,
  loading,
  suggestions,
  loadAllAttributes,
  searchCategories,
  searchBrandsAsync,
  searchColors,
  searchMaterials
} = useProductAttributes()

// Computed options for each section
const clothingOptions = computed(() => ({
  fits: options.fits,
  seasons: options.seasons,
  sports: options.sports,
  necklines: options.necklines,
  lengths: options.lengths,
  patterns: options.patterns,
  rises: options.rises,
  closures: options.closures,
  sleeveLengths: options.sleeveLengths
}))

const vintageOptions = computed(() => ({
  origins: options.origins,
  decades: options.decades,
  trends: options.trends
}))

// Computed: count filled clothing attributes
const clothingFilledCount = computed(() => {
  const clothingFields = [
    props.fit, props.season, props.sport, props.neckline,
    props.length, props.pattern, props.rise, props.closure, props.sleeveLength
  ]
  return clothingFields.filter(v => v !== null && v !== undefined && v !== '').length
})

// Computed: count filled vintage attributes
const vintageFilledCount = computed(() => {
  const vintageFields = [props.origin, props.decade, props.trend]
  return vintageFields.filter(v => v !== null && v !== undefined && v !== '').length
})

// Computed: count filled details attributes
const detailsFilledCount = computed(() => {
  const detailsFields = [props.location, props.model, props.marking]
  let count = detailsFields.filter(v => v !== null && v !== undefined && v !== '').length
  if (props.conditionSup && props.conditionSup.length > 0) count++
  if (props.uniqueFeature && props.uniqueFeature.length > 0) count++
  return count
})

// Load attributes on mount
onMounted(() => {
  loadAllAttributes()
})
</script>

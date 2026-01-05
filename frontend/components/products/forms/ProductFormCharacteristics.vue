<template>
  <div class="space-y-6">
    <h3 class="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1.5 uppercase tracking-wide">
      <i class="pi pi-tag text-xs" />
      Caractéristiques
    </h3>

    <!-- ===== ATTRIBUTS OBLIGATOIRES ===== -->
    <div class="bg-gray-50 rounded-lg p-4 space-y-4">
      <h4 class="text-xs font-semibold text-gray-600 uppercase">Obligatoires</h4>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Catégorie -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Catégorie *</label>
          <AutoComplete
            :model-value="category"
            :suggestions="categorySuggestions"
            :min-length="1"
            placeholder="Sélectionner..."
            class="w-full"
            :class="{ 'p-invalid': validation?.hasError('category') }"
            :loading="loadingCategories"
            @update:model-value="$emit('update:category', $event)"
            @complete="handleCategorySearch"
            @blur="validation?.touch('category')"
          />
          <small v-if="validation?.hasError('category')" class="p-error">
            {{ validation?.getError('category') }}
          </small>
        </div>

        <!-- Marque -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Marque *</label>
          <AutoComplete
            :model-value="brand"
            :suggestions="brandSuggestions"
            :min-length="1"
            placeholder="Ex: Nike, Levi's..."
            class="w-full"
            :class="{ 'p-invalid': validation?.hasError('brand') }"
            :loading="loadingBrands"
            @update:model-value="$emit('update:brand', $event)"
            @complete="handleBrandSearch"
            @blur="validation?.touch('brand')"
          />
          <small v-if="validation?.hasError('brand')" class="p-error">
            {{ validation?.getError('brand') }}
          </small>
        </div>

        <!-- Genre -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Genre *</label>
          <Select
            :model-value="gender"
            :options="genderOptions"
            option-label="label"
            option-value="value"
            placeholder="Sélectionner..."
            class="w-full"
            :class="{ 'p-invalid': validation?.hasError('gender') }"
            :loading="loadingGenders"
            @update:model-value="$emit('update:gender', $event)"
            @blur="validation?.touch('gender')"
          />
          <small v-if="validation?.hasError('gender')" class="p-error">
            {{ validation?.getError('gender') }}
          </small>
        </div>
      </div>

      <!-- Condition (Slider pleine largeur) -->
      <ProductsFormsConditionSlider
        :model-value="condition"
        :has-error="validation?.hasError('condition')"
        :error-message="validation?.getError('condition')"
        @update:model-value="$emit('update:condition', $event)"
      />

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Taille -->
        <ProductsFormsSizeAutocomplete
          :model-value="sizeOriginal"
          :has-error="validation?.hasError('size_original')"
          :error-message="validation?.getError('size_original')"
          @update:model-value="$emit('update:sizeOriginal', $event)"
          @update:normalized="$emit('update:sizeNormalized', $event)"
          @blur="validation?.touch('size_original')"
        />

        <!-- Couleur -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Couleur *</label>
          <AutoComplete
            :model-value="color"
            :suggestions="colorSuggestions"
            :min-length="1"
            placeholder="Ex: Bleu, Noir..."
            class="w-full"
            :class="{ 'p-invalid': validation?.hasError('color') }"
            :loading="loadingColors"
            @update:model-value="$emit('update:color', $event)"
            @complete="handleColorSearch"
            @blur="validation?.touch('color')"
          />
          <small v-if="validation?.hasError('color')" class="p-error">
            {{ validation?.getError('color') }}
          </small>
        </div>

        <!-- Matière -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Matière *</label>
          <AutoComplete
            :model-value="material"
            :suggestions="materialSuggestions"
            :min-length="1"
            placeholder="Ex: Coton, Denim..."
            class="w-full"
            :class="{ 'p-invalid': validation?.hasError('material') }"
            :loading="loadingMaterials"
            @update:model-value="$emit('update:material', $event)"
            @complete="handleMaterialSearch"
            @blur="validation?.touch('material')"
          />
          <small v-if="validation?.hasError('material')" class="p-error">
            {{ validation?.getError('material') }}
          </small>
        </div>
      </div>
    </div>

    <!-- ===== ATTRIBUTS VÊTEMENTS (Optionnels) ===== -->
    <div class="border border-gray-200 rounded-lg p-4 space-y-4">
      <div class="flex items-center justify-between cursor-pointer" @click="showClothingAttrs = !showClothingAttrs">
        <h4 class="text-xs font-semibold text-gray-600 uppercase flex items-center gap-2">
          <i class="pi pi-palette text-xs" />
          Attributs vêtements
          <span class="text-gray-400 font-normal">(optionnel)</span>
        </h4>
        <i :class="showClothingAttrs ? 'pi pi-chevron-up' : 'pi pi-chevron-down'" class="text-gray-400" />
      </div>

      <div v-show="showClothingAttrs" class="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
        <!-- Coupe -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Coupe</label>
          <Select
            :model-value="fit"
            :options="fitOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:fit', $event)"
          />
        </div>

        <!-- Saison -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Saison</label>
          <Select
            :model-value="season"
            :options="seasonOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:season', $event)"
          />
        </div>

        <!-- Sport -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Sport</label>
          <Select
            :model-value="sport"
            :options="sportOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:sport', $event)"
          />
        </div>

        <!-- Encolure -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Encolure</label>
          <Select
            :model-value="neckline"
            :options="necklineOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:neckline', $event)"
          />
        </div>

        <!-- Longueur -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Longueur</label>
          <Select
            :model-value="length"
            :options="lengthOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:length', $event)"
          />
        </div>

        <!-- Motif -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Motif</label>
          <Select
            :model-value="pattern"
            :options="patternOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:pattern', $event)"
          />
        </div>

        <!-- Hauteur taille -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Hauteur taille</label>
          <Select
            :model-value="rise"
            :options="riseOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:rise', $event)"
          />
        </div>

        <!-- Fermeture -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Fermeture</label>
          <Select
            :model-value="closure"
            :options="closureOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:closure', $event)"
          />
        </div>

        <!-- Longueur manches -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Manches</label>
          <Select
            :model-value="sleeveLength"
            :options="sleeveLengthOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:sleeveLength', $event)"
          />
        </div>
      </div>
    </div>

    <!-- ===== VINTAGE & TENDANCE (Optionnels) ===== -->
    <div class="border border-gray-200 rounded-lg p-4 space-y-4">
      <div class="flex items-center justify-between cursor-pointer" @click="showVintageAttrs = !showVintageAttrs">
        <h4 class="text-xs font-semibold text-gray-600 uppercase flex items-center gap-2">
          <i class="pi pi-clock text-xs" />
          Vintage & Tendance
          <span class="text-gray-400 font-normal">(optionnel)</span>
        </h4>
        <i :class="showVintageAttrs ? 'pi pi-chevron-up' : 'pi pi-chevron-down'" class="text-gray-400" />
      </div>

      <div v-show="showVintageAttrs" class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <!-- Origine -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Origine</label>
          <Select
            :model-value="origin"
            :options="originOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:origin', $event)"
          />
        </div>

        <!-- Décennie -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Décennie</label>
          <Select
            :model-value="decade"
            :options="decadeOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:decade', $event)"
          />
        </div>

        <!-- Tendance -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Tendance</label>
          <Select
            :model-value="trend"
            :options="trendOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:trend', $event)"
          />
        </div>
      </div>
    </div>

    <!-- ===== DÉTAILS (Optionnels) ===== -->
    <div class="border border-gray-200 rounded-lg p-4 space-y-4">
      <div class="flex items-center justify-between cursor-pointer" @click="showDetailsAttrs = !showDetailsAttrs">
        <h4 class="text-xs font-semibold text-gray-600 uppercase flex items-center gap-2">
          <i class="pi pi-list text-xs" />
          Détails supplémentaires
          <span class="text-gray-400 font-normal">(optionnel)</span>
        </h4>
        <i :class="showDetailsAttrs ? 'pi pi-chevron-up' : 'pi pi-chevron-down'" class="text-gray-400" />
      </div>

      <div v-show="showDetailsAttrs" class="space-y-4 pt-2">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Emplacement -->
          <div>
            <label class="block text-xs font-semibold mb-1 text-secondary-900">Emplacement</label>
            <InputText
              :model-value="location"
              placeholder="Ex: Étagère A3, Carton 5..."
              class="w-full"
              @update:model-value="$emit('update:location', $event)"
            />
          </div>

          <!-- Référence modèle -->
          <div>
            <label class="block text-xs font-semibold mb-1 text-secondary-900">Référence modèle</label>
            <InputText
              :model-value="model"
              placeholder="Ex: 501-0115, Air Max 90..."
              class="w-full"
              @update:model-value="$emit('update:model', $event)"
            />
          </div>
        </div>

        <!-- Détails état -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Détails état</label>
          <Chips
            :model-value="conditionSup || []"
            placeholder="Ex: Tache légère, Bouton manquant... (Entrée pour ajouter)"
            class="w-full"
            @update:model-value="$emit('update:conditionSup', $event)"
          />
          <small class="text-xs text-gray-500">Appuyez sur Entrée pour ajouter un détail</small>
        </div>

        <!-- Features uniques -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Features uniques</label>
          <Chips
            :model-value="uniqueFeature || []"
            placeholder="Ex: Vintage, Logo brodé, Pièce rare... (Entrée pour ajouter)"
            class="w-full"
            @update:model-value="$emit('update:uniqueFeature', $event)"
          />
        </div>

        <!-- Marquages -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Marquages visibles</label>
          <Textarea
            :model-value="marking"
            placeholder="Dates, codes, textes visibles sur le produit..."
            rows="2"
            class="w-full"
            @update:model-value="$emit('update:marking', $event)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import type { AttributeOption } from '~/composables/useAttributes'
import { useLocaleStore } from '~/stores/locale'

interface Props {
  // Obligatoires
  category: string
  brand: string
  condition: number | null
  sizeOriginal: string
  sizeNormalized: string | null
  color: string
  gender: string
  material: string
  // Vêtements
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
  // Détails
  conditionSup: string[] | null
  location: string | null
  model: string | null
  uniqueFeature: string[] | null
  marking: string | null
  // Validation
  validation?: any
}

withDefaults(defineProps<Props>(), {
  validation: undefined
})

defineEmits<{
  'update:category': [value: string]
  'update:brand': [value: string]
  'update:condition': [value: number]
  'update:sizeOriginal': [value: string]
  'update:sizeNormalized': [value: string | null]
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

// État des sections repliables
const showClothingAttrs = ref(false)
const showVintageAttrs = ref(false)
const showDetailsAttrs = ref(false)

// Composables
const localeStore = useLocaleStore()
const { fetchAttribute, searchBrands } = useAttributes()

// États de chargement
const loadingCategories = ref(false)
const loadingBrands = ref(false)
const loadingColors = ref(false)
const loadingMaterials = ref(false)
const loadingGenders = ref(false)

// Données pour les dropdowns
const genderOptions = ref<AttributeOption[]>([])
const fitOptions = ref<AttributeOption[]>([])
const seasonOptions = ref<AttributeOption[]>([])
const sportOptions = ref<AttributeOption[]>([])
const necklineOptions = ref<AttributeOption[]>([])
const lengthOptions = ref<AttributeOption[]>([])
const patternOptions = ref<AttributeOption[]>([])
const riseOptions = ref<AttributeOption[]>([])
const closureOptions = ref<AttributeOption[]>([])
const sleeveLengthOptions = ref<AttributeOption[]>([])
const originOptions = ref<AttributeOption[]>([])
const decadeOptions = ref<AttributeOption[]>([])
const trendOptions = ref<AttributeOption[]>([])

// Suggestions pour autocomplete
const categorySuggestions = ref<string[]>([])
const brandSuggestions = ref<string[]>([])
const colorSuggestions = ref<string[]>([])
const materialSuggestions = ref<string[]>([])

// Données brutes
const allCategories = ref<AttributeOption[]>([])
const allColors = ref<AttributeOption[]>([])
const allMaterials = ref<AttributeOption[]>([])

// Charger les attributs
const loadAttributes = async () => {
  const lang = localeStore.locale

  // Charger en parallèle
  const [
    genders, fits, seasons, sports, necklines, lengths,
    patterns, rises, closures, sleeves, origins, decades, trends,
    categories, colors, materials
  ] = await Promise.all([
    fetchAttribute('genders', lang),
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

  genderOptions.value = genders
  fitOptions.value = fits
  seasonOptions.value = seasons
  sportOptions.value = sports
  necklineOptions.value = necklines
  lengthOptions.value = lengths
  patternOptions.value = patterns
  riseOptions.value = rises
  closureOptions.value = closures
  sleeveLengthOptions.value = sleeves
  originOptions.value = origins
  decadeOptions.value = decades
  trendOptions.value = trends
  allCategories.value = categories
  allColors.value = colors
  allMaterials.value = materials
}

onMounted(() => {
  loadAttributes()
})

watch(() => localeStore.locale, () => {
  loadAttributes()
})

// Handlers de recherche
const handleCategorySearch = (event: { query: string }) => {
  const query = event.query.toLowerCase()
  categorySuggestions.value = allCategories.value
    .filter(c => c.label.toLowerCase().includes(query))
    .map(c => c.label)
    .slice(0, 10)
}

const handleBrandSearch = async (event: { query: string }) => {
  loadingBrands.value = true
  try {
    const results = await searchBrands(event.query)
    brandSuggestions.value = results.map(b => b.label)
  } finally {
    loadingBrands.value = false
  }
}

const handleColorSearch = (event: { query: string }) => {
  const query = event.query.toLowerCase()
  colorSuggestions.value = allColors.value
    .filter(c => c.label.toLowerCase().includes(query))
    .map(c => c.label)
    .slice(0, 10)
}

const handleMaterialSearch = (event: { query: string }) => {
  const query = event.query.toLowerCase()
  materialSuggestions.value = allMaterials.value
    .filter(m => m.label.toLowerCase().includes(query))
    .map(m => m.label)
    .slice(0, 10)
}
</script>

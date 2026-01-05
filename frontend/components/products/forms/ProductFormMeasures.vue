<template>
  <div class="space-y-6">
    <h3 class="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1.5 uppercase tracking-wide">
      <i class="pi pi-arrows-alt text-xs" />
      Mesures & Tarification
    </h3>

    <!-- ===== DIMENSIONS ===== -->
    <div class="bg-gray-50 rounded-lg p-4 space-y-4">
      <h4 class="text-xs font-semibold text-gray-600 uppercase flex items-center gap-2">
        <i class="pi pi-rulers text-xs" />
        Dimensions (en cm)
        <span v-if="categoryType !== 'other'" class="text-gray-400 font-normal">
          - {{ categoryTypeLabel }}
        </span>
      </h4>

      <!-- Message si pas de dimensions pour cette catégorie -->
      <div v-if="visibleDimensions.length === 0" class="text-sm text-gray-500 italic">
        Pas de dimensions nécessaires pour cette catégorie.
      </div>

      <!-- Grille de dimensions -->
      <div v-else class="grid grid-cols-2 md:grid-cols-3 gap-4">
        <!-- Dim1: Poitrine -->
        <div v-if="visibleDimensions.includes('dim1')">
          <label class="block text-xs font-semibold mb-1 text-secondary-900">
            {{ dimensionLabels.dim1.label }}
          </label>
          <InputNumber
            :model-value="dim1"
            class="w-full"
            :min="0"
            :max="300"
            suffix=" cm"
            placeholder="cm"
            @update:model-value="$emit('update:dim1', $event)"
          />
        </div>

        <!-- Dim2: Longueur totale -->
        <div v-if="visibleDimensions.includes('dim2')">
          <label class="block text-xs font-semibold mb-1 text-secondary-900">
            {{ dimensionLabels.dim2.label }}
          </label>
          <InputNumber
            :model-value="dim2"
            class="w-full"
            :min="0"
            :max="300"
            suffix=" cm"
            placeholder="cm"
            @update:model-value="$emit('update:dim2', $event)"
          />
        </div>

        <!-- Dim3: Manches -->
        <div v-if="visibleDimensions.includes('dim3')">
          <label class="block text-xs font-semibold mb-1 text-secondary-900">
            {{ dimensionLabels.dim3.label }}
          </label>
          <InputNumber
            :model-value="dim3"
            class="w-full"
            :min="0"
            :max="150"
            suffix=" cm"
            placeholder="cm"
            @update:model-value="$emit('update:dim3', $event)"
          />
        </div>

        <!-- Dim4: Taille -->
        <div v-if="visibleDimensions.includes('dim4')">
          <label class="block text-xs font-semibold mb-1 text-secondary-900">
            {{ dimensionLabels.dim4.label }}
          </label>
          <InputNumber
            :model-value="dim4"
            class="w-full"
            :min="0"
            :max="200"
            suffix=" cm"
            placeholder="cm"
            @update:model-value="$emit('update:dim4', $event)"
          />
        </div>

        <!-- Dim5: Hanches -->
        <div v-if="visibleDimensions.includes('dim5')">
          <label class="block text-xs font-semibold mb-1 text-secondary-900">
            {{ dimensionLabels.dim5.label }}
          </label>
          <InputNumber
            :model-value="dim5"
            class="w-full"
            :min="0"
            :max="200"
            suffix=" cm"
            placeholder="cm"
            @update:model-value="$emit('update:dim5', $event)"
          />
        </div>

        <!-- Dim6: Entrejambe -->
        <div v-if="visibleDimensions.includes('dim6')">
          <label class="block text-xs font-semibold mb-1 text-secondary-900">
            {{ dimensionLabels.dim6.label }}
          </label>
          <InputNumber
            :model-value="dim6"
            class="w-full"
            :min="0"
            :max="150"
            suffix=" cm"
            placeholder="cm"
            @update:model-value="$emit('update:dim6', $event)"
          />
        </div>
      </div>

      <!-- Taille suggérée -->
      <div v-if="suggestedSize" class="flex items-center gap-2 p-2 bg-green-50 rounded-md">
        <i class="pi pi-lightbulb text-green-600" />
        <span class="text-sm text-green-700">
          Taille suggérée : <strong>{{ suggestedSize }}</strong>
        </span>
      </div>
    </div>

    <!-- ===== TARIFICATION ===== -->
    <div class="border border-gray-200 rounded-lg p-4 space-y-4">
      <h4 class="text-xs font-semibold text-gray-600 uppercase flex items-center gap-2">
        <i class="pi pi-euro text-xs" />
        Tarification
        <span class="text-gray-400 font-normal">(pour calcul automatique du prix)</span>
      </h4>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Rareté -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Rareté</label>
          <Select
            :model-value="pricingRarity"
            :options="rarityOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:pricingRarity', $event)"
          />
        </div>

        <!-- Qualité -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Qualité</label>
          <Select
            :model-value="pricingQuality"
            :options="qualityOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:pricingQuality', $event)"
          />
        </div>

        <!-- Style -->
        <div>
          <label class="block text-xs font-semibold mb-1 text-secondary-900">Style</label>
          <Select
            :model-value="pricingStyle"
            :options="styleOptions"
            option-label="label"
            option-value="value"
            placeholder="..."
            class="w-full"
            show-clear
            @update:model-value="$emit('update:pricingStyle', $event)"
          />
        </div>
      </div>

      <!-- Détails prix -->
      <div>
        <label class="block text-xs font-semibold mb-1 text-secondary-900">Détails prix</label>
        <InputText
          :model-value="pricingDetails"
          placeholder="Informations supplémentaires pour le calcul du prix..."
          class="w-full"
          @update:model-value="$emit('update:pricingDetails', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  type CategoryType,
  categoryDimensions,
  dimensionLabels,
  detectCategoryType
} from '~/types/product'

interface Props {
  // Catégorie (pour dimensions dynamiques)
  category: string
  // Dimensions
  dim1: number | null
  dim2: number | null
  dim3: number | null
  dim4: number | null
  dim5: number | null
  dim6: number | null
  // Pricing
  pricingRarity: string | null
  pricingQuality: string | null
  pricingStyle: string | null
  pricingDetails: string | null
}

const props = defineProps<Props>()

defineEmits<{
  'update:dim1': [value: number | null]
  'update:dim2': [value: number | null]
  'update:dim3': [value: number | null]
  'update:dim4': [value: number | null]
  'update:dim5': [value: number | null]
  'update:dim6': [value: number | null]
  'update:pricingRarity': [value: string | null]
  'update:pricingQuality': [value: string | null]
  'update:pricingStyle': [value: string | null]
  'update:pricingDetails': [value: string | null]
}>()

// Détecter le type de catégorie
const categoryType = computed<CategoryType>(() => {
  if (!props.category) return 'other'
  return detectCategoryType(props.category)
})

// Label du type de catégorie
const categoryTypeLabel = computed(() => {
  const labels: Record<CategoryType, string> = {
    tops: 'Haut',
    bottoms: 'Bas',
    dresses: 'Robe/Combinaison',
    shoes: 'Chaussures',
    accessories: 'Accessoires',
    other: 'Autre'
  }
  return labels[categoryType.value]
})

// Dimensions visibles selon la catégorie
const visibleDimensions = computed(() => {
  return categoryDimensions[categoryType.value] as string[]
})

// Calcul de la taille suggérée basée sur les dimensions
const suggestedSize = computed(() => {
  // Pour les hauts: basé sur dim1 (poitrine)
  if (categoryType.value === 'tops' && props.dim1) {
    if (props.dim1 < 88) return 'XS'
    if (props.dim1 < 96) return 'S'
    if (props.dim1 < 104) return 'M'
    if (props.dim1 < 112) return 'L'
    if (props.dim1 < 120) return 'XL'
    return 'XXL'
  }

  // Pour les bas: basé sur dim4 (taille) et dim6 (entrejambe)
  if (categoryType.value === 'bottoms') {
    if (props.dim4 && props.dim6) {
      const waist = Math.round(props.dim4 / 2.54) // Convertir en inches
      return `W${waist}/L${Math.round(props.dim6 / 2.54)}`
    }
    if (props.dim4) {
      if (props.dim4 < 68) return 'XS'
      if (props.dim4 < 76) return 'S'
      if (props.dim4 < 84) return 'M'
      if (props.dim4 < 92) return 'L'
      if (props.dim4 < 100) return 'XL'
      return 'XXL'
    }
  }

  // Pour les robes: combinaison
  if (categoryType.value === 'dresses' && props.dim1) {
    if (props.dim1 < 88) return 'XS'
    if (props.dim1 < 96) return 'S'
    if (props.dim1 < 104) return 'M'
    if (props.dim1 < 112) return 'L'
    if (props.dim1 < 120) return 'XL'
    return 'XXL'
  }

  return null
})

// Options pour les dropdowns de pricing
const rarityOptions = [
  { label: 'Commun', value: 'common' },
  { label: 'Peu courant', value: 'uncommon' },
  { label: 'Rare', value: 'rare' },
  { label: 'Très rare', value: 'very_rare' },
  { label: 'Exceptionnel', value: 'exceptional' }
]

const qualityOptions = [
  { label: 'Basique', value: 'basic' },
  { label: 'Standard', value: 'standard' },
  { label: 'Premium', value: 'premium' },
  { label: 'Luxe', value: 'luxury' },
  { label: 'Haute couture', value: 'haute_couture' }
]

const styleOptions = [
  { label: 'Casual', value: 'casual' },
  { label: 'Streetwear', value: 'streetwear' },
  { label: 'Vintage', value: 'vintage' },
  { label: 'Sportswear', value: 'sportswear' },
  { label: 'Formel', value: 'formal' },
  { label: 'Bohème', value: 'bohemian' },
  { label: 'Minimaliste', value: 'minimalist' }
]
</script>

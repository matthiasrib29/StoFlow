<template>
  <div class="form-subsection-spacing">
    <h3 class="form-section-title">
      <i class="pi pi-arrows-alt" />
      Mesures
    </h3>

    <!-- ===== DIMENSIONS ===== -->
    <div class="bg-gray-50 rounded-lg p-4 form-field-spacing">
      <h4 class="text-xs font-semibold text-gray-600 uppercase flex items-center gap-2">
        <i class="pi pi-rulers text-xs" />
        Dimensions (en cm)
      </h4>

      <!-- Grille de dimensions -->
      <div class="grid grid-cols-2 md:grid-cols-3 form-grid-spacing">
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

      <!-- Shortened detection alert -->
      <div v-if="isLikelyShortened" class="flex items-center gap-2 p-2 bg-amber-50 rounded-md">
        <i class="pi pi-exclamation-triangle text-amber-600" />
        <span class="text-sm text-amber-700">
          Entrejambe court ({{ dim6 }} cm) — potentiellement raccourci
        </span>
        <button
          type="button"
          class="ml-auto text-xs font-medium px-2.5 py-1 rounded-md bg-amber-100 text-amber-800 hover:bg-amber-200 transition-colors"
          @click="emit('add:conditionSup', 'Hemmed/shortened')"
        >
          + Ajouter raccourci
        </button>
      </div>

      <!-- Confirmation after adding -->
      <div v-else-if="alreadyMarkedShortened && isFullLengthBottoms && dim6 && dim6 < SHORTENED_THRESHOLD_CM" class="flex items-center gap-2 p-2 bg-green-50 rounded-md">
        <i class="pi pi-check-circle text-green-600" />
        <span class="text-sm text-green-700">Marqué comme raccourci</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import {
  type CategoryType,
  categoryDimensions,
  dimensionLabels,
  detectCategoryType
} from '~/types/product'

interface Props {
  // Catégorie (pour dimensions dynamiques)
  category: string
  // Condition supplémentaire (pour détection raccourci)
  conditionSup: string[] | null
  // Dimensions
  dim1: number | null
  dim2: number | null
  dim3: number | null
  dim4: number | null
  dim5: number | null
  dim6: number | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:dim1': [value: number | null]
  'update:dim2': [value: number | null]
  'update:dim3': [value: number | null]
  'update:dim4': [value: number | null]
  'update:dim5': [value: number | null]
  'update:dim6': [value: number | null]
  'update:suggestedSize': [value: string | null]
  'add:conditionSup': [value: string]
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

// Toujours afficher les 6 dimensions
const visibleDimensions = computed(() => {
  return ['dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim6']
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

  // Pour les bas: basé sur dim1 (taille à plat + 1cm marge, × 2) et dim6 (entrejambe)
  // W arrondi à l'inférieur, L arrondi au supérieur (mieux trop grand que trop petit)
  if (categoryType.value === 'bottoms') {
    const fullWaist = props.dim1 ? (props.dim1 + 1) * 2 : null
    if (fullWaist && props.dim6) {
      const waist = Math.floor(fullWaist / 2.54)
      return `W${waist}/L${Math.ceil(props.dim6 / 2.54)}`
    }
    if (fullWaist) {
      if (fullWaist < 68) return 'XS'
      if (fullWaist < 76) return 'S'
      if (fullWaist < 84) return 'M'
      if (fullWaist < 92) return 'L'
      if (fullWaist < 100) return 'XL'
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

// Shortened detection for full-length bottoms
const FULL_LENGTH_KEYWORDS = ['jean', 'jeans', 'pantalon', 'pants', 'trousers', 'jogger']
const SHORTENED_THRESHOLD_CM = 70

const isFullLengthBottoms = computed(() => {
  if (categoryType.value !== 'bottoms' || !props.category) return false
  const lower = props.category.toLowerCase()
  return FULL_LENGTH_KEYWORDS.some(kw => lower.includes(kw))
})

const isLikelyShortened = computed(() => {
  if (!isFullLengthBottoms.value || !props.dim6) return false
  if (props.dim6 >= SHORTENED_THRESHOLD_CM) return false
  if (props.conditionSup?.includes('Hemmed/shortened')) return false
  return true
})

const alreadyMarkedShortened = computed(() => {
  return props.conditionSup?.includes('Hemmed/shortened') ?? false
})

// Emit suggestedSize to parent whenever it changes
watch(suggestedSize, (newVal) => {
  emit('update:suggestedSize', newVal)
}, { immediate: true })
</script>

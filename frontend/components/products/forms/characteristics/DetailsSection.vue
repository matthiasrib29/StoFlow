<template>
  <div class="space-y-4">
    <!-- Location (full width since model moved to required section) -->
    <ProductsFormsCharacteristicsAttributeField
      type="text"
      label="Emplacement"
      :model-value="location"
      placeholder="Ex: Étagère A3, Carton 5..."
      required
      @update:model-value="$emit('update:location', $event)"
    />

    <!-- Condition Details -->
    <ProductsFormsCharacteristicsAttributeField
      type="multiselect"
      label="Détails état"
      :model-value="filteredConditionSup"
      :options="options.conditionSups"
      placeholder="Sélectionner les détails d'état"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:conditionSup', $event)"
    />

    <!-- Unique Features -->
    <ProductsFormsCharacteristicsAttributeField
      type="multiselect"
      label="Caractéristiques uniques"
      :model-value="filteredUniqueFeature"
      :options="options.uniqueFeatures"
      placeholder="Sélectionner les caractéristiques"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:uniqueFeature', $event)"
    />

    <!-- Markings -->
    <ProductsFormsCharacteristicsAttributeField
      type="textarea"
      label="Marquages visibles"
      :model-value="marking"
      placeholder="Dates, codes, textes visibles sur le produit..."
      :rows="2"
      @update:model-value="$emit('update:marking', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import type { AttributeOption } from '~/composables/useAttributes'

interface Props {
  location: string | null
  conditionSup: string[] | null
  uniqueFeature: string[] | null
  marking: string | null
  options: {
    conditionSups: AttributeOption[]
    uniqueFeatures: AttributeOption[]
  }
}

const props = defineProps<Props>()

defineEmits<{
  'update:location': [value: string | null]
  'update:conditionSup': [value: string[] | null]
  'update:uniqueFeature': [value: string[] | null]
  'update:marking': [value: string | null]
}>()

// Filter out old free-text values that don't match any predefined option
const filteredConditionSup = computed(() => {
  if (!props.conditionSup || props.options.conditionSups.length === 0) return props.conditionSup
  const validValues = new Set(props.options.conditionSups.map(o => o.value))
  return props.conditionSup.filter(v => validValues.has(v))
})

const filteredUniqueFeature = computed(() => {
  if (!props.uniqueFeature || props.options.uniqueFeatures.length === 0) return props.uniqueFeature
  const validValues = new Set(props.options.uniqueFeatures.map(o => o.value))
  return props.uniqueFeature.filter(v => validValues.has(v))
})
</script>

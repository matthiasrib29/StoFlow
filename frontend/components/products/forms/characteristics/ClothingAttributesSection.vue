<template>
  <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
    <!-- Fit -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Coupe"
      :model-value="fit"
      :options="options.fits"
      @update:model-value="$emit('update:fit', $event)"
    />

    <!-- Season -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Saison"
      :model-value="season"
      :options="options.seasons"
      @update:model-value="$emit('update:season', $event)"
    />

    <!-- Sport -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Sport"
      :model-value="sport"
      :options="options.sports"
      @update:model-value="$emit('update:sport', $event)"
    />

    <!-- Neckline -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Encolure"
      :model-value="neckline"
      :options="options.necklines"
      @update:model-value="$emit('update:neckline', $event)"
    />

    <!-- Length -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Longueur"
      :model-value="length"
      :options="options.lengths"
      @update:model-value="$emit('update:length', $event)"
    />

    <!-- Pattern -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Motif"
      :model-value="pattern"
      :options="options.patterns"
      @update:model-value="$emit('update:pattern', $event)"
    />

    <!-- Rise -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Hauteur taille"
      :model-value="rise"
      :options="options.rises"
      @update:model-value="$emit('update:rise', $event)"
    />

    <!-- Closure -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Fermeture"
      :model-value="closure"
      :options="options.closures"
      @update:model-value="$emit('update:closure', $event)"
    />

    <!-- Sleeve Length -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Manches"
      :model-value="sleeveLength"
      :options="options.sleeveLengths"
      @update:model-value="$emit('update:sleeveLength', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import type { AttributeOption } from '~/composables/useAttributes'

interface Props {
  fit: string | null
  season: string | null
  sport: string | null
  neckline: string | null
  length: string | null
  pattern: string | null
  rise: string | null
  closure: string | null
  sleeveLength: string | null
  options: {
    fits: AttributeOption[]
    seasons: AttributeOption[]
    sports: AttributeOption[]
    necklines: AttributeOption[]
    lengths: AttributeOption[]
    patterns: AttributeOption[]
    rises: AttributeOption[]
    closures: AttributeOption[]
    sleeveLengths: AttributeOption[]
  }
}

defineProps<Props>()

defineEmits<{
  'update:fit': [value: string | string[] | null]
  'update:season': [value: string | string[] | null]
  'update:sport': [value: string | string[] | null]
  'update:neckline': [value: string | string[] | null]
  'update:length': [value: string | string[] | null]
  'update:pattern': [value: string | string[] | null]
  'update:rise': [value: string | string[] | null]
  'update:closure': [value: string | string[] | null]
  'update:sleeveLength': [value: string | string[] | null]
}>()
</script>

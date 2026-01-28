<template>
  <UiFormSection :columns="4" variant="flat" spacing="tight">
    <!-- Fit -->
    <ProductsFormsCharacteristicsAttributeField
      v-if="isVisible('fit')"
      type="select"
      label="Coupe"
      :model-value="fit"
      :options="options.fits"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:fit', $event)"
    />

    <!-- Season -->
    <ProductsFormsCharacteristicsAttributeField
      v-if="isVisible('season')"
      type="select"
      label="Saison"
      :model-value="season"
      :options="options.seasons"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:season', $event)"
    />

    <!-- Sport -->
    <ProductsFormsCharacteristicsAttributeField
      v-if="isVisible('sport')"
      type="select"
      label="Sport"
      :model-value="sport"
      :options="options.sports"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:sport', $event)"
    />

    <!-- Neckline -->
    <ProductsFormsCharacteristicsAttributeField
      v-if="isVisible('neckline')"
      type="select"
      label="Encolure"
      :model-value="neckline"
      :options="options.necklines"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:neckline', $event)"
    />

    <!-- Length -->
    <ProductsFormsCharacteristicsAttributeField
      v-if="isVisible('length')"
      type="select"
      label="Longueur"
      :model-value="length"
      :options="options.lengths"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:length', $event)"
    />

    <!-- Pattern -->
    <ProductsFormsCharacteristicsAttributeField
      v-if="isVisible('pattern')"
      type="select"
      label="Motif"
      :model-value="pattern"
      :options="options.patterns"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:pattern', $event)"
    />

    <!-- Rise -->
    <ProductsFormsCharacteristicsAttributeField
      v-if="isVisible('rise')"
      type="select"
      label="Hauteur taille"
      :model-value="rise"
      :options="options.rises"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:rise', $event)"
    />

    <!-- Closure -->
    <ProductsFormsCharacteristicsAttributeField
      v-if="isVisible('closure')"
      type="select"
      label="Fermeture"
      :model-value="closure"
      :options="options.closures"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:closure', $event)"
    />

    <!-- Sleeve Length -->
    <ProductsFormsCharacteristicsAttributeField
      v-if="isVisible('sleeve_length')"
      type="select"
      label="Manches"
      :model-value="sleeveLength"
      :options="options.sleeveLengths"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:sleeveLength', $event)"
    />

    <!-- Stretch -->
    <ProductsFormsCharacteristicsAttributeField
      v-if="isVisible('stretch')"
      type="select"
      label="Élasticité"
      :model-value="stretch"
      :options="options.stretches"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:stretch', $event)"
    />

    <!-- Lining -->
    <ProductsFormsCharacteristicsAttributeField
      v-if="isVisible('lining')"
      type="select"
      label="Doublure"
      :model-value="lining"
      :options="options.linings"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:lining', $event)"
    />
  </UiFormSection>
</template>

<script setup lang="ts">
import type { AttributeOption } from '~/composables/useAttributes'

const ALL_CLOTHING_ATTRS = [
  'fit', 'season', 'sport', 'neckline', 'length',
  'pattern', 'rise', 'closure', 'sleeve_length', 'stretch', 'lining'
]

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
  stretch: string | null
  lining: string | null
  visibleAttributes?: string[]
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
    stretches: AttributeOption[]
    linings: AttributeOption[]
  }
}

const props = withDefaults(defineProps<Props>(), {
  visibleAttributes: () => ALL_CLOTHING_ATTRS
})

const isVisible = (attr: string): boolean => {
  return props.visibleAttributes.includes(attr)
}

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
  'update:stretch': [value: string | string[] | null]
  'update:lining': [value: string | string[] | null]
}>()
</script>

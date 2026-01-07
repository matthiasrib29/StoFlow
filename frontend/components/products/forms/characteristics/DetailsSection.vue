<template>
  <div class="space-y-4">
    <!-- Location (full width since model moved to required section) -->
    <ProductsFormsCharacteristicsAttributeField
      type="text"
      label="Emplacement"
      :model-value="location"
      placeholder="Ex: Étagère A3, Carton 5..."
      @update:model-value="$emit('update:location', $event)"
    />

    <!-- Condition Details -->
    <ProductsFormsCharacteristicsAttributeField
      type="chips"
      label="Détails état"
      :model-value="conditionSup"
      placeholder="Ex: Tache légère, Bouton manquant... (Entrée pour ajouter)"
      helper-text="Appuyez sur Entrée pour ajouter un détail"
      @update:model-value="$emit('update:conditionSup', $event)"
    />

    <!-- Unique Features -->
    <ProductsFormsCharacteristicsAttributeField
      type="chips"
      label="Features uniques"
      :model-value="uniqueFeature"
      placeholder="Ex: Vintage, Logo brodé, Pièce rare... (Entrée pour ajouter)"
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
interface Props {
  location: string | null
  // model removed - moved to required section
  conditionSup: string[] | null
  uniqueFeature: string[] | null
  marking: string | null
}

defineProps<Props>()

defineEmits<{
  'update:location': [value: string | null]
  // 'update:model' removed - moved to required section
  'update:conditionSup': [value: string[] | null]
  'update:uniqueFeature': [value: string[] | null]
  'update:marking': [value: string | null]
}>()
</script>

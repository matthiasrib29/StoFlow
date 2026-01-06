<template>
  <div class="space-y-4">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Location -->
      <ProductsFormsCharacteristicsAttributeField
        type="text"
        label="Emplacement"
        :model-value="location"
        placeholder="Ex: Étagère A3, Carton 5..."
        @update:model-value="$emit('update:location', $event)"
      />

      <!-- Model Reference -->
      <ProductsFormsCharacteristicsAttributeField
        type="text"
        label="Référence modèle"
        :model-value="model"
        placeholder="Ex: 501-0115, Air Max 90..."
        @update:model-value="$emit('update:model', $event)"
      />
    </div>

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
  model: string | null
  conditionSup: string[] | null
  uniqueFeature: string[] | null
  marking: string | null
}

defineProps<Props>()

defineEmits<{
  'update:location': [value: string | null]
  'update:model': [value: string | null]
  'update:conditionSup': [value: string[] | null]
  'update:uniqueFeature': [value: string[] | null]
  'update:marking': [value: string | null]
}>()
</script>

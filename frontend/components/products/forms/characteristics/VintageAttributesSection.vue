<template>
  <UiFormSection :columns="3" variant="flat">
    <!-- Origin -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Origine"
      :model-value="origin"
      :options="options.origins"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:origin', $event)"
    />

    <!-- Decade -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Décennie"
      :model-value="decade"
      :options="options.decades"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:decade', $event)"
    />

    <!-- Trend -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Tendance"
      :model-value="trend"
      :options="options.trends"
      filter-mode="local"
      filter-placeholder="Rechercher..."
      @update:model-value="$emit('update:trend', $event)"
    />
  </UiFormSection>
</template>

<script setup lang="ts">
import type { AttributeOption } from '~/composables/useAttributes'

interface Props {
  origin: string | null
  decade: string | null
  trend: string | null
  options: {
    origins: AttributeOption[]
    decades: AttributeOption[]
    trends: AttributeOption[]
  }
}

defineProps<Props>()

defineEmits<{
  'update:origin': [value: string | null]
  'update:decade': [value: string | null]
  'update:trend': [value: string | null]
}>()
</script>

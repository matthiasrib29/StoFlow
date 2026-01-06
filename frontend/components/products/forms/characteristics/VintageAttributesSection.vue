<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <!-- Origin -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Origine"
      :model-value="origin"
      :options="options.origins"
      @update:model-value="$emit('update:origin', $event)"
    />

    <!-- Decade -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Décennie"
      :model-value="decade"
      :options="options.decades"
      @update:model-value="$emit('update:decade', $event)"
    />

    <!-- Trend -->
    <ProductsFormsCharacteristicsAttributeField
      type="select"
      label="Tendance"
      :model-value="trend"
      :options="options.trends"
      @update:model-value="$emit('update:trend', $event)"
    />
  </div>
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

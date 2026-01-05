<template>
  <div class="space-y-4">
    <h3 class="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1.5 uppercase tracking-wide">
      <i class="pi pi-tag text-xs"/>
      Attributs obligatoires
    </h3>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Brand -->
      <div>
        <label for="brand" class="block text-xs font-semibold mb-1 text-secondary-900">
          Marque *
        </label>
        <AutoComplete
          id="brand"
          :model-value="brand"
          :suggestions="brandSuggestions"
          placeholder="Ex: Levi's, Nike, Zara..."
          class="w-full"
          :class="{ 'p-invalid': validation.hasError('brand') }"
          required
          :min-length="1"
          :delay="50"
          @update:model-value="$emit('update:brand', $event)"
          @blur="validation.touch('brand')"
          @complete="$emit('search-brand', $event)"
        />
        <small v-if="validation.hasError('brand')" class="p-error">
          {{ validation.getError('brand') }}
        </small>
      </div>

      <!-- Category -->
      <div>
        <label for="category" class="block text-xs font-semibold mb-1 text-secondary-900">
          Catégorie *
        </label>
        <Select
          id="category"
          :model-value="category"
          :options="categories"
          option-label="label"
          option-value="value"
          placeholder="Sélectionner une catégorie"
          class="w-full"
          :class="{ 'p-invalid': validation.hasError('category') }"
          required
          :loading="loadingCategories"
          @update:model-value="$emit('update:category', $event)"
          @blur="validation.touch('category')"
        />
        <small v-if="validation.hasError('category')" class="p-error">
          {{ validation.getError('category') }}
        </small>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AttributeOption } from '~/composables/useAttributes'

defineProps<{
  brand: string
  category: string
  categories: AttributeOption[]
  brandSuggestions: string[]
  loadingCategories: boolean
  validation: any
}>()

defineEmits<{
  'update:brand': [value: string]
  'update:category': [value: string]
  'search-brand': [event: { query: string }]
}>()
</script>

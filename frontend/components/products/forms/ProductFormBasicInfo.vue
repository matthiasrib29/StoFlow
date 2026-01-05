<template>
  <div class="space-y-4">
    <h3 class="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1.5 uppercase tracking-wide">
      <i class="pi pi-info-circle text-xs"/>
      Informations de base
    </h3>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Title -->
      <div class="md:col-span-2">
        <label for="title" class="block text-xs font-semibold mb-1 text-secondary-900">
          Titre du produit *
        </label>
        <InputText
          id="title"
          :model-value="title"
          placeholder="Ex: Levi's 501 Vintage"
          class="w-full"
          :class="{ 'p-invalid': validation.hasError('title') }"
          required
          @update:model-value="$emit('update:title', $event)"
          @blur="validation.touch('title')"
        />
        <small v-if="validation.hasError('title')" class="p-error">
          {{ validation.getError('title') }}
        </small>
      </div>

      <!-- Description -->
      <div class="md:col-span-2">
        <div class="flex items-center justify-between mb-1">
          <label for="description" class="block text-xs font-semibold text-secondary-900">
            Description *
          </label>
          <Button
            v-if="productId"
            type="button"
            label="Générer avec IA"
            icon="pi pi-sparkles"
            class="p-button-sm p-button-outlined p-button-secondary"
            :loading="isGenerating"
            :disabled="isGenerating"
            @click="$emit('generate-description')"
          />
        </div>
        <Textarea
          id="description"
          :model-value="description"
          placeholder="Décrivez votre produit en détail..."
          rows="5"
          class="w-full"
          :class="{ 'p-invalid': validation.hasError('description') }"
          required
          @update:model-value="$emit('update:description', $event)"
          @blur="validation.touch('description')"
        />
        <small v-if="validation.hasError('description')" class="p-error">
          {{ validation.getError('description') }}
        </small>
      </div>

      <!-- Price -->
      <div>
        <label for="price" class="block text-xs font-semibold mb-1 text-secondary-900">
          Prix (€)
          <span class="text-xs text-gray-500 font-normal ml-2">
            (calculé automatiquement si vide)
          </span>
        </label>
        <InputNumber
          id="price"
          :model-value="price"
          mode="currency"
          currency="EUR"
          locale="fr-FR"
          class="w-full"
          :min="0"
          :min-fraction-digits="2"
          placeholder="Laissez vide pour calcul auto"
          @update:model-value="$emit('update:price', $event)"
        />
        <p v-if="calculatedPrice" class="text-xs text-green-600 mt-1">
          Prix suggéré: {{ calculatedPrice }}€
        </p>
      </div>

      <!-- Stock -->
      <div>
        <label for="stock_quantity" class="block text-xs font-semibold mb-1 text-secondary-900">
          Stock (quantité)
        </label>
        <InputNumber
          id="stock_quantity"
          :model-value="stockQuantity"
          class="w-full"
          :min="0"
          show-buttons
          @update:model-value="$emit('update:stockQuantity', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description: string
  price: number | null
  stockQuantity: number
  productId?: number
  isGenerating: boolean
  calculatedPrice: number | null
  validation: any
}>()

defineEmits<{
  'update:title': [value: string]
  'update:description': [value: string]
  'update:price': [value: number | null]
  'update:stockQuantity': [value: number]
  'generate-description': []
}>()
</script>

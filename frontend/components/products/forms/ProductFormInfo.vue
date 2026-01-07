<template>
  <div class="form-subsection-spacing">
    <h3 class="form-section-title">
      <i class="pi pi-info-circle" />
      Informations produit
    </h3>

    <div class="grid grid-cols-1 md:grid-cols-2 form-grid-spacing">
      <!-- Titre -->
      <div class="md:col-span-2">
        <label for="title" class="block text-xs font-semibold mb-1 text-secondary-900 flex items-center gap-1">
          Titre du produit *
          <i v-if="validation?.isFieldValid?.('title')" class="pi pi-check-circle text-green-500 text-xs" />
        </label>
        <div class="relative">
          <InputText
            id="title"
            :model-value="title"
            placeholder="Ex: Levi's 501 Vintage W32/L34"
            class="w-full"
            :class="{
              'p-invalid': validation?.hasError('title'),
              'border-green-400': validation?.isFieldValid?.('title')
            }"
            @update:model-value="handleTitleChange"
            @blur="validation?.touch('title')"
          />
        </div>
        <small v-if="validation?.hasError('title')" class="p-error">
          {{ validation?.getError('title') }}
        </small>
      </div>

      <!-- Description -->
      <div class="md:col-span-2">
        <div class="flex items-center justify-between mb-1">
          <label for="description" class="block text-xs font-semibold text-secondary-900 flex items-center gap-1">
            Description *
            <i v-if="validation?.isFieldValid?.('description')" class="pi pi-check-circle text-green-500 text-xs" />
          </label>
          <Button
            v-if="productId"
            type="button"
            label="Générer avec IA"
            icon="pi pi-sparkles"
            class="p-button-sm p-button-outlined p-button-secondary"
            :loading="isGeneratingDescription"
            :disabled="isGeneratingDescription"
            @click="$emit('generateDescription')"
          />
        </div>
        <Textarea
          id="description"
          :model-value="description"
          placeholder="Décrivez votre produit en détail : état, caractéristiques, histoire..."
          rows="4"
          class="w-full"
          :class="{
            'p-invalid': validation?.hasError('description'),
            'border-green-400': validation?.isFieldValid?.('description')
          }"
          @update:model-value="handleDescriptionChange"
          @blur="validation?.touch('description')"
        />
        <small v-if="validation?.hasError('description')" class="p-error">
          {{ validation?.getError('description') }}
        </small>
      </div>

      <!-- Prix -->
      <div>
        <label for="price" class="block text-xs font-semibold mb-1 text-secondary-900">
          Prix (EUR)
          <span class="text-xs text-gray-500 font-normal ml-1">
            (auto-calculé si vide)
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
          placeholder="Laisser vide = calcul auto"
          @update:model-value="$emit('update:price', $event)"
        />
        <p v-if="suggestedPrice" class="text-xs text-green-600 mt-1">
          Prix suggéré: {{ suggestedPrice }} EUR
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  description: string
  price: number | null
  productId?: number
  isGeneratingDescription?: boolean
  suggestedPrice?: number | null
  validation?: any
}

const props = withDefaults(defineProps<Props>(), {
  productId: undefined,
  isGeneratingDescription: false,
  suggestedPrice: null,
  validation: undefined
})

const emit = defineEmits<{
  'update:title': [value: string]
  'update:description': [value: string]
  'update:price': [value: number | null]
  'generateDescription': []
}>()

// Handle title change with validation
const handleTitleChange = (value: string) => {
  emit('update:title', value)
  // Validate with debounce if validation is available
  if (props.validation?.validateDebounced) {
    props.validation.validateDebounced('title', value)
  }
}

// Handle description change with validation
const handleDescriptionChange = (value: string) => {
  emit('update:description', value)
  // Validate with debounce if validation is available
  if (props.validation?.validateDebounced) {
    props.validation.validateDebounced('description', value)
  }
}
</script>

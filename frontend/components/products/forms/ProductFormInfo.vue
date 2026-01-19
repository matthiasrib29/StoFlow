<template>
  <div class="form-subsection-spacing">
    <h3 class="form-section-title">
      <i class="pi pi-info-circle" />
      Informations produit
    </h3>

    <div class="grid grid-cols-1 md:grid-cols-2 form-grid-spacing">
      <!-- Titre -->
      <div class="md:col-span-2">
        <div class="flex items-center justify-between mb-1">
          <label for="title" class="block text-xs font-semibold text-secondary-900 flex items-center gap-1">
            Titre du produit *
            <i v-if="validation?.isFieldValid?.('title')" class="pi pi-check-circle text-green-500 text-xs" />
          </label>
          <!-- Text Generator Button -->
          <ProductsTextGeneratorButton
            :product-id="productId"
            :attributes="textGeneratorAttributes"
            :disabled="!hasMinimumAttributes"
            label=""
            class="!p-1 !px-2"
            v-tooltip.left="hasMinimumAttributes ? 'Generer titre et description SEO' : 'Remplissez d\'abord les attributs (marque, categorie, etc.)'"
            @generate="handleTextGenerated"
            @error="handleTextError"
          />
        </div>
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
        <label for="description" class="block text-xs font-semibold mb-1 text-secondary-900 flex items-center gap-1">
          Description *
          <i v-if="validation?.isFieldValid?.('description')" class="pi pi-check-circle text-green-500 text-xs" />
        </label>
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

    </div>

    <!-- Text Preview Modal -->
    <ProductsTextPreviewModal
      v-model:visible="showTextModal"
      :titles="generatedTitles"
      :descriptions="generatedDescriptions"
      :loading="false"
      :error="textGeneratorError"
      @select-title="handleSelectTitle"
      @select-description="handleSelectDescription"
      @apply-all="handleApplyAll"
    />
  </div>
</template>

<script setup lang="ts">
import type { TextPreviewInput } from '~/types/textGenerator'

interface Props {
  title: string
  description: string
  validation?: any
  // Text generator props
  productId?: number
  brand?: string
  category?: string
  gender?: string
  sizeNormalized?: string
  colors?: string[]
  material?: string
  fit?: string
  condition?: number
  decade?: string
  rise?: string
  closure?: string
  uniqueFeature?: string[]
  pattern?: string
  trend?: string
  season?: string
  origin?: string
  conditionSup?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  validation: undefined,
  productId: undefined,
  brand: undefined,
  category: undefined,
  gender: undefined,
  sizeNormalized: undefined,
  colors: undefined,
  material: undefined,
  fit: undefined,
  condition: undefined,
  decade: undefined,
  rise: undefined,
  closure: undefined,
  uniqueFeature: undefined,
  pattern: undefined,
  trend: undefined,
  season: undefined,
  origin: undefined,
  conditionSup: undefined
})

const emit = defineEmits<{
  'update:title': [value: string]
  'update:description': [value: string]
}>()

// Text generator state
const showTextModal = ref(false)
const generatedTitles = ref<Record<string, string>>({})
const generatedDescriptions = ref<Record<string, string>>({})
const textGeneratorError = ref<string | null>(null)

// Build attributes for text generator preview
const textGeneratorAttributes = computed<TextPreviewInput>(() => ({
  brand: props.brand,
  category: props.category,
  gender: props.gender,
  size_normalized: props.sizeNormalized,
  colors: props.colors,
  material: props.material,
  fit: props.fit,
  condition: props.condition,
  decade: props.decade,
  rise: props.rise,
  closure: props.closure,
  unique_feature: props.uniqueFeature,
  pattern: props.pattern,
  trend: props.trend,
  season: props.season,
  origin: props.origin,
  condition_sup: props.conditionSup
}))

// Check if we have minimum attributes to generate
const hasMinimumAttributes = computed(() => {
  // Need at least brand or category to generate meaningful text
  return !!(props.brand || props.category)
})

// Handle text generation results
const handleTextGenerated = (results: { titles: Record<string, string>; descriptions: Record<string, string> }) => {
  generatedTitles.value = results.titles
  generatedDescriptions.value = results.descriptions
  textGeneratorError.value = null
  showTextModal.value = true
}

// Handle text generation error
const handleTextError = (message: string) => {
  textGeneratorError.value = message
  generatedTitles.value = {}
  generatedDescriptions.value = {}
  showTextModal.value = true
}

// Handle title selection from modal
const handleSelectTitle = (_format: string, title: string) => {
  emit('update:title', title)
  // Validate if validation is available
  if (props.validation?.validateDebounced) {
    props.validation.validateDebounced('title', title)
  }
}

// Handle description selection from modal
const handleSelectDescription = (_style: string, description: string) => {
  emit('update:description', description)
  // Validate if validation is available
  if (props.validation?.validateDebounced) {
    props.validation.validateDebounced('description', description)
  }
}

// Handle apply all from modal
const handleApplyAll = (data: { title: string; description: string }) => {
  emit('update:title', data.title)
  emit('update:description', data.description)
  // Validate both fields
  if (props.validation?.validateDebounced) {
    props.validation.validateDebounced('title', data.title)
    props.validation.validateDebounced('description', data.description)
  }
}

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

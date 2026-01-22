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
import type { TextPreviewInput, TitleFormat, DescriptionStyle } from '~/types/textGenerator'

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
  model?: string
  neckline?: string
  sleevelength?: string
  lining?: string
  stretch?: string
  sport?: string
  length?: string
  marking?: string
  location?: string
  dim1?: number
  dim2?: number
  dim3?: number
  dim4?: number
  dim5?: number
  dim6?: number
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
  conditionSup: undefined,
  model: undefined,
  neckline: undefined,
  sleevelength: undefined,
  lining: undefined,
  stretch: undefined,
  sport: undefined,
  length: undefined,
  marking: undefined,
  location: undefined,
  dim1: undefined,
  dim2: undefined,
  dim3: undefined,
  dim4: undefined,
  dim5: undefined,
  dim6: undefined,
})

const emit = defineEmits<{
  'update:title': [value: string]
  'update:description': [value: string]
}>()

// Text generator composable for settings and preview
const {
  settings,
  loadSettings,
  preview: previewText,
  titles: previewTitles,
  descriptions: previewDescriptions,
} = useProductTextGenerator()

// Text generator state
const showTextModal = ref(false)
const generatedTitles = ref<Record<string, string>>({})
const generatedDescriptions = ref<Record<string, string>>({})
const textGeneratorError = ref<string | null>(null)

// Track if user has manually edited title/description
const userEditedTitle = ref(false)
const userEditedDescription = ref(false)

// Track last sent attributes to prevent infinite loops
const lastSentAttributesJson = ref<string>('')

// Mapping format/style number to API key
const titleFormatKeys: Record<TitleFormat, string> = {
  1: 'minimaliste',
  2: 'standard_vinted',
  3: 'seo_mots_cles',
  4: 'vintage_collectionneur',
  5: 'technique_professionnel',
}

const descriptionStyleKeys: Record<DescriptionStyle, string> = {
  1: 'catalogue_structure',
  2: 'descriptif_redige',
  3: 'fiche_technique',
  4: 'vendeur_pro',
  5: 'visuel_emoji',
}

// Build attributes for text generator preview
const textGeneratorAttributes = computed<TextPreviewInput>(() => ({
  brand: props.brand,
  model: props.model,
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
  condition_sup: props.conditionSup,
  neckline: props.neckline,
  sleeve_length: props.sleevelength,
  lining: props.lining,
  stretch: props.stretch,
  sport: props.sport,
  length: props.length,
  marking: props.marking,
  location: props.location,
  dim1: props.dim1,
  dim2: props.dim2,
  dim3: props.dim3,
  dim4: props.dim4,
  dim5: props.dim5,
  dim6: props.dim6,
}))

// Check if we have minimum attributes to generate
const hasMinimumAttributes = computed(() => {
  // Need at least brand or category to generate meaningful text
  return !!(props.brand || props.category)
})

// Load settings on mount
onMounted(async () => {
  await loadSettings()
})

// Debounced auto-generation when attributes change
const debouncedAutoGenerate = useDebounceFn(async () => {
  if (!hasMinimumAttributes.value) return

  // Prevent infinite loops: skip if attributes haven't actually changed
  const currentJson = JSON.stringify(textGeneratorAttributes.value)
  if (currentJson === lastSentAttributesJson.value) return
  lastSentAttributesJson.value = currentJson

  // Call preview API
  await previewText(textGeneratorAttributes.value)

  // Get default format/style from settings (or fallback to 1)
  const defaultTitleFormat = settings.value?.default_title_format || 1
  const defaultDescriptionStyle = settings.value?.default_description_style || 1

  const titleKey = titleFormatKeys[defaultTitleFormat as TitleFormat]
  const descriptionKey = descriptionStyleKeys[defaultDescriptionStyle as DescriptionStyle]

  // Auto-fill title if user hasn't manually edited it
  if (!userEditedTitle.value && previewTitles.value[titleKey]) {
    emit('update:title', previewTitles.value[titleKey])
  }

  // Auto-fill description if user hasn't manually edited it
  if (!userEditedDescription.value && previewDescriptions.value[descriptionKey]) {
    emit('update:description', previewDescriptions.value[descriptionKey])
  }
}, 500)

// Watch attributes for auto-generation
watch(textGeneratorAttributes, () => {
  debouncedAutoGenerate()
}, { deep: true })

// Handle text generation results (from button click - opens modal)
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
  userEditedTitle.value = true // Mark as user choice
  emit('update:title', title)
  // Validate if validation is available
  if (props.validation?.validateDebounced) {
    props.validation.validateDebounced('title', title)
  }
}

// Handle description selection from modal
const handleSelectDescription = (_style: string, description: string) => {
  userEditedDescription.value = true // Mark as user choice
  emit('update:description', description)
  // Validate if validation is available
  if (props.validation?.validateDebounced) {
    props.validation.validateDebounced('description', description)
  }
}

// Handle apply all from modal
const handleApplyAll = (data: { title: string; description: string }) => {
  userEditedTitle.value = true
  userEditedDescription.value = true
  emit('update:title', data.title)
  emit('update:description', data.description)
  // Validate both fields
  if (props.validation?.validateDebounced) {
    props.validation.validateDebounced('title', data.title)
    props.validation.validateDebounced('description', data.description)
  }
}

// Handle title change with validation (manual edit)
const handleTitleChange = (value: string) => {
  userEditedTitle.value = true // User is manually editing
  emit('update:title', value)
  // Validate with debounce if validation is available
  if (props.validation?.validateDebounced) {
    props.validation.validateDebounced('title', value)
  }
}

// Handle description change with validation (manual edit)
const handleDescriptionChange = (value: string) => {
  userEditedDescription.value = true // User is manually editing
  emit('update:description', value)
  // Validate with debounce if validation is available
  if (props.validation?.validateDebounced) {
    props.validation.validateDebounced('description', value)
  }
}
</script>

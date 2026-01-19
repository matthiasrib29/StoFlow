<template>
  <div class="page-container">
    <PageHeader
      title="Produits"
      subtitle="Configurez les templates par défaut pour vos produits"
    />

    <div class="space-y-6">
      <!-- Test Product Info (compact) -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <i class="pi pi-box text-gray-400" />
              <span class="text-sm font-medium text-gray-600">Produit test pour les previews</span>
              <span class="text-xs text-gray-400">— Jeans Levi's 501 Vintage</span>
            </div>

            <!-- Compact attributes display -->
            <div class="flex flex-wrap gap-2">
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-white border border-gray-200">
                <span class="text-gray-500 mr-1">Marque:</span>
                <span class="font-medium">{{ testProductDisplay.brand }}</span>
              </span>
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-white border border-gray-200">
                <span class="text-gray-500 mr-1">Modèle:</span>
                <span class="font-medium">501</span>
              </span>
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-white border border-gray-200">
                <span class="text-gray-500 mr-1">Type:</span>
                <span class="font-medium">{{ testProductDisplay.category }}</span>
              </span>
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-white border border-gray-200">
                <span class="text-gray-500 mr-1">Taille:</span>
                <span class="font-medium">{{ testProductDisplay.size }}</span>
              </span>
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-white border border-gray-200">
                <span class="text-gray-500 mr-1">Matière:</span>
                <span class="font-medium">{{ testProductDisplay.material }}</span>
              </span>
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-green-50 border border-green-200 text-green-700">
                <span class="mr-1">État:</span>
                <span class="font-medium">{{ testProductDisplay.condition }}</span>
              </span>
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-amber-50 border border-amber-200 text-amber-700">
                <span class="mr-1">Époque:</span>
                <span class="font-medium">{{ testProductDisplay.decade }}</span>
              </span>
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-blue-50 border border-blue-200 text-blue-700">
                <span class="mr-1">Origine:</span>
                <span class="font-medium">{{ testProductDisplay.origin }}</span>
              </span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Title Template Section -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
          <div class="space-y-4">
            <div>
              <h3 class="text-lg font-bold text-secondary-900 mb-1">Template de titre</h3>
              <p class="text-sm text-gray-600">
                Choisissez le format utilisé pour générer automatiquement les titres de vos produits.
              </p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <div
                v-for="option in titleFormatOptions"
                :key="option.value"
                class="cursor-pointer rounded-lg border-2 p-4 transition-all"
                :class="[
                  form.titleFormat === option.value
                    ? 'border-primary-400 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                ]"
                @click="selectTitleFormat(option.value)"
              >
                <div class="flex items-center gap-3 mb-2">
                  <div
                    class="w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0"
                    :class="[
                      form.titleFormat === option.value
                        ? 'border-primary-400'
                        : 'border-gray-300'
                    ]"
                  >
                    <div
                      v-if="form.titleFormat === option.value"
                      class="w-2.5 h-2.5 rounded-full bg-primary-400"
                    />
                  </div>
                  <span class="font-semibold text-secondary-900">{{ option.label }}</span>
                </div>
                <p class="text-xs text-gray-500 ml-8">
                  {{ getTitleFormatDescription(option.value) }}
                </p>
              </div>
            </div>

            <!-- Title Preview -->
            <div v-if="previewLoading" class="flex items-center justify-center py-4">
              <i class="pi pi-spin pi-spinner text-xl text-gray-400" />
            </div>
            <div v-else-if="form.titleFormat && previewTitle" class="mt-4">
              <div class="flex items-center gap-2 mb-2">
                <i class="pi pi-eye text-primary-400" />
                <span class="text-sm font-semibold text-secondary-900">Preview</span>
                <span class="text-xs text-gray-400">({{ selectedTitleLabel }})</span>
              </div>
              <div class="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <p class="text-sm text-secondary-800 font-medium">{{ previewTitle }}</p>
              </div>
            </div>
            <div v-else-if="!form.titleFormat" class="mt-4 text-center py-4 text-gray-400 bg-gray-50 rounded-lg">
              <i class="pi pi-eye text-xl mb-1" />
              <p class="text-xs">Sélectionnez un template pour voir la preview</p>
            </div>
          </div>
        </template>
      </Card>

      <!-- Description Template Section -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
          <div class="space-y-4">
            <div>
              <h3 class="text-lg font-bold text-secondary-900 mb-1">Template de description</h3>
              <p class="text-sm text-gray-600">
                Choisissez le style utilisé pour générer automatiquement les descriptions de vos produits.
              </p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <div
                v-for="option in descriptionStyleOptions"
                :key="option.value"
                class="cursor-pointer rounded-lg border-2 p-4 transition-all"
                :class="[
                  form.descriptionStyle === option.value
                    ? 'border-primary-400 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                ]"
                @click="selectDescriptionStyle(option.value)"
              >
                <div class="flex items-center gap-3 mb-2">
                  <div
                    class="w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0"
                    :class="[
                      form.descriptionStyle === option.value
                        ? 'border-primary-400'
                        : 'border-gray-300'
                    ]"
                  >
                    <div
                      v-if="form.descriptionStyle === option.value"
                      class="w-2.5 h-2.5 rounded-full bg-primary-400"
                    />
                  </div>
                  <span class="font-semibold text-secondary-900">{{ option.label }}</span>
                </div>
                <p class="text-xs text-gray-500 ml-8">
                  {{ getDescriptionStyleDescription(option.value) }}
                </p>
              </div>
            </div>

            <!-- Description Preview -->
            <div v-if="previewLoading" class="flex items-center justify-center py-4">
              <i class="pi pi-spin pi-spinner text-xl text-gray-400" />
            </div>
            <div v-else-if="form.descriptionStyle && previewDescription" class="mt-4">
              <div class="flex items-center gap-2 mb-2">
                <i class="pi pi-eye text-primary-400" />
                <span class="text-sm font-semibold text-secondary-900">Preview</span>
                <span class="text-xs text-gray-400">({{ selectedDescriptionLabel }})</span>
              </div>
              <div class="bg-gray-50 border border-gray-200 rounded-lg p-3 max-h-48 overflow-y-auto">
                <p class="text-sm text-secondary-800 whitespace-pre-line">{{ previewDescription }}</p>
              </div>
            </div>
            <div v-else-if="!form.descriptionStyle" class="mt-4 text-center py-4 text-gray-400 bg-gray-50 rounded-lg">
              <i class="pi pi-eye text-xl mb-1" />
              <p class="text-xs">Sélectionnez un template pour voir la preview</p>
            </div>
          </div>
        </template>
      </Card>

      <!-- Buttons -->
      <div class="flex justify-end gap-3">
        <Button
          label="Annuler"
          icon="pi pi-times"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="resetForm"
        />
        <Button
          label="Sauvegarder"
          icon="pi pi-save"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          :loading="loading"
          @click="handleSave"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TitleFormat, DescriptionStyle, TextPreviewInput } from '~/types/textGenerator'
import { TITLE_FORMAT_LABELS, DESCRIPTION_STYLE_LABELS } from '~/types/textGenerator'

definePageMeta({
  layout: 'dashboard'
})

const { showSuccess, showError } = useAppToast()
const {
  titleFormatOptions,
  descriptionStyleOptions,
  settings,
  loading,
  loadSettings,
  saveSettings,
  preview,
  titles: previewTitles,
  descriptions: previewDescriptions,
} = useProductTextGenerator()

// Form state
const form = ref<{
  titleFormat: TitleFormat | null
  descriptionStyle: DescriptionStyle | null
}>({
  titleFormat: null,
  descriptionStyle: null,
})

// Preview state
const previewLoading = ref(false)

// Test product attributes for preview - realistic data from database (in French)
const testProduct: TextPreviewInput = {
  brand: "Levi's",
  model: '501',
  category: 'Jean',
  gender: 'Homme',
  size_normalized: 'W32L32',
  colors: ['Indigo foncé', 'Bleu marine'],
  material: 'Coton',
  fit: 'Slim',
  condition: 7, // Très bon état
  decade: '90s',
  origin: 'USA',
  trend: 'Vintage Americana',
  season: 'Toutes saisons',
  unique_feature: ['Selvedge', 'Rivets originaux', 'Red tab'],
  rise: 'Taille moyenne',
  closure: 'Braguette boutonnée',
  pattern: 'Uni',
  dim1: 55, // PTP measurement in cm
}

// Labels for displaying the test product attributes
const testProductDisplay = {
  brand: "Levi's",
  model: '501',
  category: 'Jean',
  size: 'W32L32',
  colors: 'Indigo foncé, Bleu marine',
  material: 'Coton',
  fit: 'Slim',
  condition: 'Très bon état',
  decade: '90s',
  origin: 'USA',
  trend: 'Vintage Americana',
  season: 'Toutes saisons',
  features: 'Selvedge, Rivets originaux, Red tab',
  rise: 'Taille moyenne',
  closure: 'Braguette boutonnée',
  pattern: 'Uni',
  gender: 'Homme',
}

// Computed
const previewTitle = computed(() => {
  if (!form.value.titleFormat) return ''
  const key = getTitleFormatKey(form.value.titleFormat)
  return previewTitles.value[key] || ''
})

const previewDescription = computed(() => {
  if (!form.value.descriptionStyle) return ''
  const key = getDescriptionStyleKey(form.value.descriptionStyle)
  return previewDescriptions.value[key] || ''
})

const selectedTitleLabel = computed(() => {
  if (!form.value.titleFormat) return ''
  return TITLE_FORMAT_LABELS[form.value.titleFormat]
})

const selectedDescriptionLabel = computed(() => {
  if (!form.value.descriptionStyle) return ''
  return DESCRIPTION_STYLE_LABELS[form.value.descriptionStyle]
})

// Helper functions
function getTitleFormatKey(format: TitleFormat): string {
  const keys: Record<TitleFormat, string> = {
    1: 'minimaliste',
    2: 'standard_vinted',
    3: 'seo_mots_cles',
    4: 'vintage_collectionneur',
    5: 'technique_professionnel',
  }
  return keys[format]
}

function getDescriptionStyleKey(style: DescriptionStyle): string {
  const keys: Record<DescriptionStyle, string> = {
    1: 'catalogue_structure',
    2: 'descriptif_redige',
    3: 'fiche_technique',
    4: 'vendeur_pro',
    5: 'visuel_emoji',
  }
  return keys[style]
}

function getTitleFormatDescription(format: TitleFormat): string {
  const descriptions: Record<TitleFormat, string> = {
    1: 'Focus marque & modèle. Idéal pour le luxe et les articles très connus',
    2: 'Équilibré avec matière et coupe. Passe-partout pour fast fashion',
    3: 'Optimisé recherche. Capture les requêtes spécifiques (col, manches, motif)',
    4: 'Inclut époque, origine et spécificités. Pour collectionneurs',
    5: 'Maximaliste avec dimensions. Pour eBay et marketplace pro',
  }
  return descriptions[format]
}

function getDescriptionStyleDescription(style: DescriptionStyle): string {
  const descriptions: Record<DescriptionStyle, string> = {
    1: 'Sections claires avec emojis. Groupé par thématique',
    2: 'Phrases fluides, ton humain. Idéal e-commerce',
    3: 'Liste pure sans fioriture. Pour export et marketplace pro',
    4: 'État et mesures en avant. Ce que les clients demandent le plus',
    5: 'Un emoji par attribut. Facile à scanner rapidement',
  }
  return descriptions[style]
}

// Generate preview
const generatePreview = async () => {
  previewLoading.value = true
  try {
    await preview(testProduct)
  }
  finally {
    previewLoading.value = false
  }
}

// Select title format and generate preview if needed
const selectTitleFormat = async (value: TitleFormat) => {
  form.value.titleFormat = value
  // Generate preview if not already loaded
  if (!previewTitle.value) {
    await generatePreview()
  }
}

// Select description style and generate preview if needed
const selectDescriptionStyle = async (value: DescriptionStyle) => {
  form.value.descriptionStyle = value
  // Generate preview if not already loaded
  if (!previewDescription.value) {
    await generatePreview()
  }
}

// Load settings on mount
onMounted(async () => {
  await loadSettings()
  if (settings.value) {
    form.value.titleFormat = settings.value.default_title_format
    form.value.descriptionStyle = settings.value.default_description_style
  }
  // Generate initial preview if we have saved settings
  if (form.value.titleFormat && form.value.descriptionStyle) {
    await generatePreview()
  }
})

// Reset form to saved values
const resetForm = () => {
  if (settings.value) {
    form.value.titleFormat = settings.value.default_title_format
    form.value.descriptionStyle = settings.value.default_description_style
  }
}

// Save settings
const handleSave = async () => {
  try {
    await saveSettings({
      default_title_format: form.value.titleFormat,
      default_description_style: form.value.descriptionStyle,
    })
    showSuccess('Paramètres sauvegardés', 'Vos templates par défaut ont été mis à jour')
  }
  catch {
    showError('Erreur', 'Impossible de sauvegarder les paramètres')
  }
}
</script>

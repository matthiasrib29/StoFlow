<template>
  <form class="space-y-4" @submit.prevent="handleSubmit">
    <!-- ===== BOUTON REMPLIR AVEC IA ===== -->
    <div
      v-if="productId && hasImages"
      class="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-lg p-4 mb-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="bg-primary-100 rounded-full p-2">
            <i class="pi pi-sparkles text-primary-600 text-lg" />
          </div>
          <div>
            <h4 class="text-sm font-semibold text-primary-900">Remplissage automatique</h4>
            <p class="text-xs text-primary-700">Analysez les images pour remplir le formulaire automatiquement</p>
          </div>
        </div>
        <Button
          type="button"
          label="Remplir avec l'IA"
          icon="pi pi-sparkles"
          class="p-button-primary"
          :loading="isAnalyzingImages"
          :disabled="isAnalyzingImages || isGeneratingDescription"
          @click="analyzeAndFillForm"
        />
      </div>
    </div>

    <!-- ===== INFORMATIONS DE BASE ===== -->
    <div class="space-y-4">
      <h3 class="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1.5 uppercase tracking-wide">
        <i class="pi pi-info-circle text-xs"/>
        Informations de base
      </h3>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="md:col-span-2">
          <label for="title" class="block text-xs font-semibold mb-1 text-secondary-900">
            Titre du produit *
          </label>
          <InputText
            id="title"
            :model-value="modelValue.title"
            placeholder="Ex: Levi's 501 Vintage"
            class="w-full"
            :class="{ 'p-invalid': validation.hasError('title') }"
            required
            @update:model-value="handleFieldUpdate('title', $event)"
            @blur="validation.touch('title')"
          />
          <small v-if="validation.hasError('title')" class="p-error">
            {{ validation.getError('title') }}
          </small>
        </div>

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
              :loading="isGeneratingDescription"
              :disabled="isGeneratingDescription"
              @click="generateDescription"
            />
          </div>
          <Textarea
            id="description"
            :model-value="modelValue.description"
            placeholder="Décrivez votre produit en détail..."
            rows="5"
            class="w-full"
            :class="{ 'p-invalid': validation.hasError('description') }"
            required
            @update:model-value="handleFieldUpdate('description', $event)"
            @blur="validation.touch('description')"
          />
          <small v-if="validation.hasError('description')" class="p-error">
            {{ validation.getError('description') }}
          </small>
        </div>

        <div>
          <label for="price" class="block text-xs font-semibold mb-1 text-secondary-900">
            Prix (€)
            <span class="text-xs text-gray-500 font-normal ml-2">
              (calculé automatiquement si vide)
            </span>
          </label>
          <InputNumber
            id="price"
            :model-value="modelValue.price"
            mode="currency"
            currency="EUR"
            locale="fr-FR"
            class="w-full"
            :min="0"
            :min-fraction-digits="2"
            placeholder="Laissez vide pour calcul auto"
            @update:model-value="updateField('price', $event)"
          />
          <p v-if="calculatedPrice" class="text-xs text-green-600 mt-1">
            💡 Prix suggéré: {{ calculatedPrice }}€
          </p>
        </div>

        <div>
          <label for="stock_quantity" class="block text-xs font-semibold mb-1 text-secondary-900">
            Stock (quantité)
          </label>
          <InputNumber
            id="stock_quantity"
            :model-value="modelValue.stock_quantity"
            class="w-full"
            :min="0"
            show-buttons
            @update:model-value="updateField('stock_quantity', $event)"
          />
        </div>
      </div>
    </div>

    <!-- ===== ATTRIBUTS OBLIGATOIRES ===== -->
    <div class="space-y-4">
      <h3 class="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1.5 uppercase tracking-wide">
        <i class="pi pi-tag text-xs"/>
        Attributs obligatoires
      </h3>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label for="brand" class="block text-xs font-semibold mb-1 text-secondary-900">
            Marque *
          </label>
          <AutoComplete
            id="brand"
            :model-value="modelValue.brand"
            :suggestions="brandSuggestionLabels"
            placeholder="Ex: Levi's, Nike, Zara..."
            class="w-full"
            :class="{ 'p-invalid': validation.hasError('brand') }"
            required
            :min-length="1"
            :delay="50"
            @update:model-value="handleFieldUpdate('brand', $event)"
            @blur="validation.touch('brand')"
            @complete="handleBrandSearch"
          />
          <small v-if="validation.hasError('brand')" class="p-error">
            {{ validation.getError('brand') }}
          </small>
        </div>

        <div>
          <label for="category" class="block text-xs font-semibold mb-1 text-secondary-900">
            Catégorie *
          </label>
          <Select
            id="category"
            :model-value="modelValue.category"
            :options="categories"
            option-label="label"
            option-value="value"
            placeholder="Sélectionner une catégorie"
            class="w-full"
            :class="{ 'p-invalid': validation.hasError('category') }"
            required
            :loading="loadingCategories"
            @update:model-value="handleFieldUpdate('category', $event)"
            @blur="validation.touch('category')"
          />
          <small v-if="validation.hasError('category')" class="p-error">
            {{ validation.getError('category') }}
          </small>
        </div>

      </div>
    </div>

    <!-- ===== ATTRIBUTS (OBLIGATOIRES ET OPTIONNELS) ===== -->
    <ProductsFormsProductFormAttributes
      :condition="modelValue.condition"
      :label-size="modelValue.label_size"
      :color="modelValue.color"
      :material="modelValue.material"
      :fit="modelValue.fit"
      :gender="modelValue.gender"
      :season="modelValue.season"
      :conditions="conditions"
      :genders="genders"
      :seasons="seasons"
      :loading-conditions="loadingConditions"
      :loading-genders="loadingGenders"
      :loading-seasons="loadingSeasons"
      :validation="validation"
      @update:condition="updateField('condition', $event)"
      @update:label-size="updateField('label_size', $event)"
      @update:color="updateField('color', $event)"
      @update:material="updateField('material', $event)"
      @update:fit="updateField('fit', $event)"
      @update:gender="updateField('gender', $event)"
      @update:season="updateField('season', $event)"
    />

    <!-- ===== DIMENSIONS (MEASUREMENTS) ===== -->
    <ProductsFormsProductFormDimensions
      :dim1="modelValue.dim1"
      :dim2="modelValue.dim2"
      :dim3="modelValue.dim3"
      :dim4="modelValue.dim4"
      :dim5="modelValue.dim5"
      :dim6="modelValue.dim6"
      :validation="validation"
      @update:dim1="updateField('dim1', $event)"
      @update:dim2="updateField('dim2', $event)"
      @update:dim3="updateField('dim3', $event)"
      @update:dim4="updateField('dim4', $event)"
      @update:dim5="updateField('dim5', $event)"
      @update:dim6="updateField('dim6', $event)"
    />

    <!-- Actions -->
    <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
      <Button
        type="button"
        label="Annuler"
        icon="pi pi-times"
        class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
        @click="$emit('cancel')"
      />
      <Button
        type="submit"
        :label="submitLabel"
        icon="pi pi-check"
        class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold"
        :loading="isSubmitting"
      />
    </div>
  </form>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import type { AttributeOption } from '~/composables/useAttributes'
import { useLocaleStore } from '~/stores/locale'

interface ProductFormData {
  // Informations de base
  title: string
  description: string
  price: number | null

  // Attributs obligatoires
  brand: string
  category: string
  condition: string
  label_size: string
  color: string

  // Attributs optionnels
  material?: string | null
  fit?: string | null
  gender?: string | null
  season?: string | null

  // Dimensions
  dim1?: number | null
  dim2?: number | null
  dim3?: number | null
  dim4?: number | null
  dim5?: number | null
  dim6?: number | null

  // Stock
  stock_quantity: number
}

interface Props {
  modelValue: ProductFormData
  isSubmitting?: boolean
  submitLabel?: string
  productId?: number
  hasImages?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSubmitting: false,
  submitLabel: 'Créer le produit',
  productId: undefined,
  hasImages: false
})

const emit = defineEmits<{
  'update:modelValue': [value: ProductFormData]
  'submit': []
  'cancel': []
}>()

// Utiliser le composable pour récupérer les attributs
const {
  categories,
  conditions,
  genders,
  seasons,
  fetchAllAttributes,
  fetchAttribute,
  searchBrands,
  loadingCategories,
  loadingConditions,
  loadingGenders,
  loadingSeasons,
  clearCache
} = useAttributes()

// Store de locale pour la langue courante
const localeStore = useLocaleStore()

// Validation du formulaire
const validation = useProductFormValidation()
const { showSuccess, showError, showWarn } = useAppToast()

// API pour la génération IA
const { post } = useApi()

// État pour la génération de description IA
const isGeneratingDescription = ref(false)

// État pour l'analyse d'images IA (Gemini Vision)
const isAnalyzingImages = ref(false)

// État pour les suggestions de marques (autocomplete)
const brandSuggestions = ref<AttributeOption[]>([])

// Extraire juste les labels pour l'autocomplete (PrimeVue attend un tableau de strings)
const brandSuggestionLabels = computed(() => {
  return brandSuggestions.value.map(b => b.label)
})

// Fonction pour charger tous les attributs (utilisée au montage et au changement de langue)
const loadAllAttributes = async () => {
  const lang = localeStore.locale
  // Note: colors, materials, fits sont maintenant chargés par ProductFormAttributes
  await fetchAllAttributes(lang)
}

// Charger les attributs au montage du composant
onMounted(() => {
  loadAllAttributes()
})

// Recharger les attributs quand la langue change
watch(() => localeStore.locale, async () => {
  clearCache()
  await loadAllAttributes()
})

// TODO: Implémenter le calcul automatique du prix
const calculatedPrice = computed(() => {
  // Si le prix est déjà défini, ne pas calculer
  if (props.modelValue.price) return null

  // TODO: Appeler l'API pour calculer le prix selon brand + category + condition
  // Pour l'instant, retourner null
  return null
})

const updateField = (field: keyof ProductFormData, value: any) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })
}

// Fonction pour mettre à jour un champ avec validation
const handleFieldUpdate = (field: keyof ProductFormData, value: any) => {
  updateField(field, value)

  // Valider le champ si déjà touché
  if (validation.touched.value.has(field)) {
    validation.validateAndSetError(field, value)
  }
}

// Gérer le submit avec validation complète
const handleSubmit = () => {
  // Valider le formulaire complet
  const isValid = validation.validateForm(props.modelValue)

  if (!isValid) {
    // Marquer tous les champs comme touchés pour afficher toutes les erreurs
    validation.touchAll(props.modelValue)

    showWarn('Formulaire invalide', 'Veuillez corriger les erreurs avant de continuer')

    return
  }

  // Si valide, émettre l'événement submit
  emit('submit')
}

// Gérer la recherche de marques pour l'autocomplete
const handleBrandSearch = async (event: { query: string }) => {
  const results = await searchBrands(event.query)
  brandSuggestions.value = results
}

// Générer une description avec l'IA
const generateDescription = async () => {
  if (!props.productId) {
    showError('Erreur', 'Sauvegardez d\'abord le produit avant de générer une description')
    return
  }

  isGeneratingDescription.value = true

  try {
    const response = await post<{ description: string }>(
      `/products/${props.productId}/generate-description`
    )

    if (response?.description) {
      // Mettre à jour la description dans le formulaire
      updateField('description', response.description)
      showSuccess('Description générée', 'La description a été générée par l\'IA')
    }
  } catch (error: any) {
    const message = error?.data?.detail || error?.message || 'Erreur lors de la génération'

    if (message.includes('Crédits IA insuffisants') || error?.status === 402) {
      showError('Crédits insuffisants', 'Vous n\'avez plus de crédits IA. Upgradez votre abonnement.')
    } else {
      showError('Erreur', message)
    }
  } finally {
    isGeneratingDescription.value = false
  }
}

// Interface pour la réponse de l'analyse d'images
interface VisionAnalysisResponse {
  attributes: {
    title?: string | null
    description?: string | null
    price?: number | null
    category?: string | null
    brand?: string | null
    condition?: number | null
    size?: string | null
    label_size?: string | null
    color?: string | null
    material?: string | null
    fit?: string | null
    gender?: string | null
    season?: string | null
    sport?: string | null
    neckline?: string | null
    length?: string | null
    pattern?: string | null
    condition_sup?: string | null
    unique_feature?: string | null
    marking?: string | null
    confidence?: number
  }
  model: string
  images_analyzed: number
  tokens_used: number
  cost: number
  processing_time_ms: number
}

// Analyser les images et remplir le formulaire avec l'IA
const analyzeAndFillForm = async () => {
  if (!props.productId) {
    showError('Erreur', 'Sauvegardez d\'abord le produit avant d\'analyser les images')
    return
  }

  if (!props.hasImages) {
    showError('Erreur', 'Ajoutez des images au produit avant de lancer l\'analyse')
    return
  }

  isAnalyzingImages.value = true

  try {
    const response = await post<VisionAnalysisResponse>(
      `/products/${props.productId}/analyze-images`
    )

    if (response?.attributes) {
      const attrs = response.attributes
      let fieldsUpdated = 0

      // Auto-fill tous les champs non-null
      if (attrs.title) { updateField('title', attrs.title); fieldsUpdated++ }
      if (attrs.description) { updateField('description', attrs.description); fieldsUpdated++ }
      if (attrs.price) { updateField('price', attrs.price); fieldsUpdated++ }
      if (attrs.category) { updateField('category', attrs.category); fieldsUpdated++ }
      if (attrs.brand) { updateField('brand', attrs.brand); fieldsUpdated++ }
      if (attrs.condition !== null && attrs.condition !== undefined) {
        // Convertir la note 0-10 en string pour le select
        updateField('condition', String(attrs.condition))
        fieldsUpdated++
      }
      if (attrs.color) { updateField('color', attrs.color); fieldsUpdated++ }
      if (attrs.material) { updateField('material', attrs.material); fieldsUpdated++ }
      if (attrs.size) { updateField('size', attrs.size); fieldsUpdated++ }
      if (attrs.label_size) { updateField('label_size', attrs.label_size); fieldsUpdated++ }
      if (attrs.gender) { updateField('gender', attrs.gender); fieldsUpdated++ }
      if (attrs.season) { updateField('season', attrs.season); fieldsUpdated++ }
      if (attrs.fit) { updateField('fit', attrs.fit); fieldsUpdated++ }
      if (attrs.pattern) { updateField('pattern', attrs.pattern); fieldsUpdated++ }
      if (attrs.neckline) { updateField('neckline', attrs.neckline); fieldsUpdated++ }
      if (attrs.unique_feature) { updateField('unique_feature', attrs.unique_feature); fieldsUpdated++ }
      if (attrs.marking) { updateField('marking', attrs.marking); fieldsUpdated++ }

      const confidence = attrs.confidence ? Math.round(attrs.confidence * 100) : 0
      showSuccess(
        'Formulaire rempli',
        `${response.images_analyzed} image(s) analysée(s), ${fieldsUpdated} champ(s) rempli(s) (confiance: ${confidence}%)`
      )
    }
  } catch (error: any) {
    const message = error?.data?.detail || error?.message || 'Erreur lors de l\'analyse'

    if (message.includes('Crédits IA insuffisants') || error?.status === 402) {
      showError('Crédits insuffisants', 'Vous n\'avez plus de crédits IA. Upgradez votre abonnement.')
    } else if (message.includes('pas d\'images')) {
      showError('Pas d\'images', 'Ajoutez des images au produit avant de lancer l\'analyse.')
    } else {
      showError('Erreur', message)
    }
  } finally {
    isAnalyzingImages.value = false
  }
}
</script>

<template>
  <form class="space-y-8" @submit.prevent="handleSubmit">
    <!-- ===== INFORMATIONS DE BASE ===== -->
    <div class="bg-white rounded-lg shadow-sm p-6">
      <h3 class="text-lg font-bold text-secondary-900 mb-4 flex items-center gap-2">
        <i class="pi pi-info-circle"/>
        Informations de base
      </h3>

      <div class="grid grid-cols-2 gap-6">
        <div class="col-span-2">
          <label for="title" class="block text-sm font-bold mb-2 text-secondary-900">
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

        <div class="col-span-2">
          <label for="description" class="block text-sm font-bold mb-2 text-secondary-900">
            Description *
          </label>
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
          <label for="price" class="block text-sm font-bold mb-2 text-secondary-900">
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
          <label for="stock_quantity" class="block text-sm font-bold mb-2 text-secondary-900">
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
    <div class="bg-white rounded-lg shadow-sm p-6">
      <h3 class="text-lg font-bold text-secondary-900 mb-4 flex items-center gap-2">
        <i class="pi pi-tag"/>
        Attributs obligatoires
      </h3>

      <div class="grid grid-cols-2 gap-6">
        <div>
          <label for="brand" class="block text-sm font-bold mb-2 text-secondary-900">
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
          <label for="category" class="block text-sm font-bold mb-2 text-secondary-900">
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
    <div class="flex items-center justify-end gap-4 pt-6 border-t border-gray-200">
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
}

const props = withDefaults(defineProps<Props>(), {
  isSubmitting: false,
  submitLabel: 'Créer le produit'
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
const { showError, showWarn } = useAppToast()

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
</script>

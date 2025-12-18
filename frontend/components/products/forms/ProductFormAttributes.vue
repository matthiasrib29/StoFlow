<template>
  <!-- ===== ATTRIBUTS OBLIGATOIRES ===== -->
  <div class="bg-white rounded-lg shadow-sm p-6">
    <h3 class="text-lg font-bold text-secondary-900 mb-4 flex items-center gap-2">
      <i class="pi pi-tag"></i>
      Attributs obligatoires
    </h3>

    <div class="grid grid-cols-2 gap-6">
      <div>
        <label for="condition" class="block text-sm font-bold mb-2 text-secondary-900">
          État *
        </label>
        <Select
          id="condition"
          :model-value="condition"
          @update:model-value="handleAttributeUpdate('condition', $event)"
          @blur="validation?.touch('condition')"
          :options="conditions"
          optionLabel="label"
          optionValue="value"
          placeholder="Sélectionner l'état"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('condition') }"
          required
          :loading="loadingConditions"
        />
        <small v-if="validation?.hasError('condition')" class="p-error">
          {{ validation?.getError('condition') }}
        </small>
      </div>

      <div>
        <label for="label_size" class="block text-sm font-bold mb-2 text-secondary-900">
          Taille *
        </label>
        <InputText
          id="label_size"
          :model-value="labelSize"
          @update:model-value="handleAttributeUpdate('label_size', $event)"
          @blur="validation?.touch('label_size')"
          placeholder="Ex: M, 42, W32/L34..."
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('label_size') }"
          required
        />
        <small v-if="validation?.hasError('label_size')" class="p-error">
          {{ validation?.getError('label_size') }}
        </small>
      </div>

      <div>
        <label for="color" class="block text-sm font-bold mb-2 text-secondary-900">
          Couleur *
        </label>
        <Select
          id="color"
          :model-value="color"
          @update:model-value="handleAttributeUpdate('color', $event)"
          @blur="validation?.touch('color')"
          :options="colorsOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Sélectionner la couleur"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('color') }"
          required
          :loading="loadingColors"
        />
        <small v-if="validation?.hasError('color')" class="p-error">
          {{ validation?.getError('color') }}
        </small>
      </div>
    </div>
  </div>

  <!-- ===== ATTRIBUTS OPTIONNELS ===== -->
  <div class="bg-white rounded-lg shadow-sm p-6">
    <h3 class="text-lg font-bold text-secondary-900 mb-4 flex items-center gap-2">
      <i class="pi pi-sliders-h"></i>
      Attributs optionnels
    </h3>

    <div class="grid grid-cols-2 gap-6">
      <div>
        <label for="material" class="block text-sm font-bold mb-2 text-secondary-900">
          Matière
        </label>
        <Select
          id="material"
          :model-value="material"
          @update:model-value="handleAttributeUpdate('material', $event)"
          @blur="validation?.touch('material')"
          :options="materialsOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Sélectionner la matière"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('material') }"
          :loading="loadingMaterials"
        />
        <small v-if="validation?.hasError('material')" class="p-error">
          {{ validation?.getError('material') }}
        </small>
      </div>

      <div>
        <label for="fit" class="block text-sm font-bold mb-2 text-secondary-900">
          Coupe
        </label>
        <Select
          id="fit"
          :model-value="fit"
          @update:model-value="handleAttributeUpdate('fit', $event)"
          @blur="validation?.touch('fit')"
          :options="fitsOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Sélectionner la coupe"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('fit') }"
          :loading="loadingFits"
        />
        <small v-if="validation?.hasError('fit')" class="p-error">
          {{ validation?.getError('fit') }}
        </small>
      </div>

      <div>
        <label for="gender" class="block text-sm font-bold mb-2 text-secondary-900">
          Genre
        </label>
        <Select
          id="gender"
          :model-value="gender"
          @update:model-value="handleAttributeUpdate('gender', $event)"
          @blur="validation?.touch('gender')"
          :options="genders"
          optionLabel="label"
          optionValue="value"
          placeholder="Sélectionner le genre"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('gender') }"
          :loading="loadingGenders"
        />
        <small v-if="validation?.hasError('gender')" class="p-error">
          {{ validation?.getError('gender') }}
        </small>
      </div>

      <div>
        <label for="season" class="block text-sm font-bold mb-2 text-secondary-900">
          Saison
        </label>
        <Select
          id="season"
          :model-value="season"
          @update:model-value="handleAttributeUpdate('season', $event)"
          @blur="validation?.touch('season')"
          :options="seasons"
          optionLabel="label"
          optionValue="value"
          placeholder="Sélectionner la saison"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('season') }"
          :loading="loadingSeasons"
        />
        <small v-if="validation?.hasError('season')" class="p-error">
          {{ validation?.getError('season') }}
        </small>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import type { AttributeOption, ConditionOption } from '~/composables/useAttributes'
import { useLocaleStore } from '~/stores/locale'
import type { useProductFormValidation } from '~/composables/useProductFormValidation'

/**
 * Composant pour les attributs du produit
 *
 * Gère les attributs obligatoires (condition, taille, couleur) et
 * les attributs optionnels (matière, coupe, genre, saison)
 */

interface Props {
  // Attributs obligatoires
  condition: string
  labelSize: string
  color: string

  // Attributs optionnels
  material?: string | null
  fit?: string | null
  gender?: string | null
  season?: string | null

  // Options déjà chargées par le parent
  conditions: ConditionOption[]
  genders: AttributeOption[]
  seasons: AttributeOption[]

  // États de chargement du parent
  loadingConditions: boolean
  loadingGenders: boolean
  loadingSeasons: boolean

  // Validation
  validation?: ReturnType<typeof useProductFormValidation>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:condition': [value: string]
  'update:labelSize': [value: string]
  'update:color': [value: string]
  'update:material': [value: string | null]
  'update:fit': [value: string | null]
  'update:gender': [value: string | null]
  'update:season': [value: string | null]
}>()

// Charger les attributs supplémentaires (colors, materials, fits)
const localeStore = useLocaleStore()
const { loadMultipleAttributes } = useAttributeLoader()

const colorsOptions = ref<AttributeOption[]>([])
const materialsOptions = ref<AttributeOption[]>([])
const fitsOptions = ref<AttributeOption[]>([])

const loadingColors = ref(false)
const loadingMaterials = ref(false)
const loadingFits = ref(false)

// Charger les attributs au montage
onMounted(async () => {
  const lang = localeStore.locale

  await loadMultipleAttributes([
    { type: 'colors', targetRef: colorsOptions, loadingRef: loadingColors },
    { type: 'materials', targetRef: materialsOptions, loadingRef: loadingMaterials },
    { type: 'fits', targetRef: fitsOptions, loadingRef: loadingFits }
  ], lang)
})

/**
 * Gérer la mise à jour des champs avec validation
 */
type AttributeField = 'condition' | 'label_size' | 'color' | 'material' | 'fit' | 'gender' | 'season'

const handleAttributeUpdate = (field: AttributeField, value: string | null) => {
  // Émettre l'événement correspondant
  if (field === 'condition') emit('update:condition', value as string)
  else if (field === 'label_size') emit('update:labelSize', value as string)
  else if (field === 'color') emit('update:color', value as string)
  else if (field === 'material') emit('update:material', value)
  else if (field === 'fit') emit('update:fit', value)
  else if (field === 'gender') emit('update:gender', value)
  else if (field === 'season') emit('update:season', value)

  // Valider le champ si validation est fournie et le champ a déjà été touché
  if (props.validation && props.validation.touched.value.has(field)) {
    props.validation.validateAndSetError(field, value)
  }
}
</script>

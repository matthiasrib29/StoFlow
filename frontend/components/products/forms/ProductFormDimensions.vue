<template>
  <div class="space-y-3">
    <h3 class="text-xs font-bold text-gray-500 mb-2 flex items-center gap-1.5 uppercase tracking-wide">
      <i class="pi pi-arrows-alt text-xs"/>
      Dimensions (cm)
    </h3>

    <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
      <div>
        <label for="dim1" class="block text-xs font-semibold mb-1 text-secondary-900">
          Tour de poitrine / Épaules
        </label>
        <InputNumber
          id="dim1"
          :model-value="dim1"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('dim1') }"
          :min="0"
          suffix=" cm"
          @update:model-value="handleDimUpdate('dim1', $event)"
          @blur="validation?.touch('dim1')"
        />
        <small v-if="validation?.hasError('dim1')" class="p-error">
          {{ validation?.getError('dim1') }}
        </small>
      </div>

      <div>
        <label for="dim2" class="block text-xs font-semibold mb-1 text-secondary-900">
          Longueur totale
        </label>
        <InputNumber
          id="dim2"
          :model-value="dim2"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('dim2') }"
          :min="0"
          suffix=" cm"
          @update:model-value="handleDimUpdate('dim2', $event)"
          @blur="validation?.touch('dim2')"
        />
        <small v-if="validation?.hasError('dim2')" class="p-error">
          {{ validation?.getError('dim2') }}
        </small>
      </div>

      <div>
        <label for="dim3" class="block text-xs font-semibold mb-1 text-secondary-900">
          Longueur manche
        </label>
        <InputNumber
          id="dim3"
          :model-value="dim3"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('dim3') }"
          :min="0"
          suffix=" cm"
          @update:model-value="handleDimUpdate('dim3', $event)"
          @blur="validation?.touch('dim3')"
        />
        <small v-if="validation?.hasError('dim3')" class="p-error">
          {{ validation?.getError('dim3') }}
        </small>
      </div>

      <div>
        <label for="dim4" class="block text-xs font-semibold mb-1 text-secondary-900">
          Tour de taille
        </label>
        <InputNumber
          id="dim4"
          :model-value="dim4"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('dim4') }"
          :min="0"
          suffix=" cm"
          @update:model-value="handleDimUpdate('dim4', $event)"
          @blur="validation?.touch('dim4')"
        />
        <small v-if="validation?.hasError('dim4')" class="p-error">
          {{ validation?.getError('dim4') }}
        </small>
      </div>

      <div>
        <label for="dim5" class="block text-xs font-semibold mb-1 text-secondary-900">
          Tour de hanches
        </label>
        <InputNumber
          id="dim5"
          :model-value="dim5"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('dim5') }"
          :min="0"
          suffix=" cm"
          @update:model-value="handleDimUpdate('dim5', $event)"
          @blur="validation?.touch('dim5')"
        />
        <small v-if="validation?.hasError('dim5')" class="p-error">
          {{ validation?.getError('dim5') }}
        </small>
      </div>

      <div>
        <label for="dim6" class="block text-xs font-semibold mb-1 text-secondary-900">
          Entrejambe
        </label>
        <InputNumber
          id="dim6"
          :model-value="dim6"
          class="w-full"
          :class="{ 'p-invalid': validation?.hasError('dim6') }"
          :min="0"
          suffix=" cm"
          @update:model-value="handleDimUpdate('dim6', $event)"
          @blur="validation?.touch('dim6')"
        />
        <small v-if="validation?.hasError('dim6')" class="p-error">
          {{ validation?.getError('dim6') }}
        </small>
      </div>
    </div>

    <p v-if="adjustedSize" class="text-xs text-green-600 mt-3">
      💡 Taille ajustée: <strong>{{ adjustedSize }}</strong>
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import InputNumber from 'primevue/inputnumber'
import type { useProductFormValidation } from '~/composables/useProductFormValidation'

/**
 * Composant pour les dimensions du produit
 *
 * Gère les 6 dimensions (cm) et calcule automatiquement
 * la taille ajustée (format jean W/L)
 */

interface Props {
  dim1?: number | null
  dim2?: number | null
  dim3?: number | null
  dim4?: number | null
  dim5?: number | null
  dim6?: number | null
  validation?: ReturnType<typeof useProductFormValidation>
}

const props = withDefaults(defineProps<Props>(), {
  dim1: null,
  dim2: null,
  dim3: null,
  dim4: null,
  dim5: null,
  dim6: null
})

const emit = defineEmits<{
  'update:dim1': [value: number | null]
  'update:dim2': [value: number | null]
  'update:dim3': [value: number | null]
  'update:dim4': [value: number | null]
  'update:dim5': [value: number | null]
  'update:dim6': [value: number | null]
}>()

/**
 * Calculer la taille ajustée automatiquement si dim1 et dim6 sont fournis
 * Format jean standard : W{dim1}/L{dim6}
 */
const adjustedSize = computed(() => {
  if (props.dim1 && props.dim6) {
    return `W${props.dim1}/L${props.dim6}`
  } else if (props.dim1) {
    return `W${props.dim1}`
  }
  return null
})

/**
 * Gérer la mise à jour d'un champ dimension avec validation
 */
const handleDimUpdate = (field: 'dim1' | 'dim2' | 'dim3' | 'dim4' | 'dim5' | 'dim6', value: number | null) => {
  // Émettre l'événement correspondant
  switch (field) {
    case 'dim1': emit('update:dim1', value); break
    case 'dim2': emit('update:dim2', value); break
    case 'dim3': emit('update:dim3', value); break
    case 'dim4': emit('update:dim4', value); break
    case 'dim5': emit('update:dim5', value); break
    case 'dim6': emit('update:dim6', value); break
  }

  // Valider le champ si validation est fournie et le champ a déjà été touché
  if (props.validation && props.validation.touched.value.has(field)) {
    props.validation.validateAndSetError(field, value)
  }
}
</script>

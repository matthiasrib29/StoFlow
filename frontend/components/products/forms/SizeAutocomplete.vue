<template>
  <div class="size-autocomplete">
    <label class="block text-xs font-semibold mb-1 text-secondary-900">
      Taille *
    </label>

    <AutoComplete
      :model-value="modelValue"
      :suggestions="suggestions"
      :min-length="1"
      :delay="100"
      placeholder="Ex: M, L, 42, W32/L34..."
      class="w-full"
      :class="{ 'p-invalid': hasError }"
      :loading="loading"
      @complete="handleSearch"
      @update:model-value="handleValueChange"
      @item-select="handleItemSelect"
      @blur="handleBlur"
    >
      <template #option="{ option }">
        <div class="flex items-center gap-2">
          <span class="font-medium">{{ option }}</span>
        </div>
      </template>
    </AutoComplete>

    <!-- Indication de taille normalisée -->
    <div v-if="normalizedSize" class="flex items-center gap-1 mt-1">
      <i class="pi pi-check-circle text-green-500 text-xs" />
      <span class="text-xs text-green-600">
        Taille standardisée: {{ normalizedSize }}
      </span>
    </div>

    <!-- Indication de taille libre -->
    <div v-else-if="modelValue && !loading" class="flex items-center gap-1 mt-1">
      <i class="pi pi-info-circle text-blue-500 text-xs" />
      <span class="text-xs text-blue-600">
        Taille personnalisée (sera créée si inexistante)
      </span>
    </div>

    <!-- Message d'erreur -->
    <small v-if="hasError && errorMessage" class="p-error">
      {{ errorMessage }}
    </small>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  modelValue: string
  hasError?: boolean
  errorMessage?: string
}

const props = withDefaults(defineProps<Props>(), {
  hasError: false,
  errorMessage: ''
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:normalized': [value: string | null]
  'blur': []
}>()

// État
const suggestions = ref<string[]>([])
const loading = ref(false)
const normalizedSize = ref<string | null>(null)
const allSizes = ref<string[]>([])

// Handle value changes from AutoComplete (typing or selection)
const handleValueChange = (value: string | null) => {
  const strValue = value || ''
  emit('update:modelValue', strValue)
  checkNormalized(strValue)
}

// Handle item selection from dropdown
const handleItemSelect = (event: { value: string }) => {
  const strValue = event.value || ''
  emit('update:modelValue', strValue)
  checkNormalized(strValue)
}

// API
const { get } = useApi()

// Charger toutes les tailles au montage
onMounted(async () => {
  try {
    const response = await get<{ sizes: Array<{ name_en: string }> }>('/attributes/sizes')
    if (response?.sizes) {
      allSizes.value = response.sizes.map(s => s.name_en)
    }
  } catch (error) {
    console.error('Failed to load sizes:', error)
  }
})

// Recherche de suggestions
const handleSearch = (event: { query: string }) => {
  const query = event.query.toLowerCase().trim()

  if (!query) {
    suggestions.value = allSizes.value.slice(0, 10)
    return
  }

  // Filtrer les tailles qui correspondent
  suggestions.value = allSizes.value
    .filter(size => size.toLowerCase().includes(query))
    .slice(0, 10)

  // Ajouter la valeur saisie si elle n'existe pas
  if (!suggestions.value.some(s => s.toLowerCase() === query)) {
    suggestions.value.push(event.query)
  }
}

// Handle blur - emit blur event
const handleBlur = () => {
  emit('blur')
}

// Vérifier si la taille est normalisée
const checkNormalized = (value: string) => {
  if (!value) {
    normalizedSize.value = null
    emit('update:normalized', null)
    return
  }

  // Chercher une correspondance exacte (case insensitive)
  const match = allSizes.value.find(
    s => s.toLowerCase() === value.toLowerCase()
  )

  if (match) {
    normalizedSize.value = match
    emit('update:normalized', match)
  } else {
    normalizedSize.value = null
    emit('update:normalized', null)
  }
}

// Vérifier la normalisation quand modelValue change
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    checkNormalized(newVal)
  }
}, { immediate: true })
</script>

<style scoped>
.size-autocomplete :deep(.p-autocomplete) {
  width: 100%;
}

.size-autocomplete :deep(.p-autocomplete-input) {
  width: 100%;
}
</style>

<template>
  <Dialog
    v-model:visible="visible"
    :header="dialogTitle"
    :modal="true"
    :style="{ width: '600px' }"
    :closable="!isLoading"
    @hide="onClose"
  >
    <div class="space-y-4">
      <!-- Brand Form -->
      <template v-if="type === 'brands'">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (EN) *</label>
            <InputText
              v-model="form.name"
              class="w-full"
              :disabled="isEdit"
              placeholder="Brand name"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (FR)</label>
            <InputText v-model="form.name_fr" class="w-full" placeholder="Nom de la marque" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <Textarea v-model="form.description" class="w-full" rows="2" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Vinted ID</label>
            <InputText v-model="form.vinted_id" class="w-full" placeholder="ID Vinted" />
          </div>
          <div class="flex items-center pt-6">
            <Checkbox v-model="form.monitoring" :binary="true" inputId="monitoring" />
            <label for="monitoring" class="ml-2 text-sm text-gray-700">Monitoring active</label>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Sector Jeans</label>
            <Select
              v-model="form.sector_jeans"
              :options="sectorOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Choisir..."
              class="w-full"
              showClear
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Sector Jacket</label>
            <Select
              v-model="form.sector_jacket"
              :options="sectorOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Choisir..."
              class="w-full"
              showClear
            />
          </div>
        </div>
      </template>

      <!-- Category Form -->
      <template v-else-if="type === 'categories'">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (EN) *</label>
            <InputText
              v-model="form.name_en"
              class="w-full"
              :disabled="isEdit"
              placeholder="Category name"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Categorie parente</label>
            <InputText v-model="form.parent_category" class="w-full" placeholder="Parent category" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (FR)</label>
            <InputText v-model="form.name_fr" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (DE)</label>
            <InputText v-model="form.name_de" class="w-full" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (IT)</label>
            <InputText v-model="form.name_it" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (ES)</label>
            <InputText v-model="form.name_es" class="w-full" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Genres disponibles</label>
          <MultiSelect
            v-model="form.genders"
            :options="genderOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Selectionner..."
            class="w-full"
          />
        </div>
      </template>

      <!-- Color Form -->
      <template v-else-if="type === 'colors'">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (EN) *</label>
            <InputText
              v-model="form.name_en"
              class="w-full"
              :disabled="isEdit"
              placeholder="Color name"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Code hex</label>
            <div class="flex gap-2">
              <InputText v-model="form.hex_code" class="flex-1" placeholder="#RRGGBB" />
              <div
                v-if="form.hex_code"
                class="w-10 h-10 rounded border"
                :style="{ backgroundColor: form.hex_code }"
              />
            </div>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (FR)</label>
            <InputText v-model="form.name_fr" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (DE)</label>
            <InputText v-model="form.name_de" class="w-full" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (IT)</label>
            <InputText v-model="form.name_it" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (ES)</label>
            <InputText v-model="form.name_es" class="w-full" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (NL)</label>
            <InputText v-model="form.name_nl" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (PL)</label>
            <InputText v-model="form.name_pl" class="w-full" />
          </div>
        </div>
      </template>

      <!-- Material Form -->
      <template v-else-if="type === 'materials'">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (EN) *</label>
            <InputText
              v-model="form.name_en"
              class="w-full"
              :disabled="isEdit"
              placeholder="Material name"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Vinted ID</label>
            <InputNumber v-model="form.vinted_id" class="w-full" placeholder="ID Vinted" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (FR)</label>
            <InputText v-model="form.name_fr" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (DE)</label>
            <InputText v-model="form.name_de" class="w-full" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (IT)</label>
            <InputText v-model="form.name_it" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (ES)</label>
            <InputText v-model="form.name_es" class="w-full" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (NL)</label>
            <InputText v-model="form.name_nl" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nom (PL)</label>
            <InputText v-model="form.name_pl" class="w-full" />
          </div>
        </div>
      </template>
    </div>

    <template #footer>
      <Button label="Annuler" severity="secondary" @click="onClose" :disabled="isLoading" />
      <Button :label="isEdit ? 'Modifier' : 'Creer'" @click="onSave" :loading="isLoading" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import Select from 'primevue/select'
import MultiSelect from 'primevue/multiselect'
import Checkbox from 'primevue/checkbox'
import type { AttributeType, AdminAttribute } from '~/composables/useAdminAttributes'

interface Props {
  type: AttributeType
  item?: AdminAttribute | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  save: [data: Record<string, any>]
}>()

// State
const visible = ref(true)
const isLoading = ref(false)
const form = ref<Record<string, any>>({})

// Computed
const isEdit = computed(() => !!props.item)

const dialogTitle = computed(() => {
  const typeLabels: Record<AttributeType, string> = {
    brands: 'Marque',
    categories: 'Categorie',
    colors: 'Couleur',
    materials: 'Matiere',
  }
  return `${isEdit.value ? 'Modifier' : 'Nouvelle'} ${typeLabels[props.type]}`
})

// Options
const sectorOptions = [
  { label: 'Budget', value: 'BUDGET' },
  { label: 'Standard', value: 'STANDARD' },
  { label: 'Hype', value: 'HYPE' },
  { label: 'Premium', value: 'PREMIUM' },
  { label: 'Ultra Premium', value: 'ULTRA PREMIUM' },
]

const genderOptions = [
  { label: 'Hommes', value: 'men' },
  { label: 'Femmes', value: 'women' },
  { label: 'Garcons', value: 'boys' },
  { label: 'Filles', value: 'girls' },
]

// Initialize form based on type and item
const initForm = () => {
  if (props.item) {
    form.value = { ...props.item }
  } else {
    // Default values based on type
    switch (props.type) {
      case 'brands':
        form.value = {
          name: '',
          name_fr: '',
          description: '',
          vinted_id: '',
          monitoring: false,
          sector_jeans: null,
          sector_jacket: null,
        }
        break
      case 'categories':
        form.value = {
          name_en: '',
          parent_category: '',
          name_fr: '',
          name_de: '',
          name_it: '',
          name_es: '',
          genders: [],
        }
        break
      case 'colors':
        form.value = {
          name_en: '',
          name_fr: '',
          name_de: '',
          name_it: '',
          name_es: '',
          name_nl: '',
          name_pl: '',
          hex_code: '',
        }
        break
      case 'materials':
        form.value = {
          name_en: '',
          name_fr: '',
          name_de: '',
          name_it: '',
          name_es: '',
          name_nl: '',
          name_pl: '',
          vinted_id: null,
        }
        break
    }
  }
}

// Handlers
const onClose = () => {
  visible.value = false
  emit('close')
}

const onSave = () => {
  // Remove empty strings and pk field for updates
  const data: Record<string, any> = {}

  for (const [key, value] of Object.entries(form.value)) {
    if (key === 'pk') continue // Skip pk field
    if (value === '' || value === null || value === undefined) {
      // For updates, skip empty fields (they won't be changed)
      if (isEdit.value) continue
      // For creates, include null for optional fields
      data[key] = null
    } else {
      data[key] = value
    }
  }

  emit('save', data)
}

// Initialize on mount
onMounted(() => {
  initForm()
})

// Watch for item changes
watch(
  () => props.item,
  () => {
    initForm()
  }
)

// Expose loading state for parent
defineExpose({
  setLoading: (loading: boolean) => {
    isLoading.value = loading
  },
  close: () => {
    visible.value = false
  },
})
</script>

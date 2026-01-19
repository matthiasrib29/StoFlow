<template>
  <div class="page-container">
    <PageHeader
      title="Produits"
      subtitle="Configurez les templates par défaut pour vos produits"
    />

    <Card class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <div class="space-y-6">
          <!-- Templates section -->
          <div>
            <h3 class="text-lg font-bold text-secondary-900 mb-1">Templates par défaut</h3>
            <p class="text-sm text-gray-600 mb-6">
              Ces templates seront utilisés par défaut lors de la génération automatique des titres et descriptions.
            </p>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl">
              <!-- Title Format -->
              <div>
                <label class="block text-sm font-semibold text-secondary-900 mb-2">
                  Format de titre
                </label>
                <Select
                  v-model="form.titleFormat"
                  :options="titleFormatOptions"
                  option-label="label"
                  option-value="value"
                  placeholder="Sélectionner un format"
                  class="w-full"
                />
                <p class="text-xs text-gray-400 mt-1">
                  Détermine les attributs inclus dans le titre généré
                </p>
              </div>

              <!-- Description Style -->
              <div>
                <label class="block text-sm font-semibold text-secondary-900 mb-2">
                  Style de description
                </label>
                <Select
                  v-model="form.descriptionStyle"
                  :options="descriptionStyleOptions"
                  option-label="label"
                  option-value="value"
                  placeholder="Sélectionner un style"
                  class="w-full"
                />
                <p class="text-xs text-gray-400 mt-1">
                  Détermine le ton et la structure de la description
                </p>
              </div>
            </div>
          </div>

          <Divider />

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
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import type { TitleFormat, DescriptionStyle } from '~/types/textGenerator'

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
} = useProductTextGenerator()

// Form state
const form = ref<{
  titleFormat: TitleFormat | null
  descriptionStyle: DescriptionStyle | null
}>({
  titleFormat: null,
  descriptionStyle: null,
})

// Load settings on mount
onMounted(async () => {
  await loadSettings()
  if (settings.value) {
    form.value.titleFormat = settings.value.default_title_format
    form.value.descriptionStyle = settings.value.default_description_style
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

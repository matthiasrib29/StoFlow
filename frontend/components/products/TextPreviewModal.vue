<template>
  <Dialog
    :visible="visible"
    modal
    header="Textes generes"
    :style="{ width: '800px', maxWidth: '90vw' }"
    @update:visible="$emit('update:visible', $event)"
  >
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <ProgressSpinner
        style="width: 50px; height: 50px"
        stroke-width="4"
      />
    </div>

    <!-- Error state -->
    <Message v-else-if="error" severity="error" :closable="false" class="mb-4">
      {{ error }}
    </Message>

    <!-- Empty state -->
    <div v-else-if="!hasTitles && !hasDescriptions" class="text-center py-8 text-gray-500">
      <i class="pi pi-inbox text-4xl mb-4 block" />
      <p>Aucun texte genere.</p>
      <p class="text-sm mt-2">Remplissez les attributs du produit et reessayez.</p>
    </div>

    <!-- Results -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Titles section -->
      <div v-if="hasTitles">
        <h3 class="text-sm font-semibold text-secondary-900 mb-3 flex items-center gap-2">
          <i class="pi pi-tag" />
          Titres
        </h3>
        <div class="space-y-3">
          <div
            v-for="(title, format) in titles"
            :key="format"
            class="border border-gray-200 rounded-lg p-4 cursor-pointer transition-all"
            :class="selectedTitle === format ? 'ring-2 ring-primary-400 bg-primary-50' : 'hover:border-gray-300'"
            @click="selectTitle(format)"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-medium text-gray-500 uppercase">
                {{ getTitleFormatLabel(format) }}
              </span>
              <div class="flex items-center gap-1">
                <Button
                  type="button"
                  icon="pi pi-copy"
                  text
                  rounded
                  size="small"
                  v-tooltip.top="'Copier'"
                  @click.stop="copyToClipboard(title)"
                />
                <i
                  v-if="selectedTitle === format"
                  class="pi pi-check-circle text-primary-500"
                />
              </div>
            </div>
            <p class="text-sm text-secondary-900">{{ title }}</p>
            <Button
              v-if="selectedTitle === format"
              type="button"
              label="Utiliser ce titre"
              icon="pi pi-check"
              size="small"
              class="mt-3 bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
              @click.stop="handleSelectTitle"
            />
          </div>
        </div>
      </div>

      <!-- Descriptions section -->
      <div v-if="hasDescriptions">
        <h3 class="text-sm font-semibold text-secondary-900 mb-3 flex items-center gap-2">
          <i class="pi pi-align-left" />
          Descriptions
        </h3>
        <div class="space-y-3">
          <div
            v-for="(description, style) in descriptions"
            :key="style"
            class="border border-gray-200 rounded-lg p-4 cursor-pointer transition-all"
            :class="selectedDescription === style ? 'ring-2 ring-primary-400 bg-primary-50' : 'hover:border-gray-300'"
            @click="selectDescription(style)"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-medium text-gray-500 uppercase">
                {{ getDescriptionStyleLabel(style) }}
              </span>
              <div class="flex items-center gap-1">
                <Button
                  type="button"
                  icon="pi pi-copy"
                  text
                  rounded
                  size="small"
                  v-tooltip.top="'Copier'"
                  @click.stop="copyToClipboard(description)"
                />
                <i
                  v-if="selectedDescription === style"
                  class="pi pi-check-circle text-primary-500"
                />
              </div>
            </div>
            <p class="text-sm text-secondary-900 whitespace-pre-line line-clamp-4">{{ description }}</p>
            <Button
              v-if="selectedDescription === style"
              type="button"
              label="Utiliser cette description"
              icon="pi pi-check"
              size="small"
              class="mt-3 bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
              @click.stop="handleSelectDescription"
            />
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full">
        <Button
          type="button"
          label="Fermer"
          icon="pi pi-times"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="$emit('update:visible', false)"
        />
        <Button
          type="button"
          label="Appliquer les deux"
          icon="pi pi-check-double"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          :disabled="!canApplyBoth"
          @click="handleApplyAll"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { TITLE_FORMAT_LABELS, DESCRIPTION_STYLE_LABELS } from '~/types/textGenerator'
import type { TitleFormat, DescriptionStyle } from '~/types/textGenerator'

interface Props {
  visible: boolean
  titles: Record<string, string>
  descriptions: Record<string, string>
  loading?: boolean
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  error: null
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'select-title': [format: string, title: string]
  'select-description': [style: string, description: string]
  'apply-all': [data: { titleFormat: string; title: string; descriptionStyle: string; description: string }]
}>()

// Selection state
const selectedTitle = ref<string | null>(null)
const selectedDescription = ref<string | null>(null)

// Computed
const hasTitles = computed(() => Object.keys(props.titles).length > 0)
const hasDescriptions = computed(() => Object.keys(props.descriptions).length > 0)
const canApplyBoth = computed(() => selectedTitle.value && selectedDescription.value)

// Reset selection when modal opens with new data
watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    // Auto-select first title and description
    const titleKeys = Object.keys(props.titles)
    const descKeys = Object.keys(props.descriptions)
    selectedTitle.value = titleKeys.length > 0 ? titleKeys[0] : null
    selectedDescription.value = descKeys.length > 0 ? descKeys[0] : null
  }
})

// Get label for title format
const getTitleFormatLabel = (format: string): string => {
  const formatNum = Number(format) as TitleFormat
  return TITLE_FORMAT_LABELS[formatNum] || `Format ${format}`
}

// Get label for description style
const getDescriptionStyleLabel = (style: string): string => {
  const styleNum = Number(style) as DescriptionStyle
  return DESCRIPTION_STYLE_LABELS[styleNum] || `Style ${style}`
}

// Selection handlers
const selectTitle = (format: string) => {
  selectedTitle.value = format
}

const selectDescription = (style: string) => {
  selectedDescription.value = style
}

// Action handlers
const handleSelectTitle = () => {
  if (selectedTitle.value) {
    emit('select-title', selectedTitle.value, props.titles[selectedTitle.value])
  }
}

const handleSelectDescription = () => {
  if (selectedDescription.value) {
    emit('select-description', selectedDescription.value, props.descriptions[selectedDescription.value])
  }
}

const handleApplyAll = () => {
  if (selectedTitle.value && selectedDescription.value) {
    emit('apply-all', {
      titleFormat: selectedTitle.value,
      title: props.titles[selectedTitle.value],
      descriptionStyle: selectedDescription.value,
      description: props.descriptions[selectedDescription.value]
    })
    emit('update:visible', false)
  }
}

// Copy to clipboard
const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
  }
  catch (e) {
    console.error('Failed to copy to clipboard:', e)
  }
}
</script>

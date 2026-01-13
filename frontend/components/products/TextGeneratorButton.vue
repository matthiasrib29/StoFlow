<template>
  <Button
    type="button"
    :label="label"
    icon="pi pi-bolt"
    class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
    :loading="textGenerator.loading.value"
    :disabled="disabled || textGenerator.loading.value"
    v-tooltip.top="'Generer automatiquement titre et description SEO'"
    @click="handleGenerate"
  >
    <template v-if="$slots.default" #default>
      <slot />
    </template>
  </Button>
</template>

<script setup lang="ts">
import type { TextPreviewInput } from '~/types/textGenerator'

interface Props {
  productId?: number
  attributes?: TextPreviewInput
  disabled?: boolean
  label?: string
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  label: 'Generer textes'
})

const emit = defineEmits<{
  'generate': [results: { titles: Record<string, string>; descriptions: Record<string, string> }]
  'error': [message: string]
}>()

const textGenerator = useProductTextGenerator()

const handleGenerate = async () => {
  try {
    // Mode 1: Generate from existing product
    if (props.productId) {
      await textGenerator.generate(props.productId)
    }
    // Mode 2: Preview from raw attributes
    else if (props.attributes) {
      await textGenerator.preview(props.attributes)
    }
    else {
      emit('error', 'Aucun produit ou attributs fournis')
      return
    }

    // Check for errors
    if (textGenerator.error.value) {
      emit('error', textGenerator.error.value)
      return
    }

    // Emit results
    emit('generate', {
      titles: textGenerator.titles.value,
      descriptions: textGenerator.descriptions.value
    })
  }
  catch (e) {
    const message = e instanceof Error ? e.message : 'Erreur lors de la generation'
    emit('error', message)
  }
}
</script>

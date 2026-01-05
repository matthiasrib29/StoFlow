<template>
  <Dialog
    :visible="visible"
    modal
    header="Modifier le prix"
    class="w-[400px]"
    @update:visible="$emit('update:visible', $event)"
  >
    <div v-if="publication" class="space-y-4">
      <div>
        <p class="font-semibold text-secondary-900 mb-2">{{ publication.product?.title }}</p>
        <p class="text-sm text-gray-600 mb-4">Prix actuel: {{ formatCurrency(publication.price) }}</p>
      </div>

      <div>
        <label class="block text-sm font-semibold text-secondary-900 mb-2">Nouveau prix</label>
        <InputNumber
          v-model="localPrice"
          mode="currency"
          currency="EUR"
          locale="fr-FR"
          class="w-full"
          :min="0"
          :max-fraction-digits="2"
        />
      </div>
    </div>

    <template #footer>
      <Button
        label="Annuler"
        icon="pi pi-times"
        class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
        @click="$emit('update:visible', false)"
      />
      <Button
        label="Sauvegarder"
        icon="pi pi-check"
        class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
        @click="handleSave"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { formatCurrency } from '~/utils/formatters'

interface Publication {
  id: string
  price: number
  product?: {
    id: number
    title: string
  }
}

const props = defineProps<{
  visible: boolean
  publication: Publication | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'save': [price: number]
}>()

const localPrice = ref(0)

// Sync local price when publication changes
watch(() => props.publication, (pub) => {
  if (pub) {
    localPrice.value = pub.price
  }
}, { immediate: true })

const handleSave = () => {
  emit('save', localPrice.value)
}
</script>

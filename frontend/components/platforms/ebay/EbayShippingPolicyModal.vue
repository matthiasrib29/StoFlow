<template>
  <Dialog
    :visible="visible"
    modal
    header="Nouvelle politique d'expédition"
    class="w-[500px]"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="space-y-4">
      <div>
        <label class="block text-sm font-semibold text-secondary-900 mb-2">Nom de la politique *</label>
        <InputText v-model="form.name" class="w-full" placeholder="Ex: Livraison Standard" />
      </div>

      <div>
        <label class="block text-sm font-semibold text-secondary-900 mb-2">Description</label>
        <Textarea v-model="form.description" class="w-full" rows="2" placeholder="Description optionnelle" />
      </div>

      <div>
        <label class="block text-sm font-semibold text-secondary-900 mb-2">Type d'expédition</label>
        <Select
          v-model="form.type"
          :options="shippingTypes"
          option-label="label"
          option-value="value"
          class="w-full"
        />
      </div>

      <div v-if="form.type !== 'free_shipping'">
        <label class="block text-sm font-semibold text-secondary-900 mb-2">Coût d'expédition (EUR)</label>
        <InputNumber
          v-model="form.cost"
          mode="currency"
          currency="EUR"
          locale="fr-FR"
          class="w-full"
          :min="0"
        />
      </div>

      <div>
        <label class="block text-sm font-semibold text-secondary-900 mb-2">Délai de traitement (jours)</label>
        <InputNumber v-model="form.handlingTime" class="w-full" :min="0" :max="30" />
      </div>

      <div class="flex items-center gap-2">
        <Checkbox v-model="form.isDefault" :binary="true" />
        <label class="text-sm text-secondary-900">Définir comme politique par défaut</label>
      </div>
    </div>

    <template #footer>
      <Button
        label="Annuler"
        class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
        @click="$emit('update:visible', false)"
      />
      <Button
        label="Créer"
        icon="pi pi-check"
        class="bg-blue-500 hover:bg-blue-600 text-white border-0 font-semibold"
        @click="handleCreate"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
interface ShippingPolicyForm {
  name: string
  description: string
  type: 'flat_rate' | 'calculated' | 'free_shipping'
  cost: number
  handlingTime: number
  isDefault: boolean
}

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'create': [policy: ShippingPolicyForm]
}>()

const shippingTypes = [
  { label: 'Forfait', value: 'flat_rate' },
  { label: 'Calculé', value: 'calculated' },
  { label: 'Gratuit', value: 'free_shipping' }
]

const form = reactive<ShippingPolicyForm>({
  name: '',
  description: '',
  type: 'flat_rate',
  cost: 5.99,
  handlingTime: 1,
  isDefault: false
})

const handleCreate = () => {
  emit('create', { ...form })
  // Reset form
  form.name = ''
  form.description = ''
  form.type = 'flat_rate'
  form.cost = 5.99
  form.handlingTime = 1
  form.isDefault = false
}
</script>

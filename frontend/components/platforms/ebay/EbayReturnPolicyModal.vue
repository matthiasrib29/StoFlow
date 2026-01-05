<template>
  <Dialog
    :visible="visible"
    modal
    header="Nouvelle politique de retour"
    class="w-[500px]"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="space-y-4">
      <div>
        <label class="block text-sm font-semibold text-secondary-900 mb-2">Nom de la politique *</label>
        <InputText v-model="form.name" class="w-full" placeholder="Ex: Retours 30 jours" />
      </div>

      <div class="flex items-center gap-2">
        <Checkbox v-model="form.returnsAccepted" :binary="true" />
        <label class="text-sm text-secondary-900">Accepter les retours</label>
      </div>

      <div v-if="form.returnsAccepted">
        <label class="block text-sm font-semibold text-secondary-900 mb-2">Période de retour (jours)</label>
        <InputNumber v-model="form.returnPeriod" class="w-full" :min="1" :max="60" />
      </div>

      <div v-if="form.returnsAccepted">
        <label class="block text-sm font-semibold text-secondary-900 mb-2">Frais de retour payés par</label>
        <Select
          v-model="form.shippingCostPaidBy"
          :options="shippingCostOptions"
          option-label="label"
          option-value="value"
          class="w-full"
        />
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
interface ReturnPolicyForm {
  name: string
  returnsAccepted: boolean
  returnPeriod: number
  shippingCostPaidBy: 'buyer' | 'seller'
  isDefault: boolean
}

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'create': [policy: ReturnPolicyForm]
}>()

const shippingCostOptions = [
  { label: 'Acheteur', value: 'buyer' },
  { label: 'Vendeur', value: 'seller' }
]

const form = reactive<ReturnPolicyForm>({
  name: '',
  returnsAccepted: true,
  returnPeriod: 30,
  shippingCostPaidBy: 'buyer',
  isDefault: false
})

const handleCreate = () => {
  emit('create', { ...form })
  // Reset form
  form.name = ''
  form.returnsAccepted = true
  form.returnPeriod = 30
  form.shippingCostPaidBy = 'buyer'
  form.isDefault = false
}
</script>

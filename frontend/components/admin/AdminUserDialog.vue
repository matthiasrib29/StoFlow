<template>
  <Dialog
    :visible="visible"
    :header="isEditing ? 'Modifier l\'utilisateur' : 'Nouvel utilisateur'"
    :style="{ width: '500px' }"
    :modal="true"
    class="p-fluid"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="space-y-4 py-4">
      <!-- Email -->
      <div class="field">
        <label for="email" class="font-medium text-sm text-gray-700 mb-1 block">Email *</label>
        <InputText
          id="email"
          v-model="localForm.email"
          type="email"
          :class="{ 'p-invalid': submitted && !localForm.email }"
          placeholder="utilisateur@exemple.com"
        />
        <small v-if="submitted && !localForm.email" class="p-error">L'email est requis</small>
      </div>

      <!-- Full Name -->
      <div class="field">
        <label for="fullName" class="font-medium text-sm text-gray-700 mb-1 block">Nom complet *</label>
        <InputText
          id="fullName"
          v-model="localForm.full_name"
          :class="{ 'p-invalid': submitted && !localForm.full_name }"
          placeholder="Jean Dupont"
        />
        <small v-if="submitted && !localForm.full_name" class="p-error">Le nom est requis</small>
      </div>

      <!-- Password -->
      <div class="field">
        <label for="password" class="font-medium text-sm text-gray-700 mb-1 block">
          {{ isEditing ? 'Nouveau mot de passe (laisser vide pour ne pas changer)' : 'Mot de passe *' }}
        </label>
        <Password
          id="password"
          v-model="localForm.password"
          :class="{ 'p-invalid': submitted && !isEditing && !localForm.password }"
          :feedback="false"
          toggle-mask
          placeholder="********"
        />
        <small v-if="submitted && !isEditing && !localForm.password" class="p-error">Le mot de passe est requis</small>
      </div>

      <!-- Role -->
      <div class="field">
        <label for="role" class="font-medium text-sm text-gray-700 mb-1 block">Rôle *</label>
        <Dropdown
          id="role"
          v-model="localForm.role"
          :options="roleOptions"
          option-label="label"
          option-value="value"
          placeholder="Sélectionner un rôle"
          :disabled="isCurrentUser"
        />
      </div>

      <!-- Subscription Tier -->
      <div class="field">
        <label for="tier" class="font-medium text-sm text-gray-700 mb-1 block">Abonnement</label>
        <Dropdown
          id="tier"
          v-model="localForm.subscription_tier"
          :options="tierOptions"
          option-label="label"
          option-value="value"
          placeholder="Sélectionner un abonnement"
        />
      </div>

      <!-- Business Name -->
      <div class="field">
        <label for="businessName" class="font-medium text-sm text-gray-700 mb-1 block">Nom de l'entreprise</label>
        <InputText
          id="businessName"
          v-model="localForm.business_name"
          placeholder="Ma Boutique"
        />
      </div>

      <!-- Is Active -->
      <div class="field flex items-center gap-3">
        <Checkbox
          id="isActive"
          v-model="localForm.is_active"
          :binary="true"
          :disabled="isCurrentUser"
        />
        <label for="isActive" class="font-medium text-sm text-gray-700">Compte actif</label>
      </div>
    </div>

    <template #footer>
      <Button
        label="Annuler"
        icon="pi pi-times"
        class="p-button-text"
        @click="$emit('update:visible', false)"
      />
      <Button
        :label="isEditing ? 'Enregistrer' : 'Créer'"
        icon="pi pi-check"
        class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
        :loading="loading"
        @click="handleSave"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
interface UserForm {
  email: string
  full_name: string
  password: string
  role: string
  subscription_tier: string
  business_name: string
  is_active: boolean
}

const props = defineProps<{
  visible: boolean
  isEditing: boolean
  isCurrentUser: boolean
  loading: boolean
  form: UserForm
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'save': [form: UserForm]
}>()

const submitted = ref(false)

const localForm = ref<UserForm>({ ...props.form })

// Sync form when props change
watch(() => props.form, (newForm) => {
  localForm.value = { ...newForm }
}, { deep: true })

watch(() => props.visible, (visible) => {
  if (visible) {
    submitted.value = false
    localForm.value = { ...props.form }
  }
})

const roleOptions = [
  { label: 'Admin', value: 'admin' },
  { label: 'Utilisateur', value: 'user' },
  { label: 'Support', value: 'support' },
]

const tierOptions = [
  { label: 'Free', value: 'free' },
  { label: 'Starter', value: 'starter' },
  { label: 'Pro', value: 'pro' },
  { label: 'Enterprise', value: 'enterprise' },
]

const handleSave = () => {
  submitted.value = true

  if (!localForm.value.email || !localForm.value.full_name) {
    return
  }

  if (!props.isEditing && !localForm.value.password) {
    return
  }

  emit('save', { ...localForm.value })
}
</script>

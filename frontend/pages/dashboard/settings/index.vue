<template>
  <div class="p-8">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-secondary-900 mb-1">Profil</h1>
      <p class="text-gray-600">Gérez vos informations personnelles</p>
    </div>

    <!-- Contenu -->
    <Card class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <div class="space-y-6">
          <!-- Informations personnelles -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-semibold text-secondary-900 mb-2">Nom complet</label>
              <InputText
                v-model="profile.fullName"
                placeholder="Votre nom complet"
                class="w-full"
              />
            </div>

            <div>
              <label class="block text-sm font-semibold text-secondary-900 mb-2">Email</label>
              <InputText
                v-model="profile.email"
                type="email"
                placeholder="votre@email.com"
                class="w-full"
              />
            </div>

            <div>
              <label class="block text-sm font-semibold text-secondary-900 mb-2">Téléphone</label>
              <InputText
                v-model="profile.phone"
                placeholder="+33 6 12 34 56 78"
                class="w-full"
              />
            </div>

            <div>
              <label class="block text-sm font-semibold text-secondary-900 mb-2">Entreprise</label>
              <InputText
                v-model="profile.company"
                placeholder="Nom de votre entreprise"
                class="w-full"
              />
            </div>
          </div>

          <Divider />

          <!-- Boutons -->
          <div class="flex justify-end gap-3">
            <Button
              label="Annuler"
              icon="pi pi-times"
              class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
              @click="resetProfile"
            />
            <Button
              label="Sauvegarder"
              icon="pi pi-save"
              class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
              @click="saveProfile"
            />
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})

const { showSuccess } = useAppToast()
const authStore = useAuthStore()

// Profile data
const profile = ref({
  fullName: authStore.user?.full_name || '',
  email: authStore.user?.email || '',
  phone: '',
  company: authStore.user?.tenant_name || ''
})

// Methods
const saveProfile = () => {
  showSuccess('Profil sauvegardé', 'Vos informations ont été mises à jour', 3000)
}

const resetProfile = () => {
  profile.value = {
    fullName: authStore.user?.full_name || '',
    email: authStore.user?.email || '',
    phone: '',
    company: authStore.user?.tenant_name || ''
  }
}
</script>

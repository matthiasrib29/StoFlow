<template>
  <div class="page-container">
    <PageHeader
      title="Sécurité"
      subtitle="Gérez la sécurité de votre compte"
    />

    <!-- Contenu -->
    <div class="space-y-6">
      <!-- Changement de mot de passe -->
      <Card class="shadow-sm modern-rounded border border-gray-100">
        <template #content>
          <div class="space-y-6">
            <div>
              <h3 class="text-lg font-bold text-secondary-900 mb-1">Changer le mot de passe</h3>
              <p class="text-sm text-gray-600 mb-4">Mettez à jour votre mot de passe régulièrement pour plus de sécurité</p>
            </div>

            <div class="grid grid-cols-1 gap-4 max-w-md">
              <div>
                <label class="block text-sm font-semibold text-secondary-900 mb-2">Mot de passe actuel</label>
                <Password
                  v-model="passwords.current"
                  placeholder="Votre mot de passe actuel"
                  class="w-full"
                  :feedback="false"
                  toggle-mask
                />
              </div>

              <div>
                <label class="block text-sm font-semibold text-secondary-900 mb-2">Nouveau mot de passe</label>
                <Password
                  v-model="passwords.new"
                  placeholder="Nouveau mot de passe"
                  class="w-full"
                  toggle-mask
                />
              </div>

              <div>
                <label class="block text-sm font-semibold text-secondary-900 mb-2">Confirmer le mot de passe</label>
                <Password
                  v-model="passwords.confirm"
                  placeholder="Confirmer le mot de passe"
                  class="w-full"
                  :feedback="false"
                  toggle-mask
                />
              </div>
            </div>

            <div class="flex justify-end">
              <Button
                label="Mettre à jour le mot de passe"
                icon="pi pi-lock"
                class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
                @click="updatePassword"
              />
            </div>
          </div>
        </template>
      </Card>

      <!-- MVP1: 2FA et Sessions actives désactivés - voir commentaire en bas -->
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})

const { showSuccess, showError } = useAppToast()

// Password form
const passwords = ref({
  current: '',
  new: '',
  confirm: ''
})

// Methods
const updatePassword = () => {
  if (!passwords.value.current || !passwords.value.new || !passwords.value.confirm) {
    showError('Erreur', 'Veuillez remplir tous les champs')
    return
  }

  if (passwords.value.new !== passwords.value.confirm) {
    showError('Erreur', 'Les mots de passe ne correspondent pas')
    return
  }

  showSuccess('Mot de passe mis à jour', 'Votre mot de passe a été changé avec succès', 3000)
  passwords.value = { current: '', new: '', confirm: '' }
}
</script>

<!--
MVP1: Sections 2FA et Sessions actives désactivées - Code original commenté

<Card class="shadow-sm modern-rounded border border-gray-100">
  <template #content>
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-bold text-secondary-900 mb-1">Authentification à deux facteurs</h3>
          <p class="text-sm text-gray-600">Ajoutez une couche de sécurité supplémentaire à votre compte</p>
        </div>
        <ToggleSwitch v-model="twoFactorEnabled" />
      </div>

      <div v-if="!twoFactorEnabled" class="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div class="flex items-start gap-3">
          <i class="pi pi-exclamation-triangle text-amber-500 mt-0.5" />
          <div>
            <p class="font-medium text-amber-800">2FA non activé</p>
            <p class="text-sm text-amber-700">Nous recommandons fortement d'activer l'authentification à deux facteurs pour protéger votre compte.</p>
          </div>
        </div>
      </div>

      <div v-else class="bg-green-50 border border-green-200 rounded-lg p-4">
        <div class="flex items-start gap-3">
          <i class="pi pi-check-circle text-green-500 mt-0.5" />
          <div>
            <p class="font-medium text-green-800">2FA activé</p>
            <p class="text-sm text-green-700">Votre compte est protégé par l'authentification à deux facteurs.</p>
          </div>
        </div>
      </div>
    </div>
  </template>
</Card>

<Card class="shadow-sm modern-rounded border border-gray-100">
  <template #content>
    <div class="space-y-4">
      <div>
        <h3 class="text-lg font-bold text-secondary-900 mb-1">Sessions actives</h3>
        <p class="text-sm text-gray-600">Gérez les appareils connectés à votre compte</p>
      </div>

      <div class="space-y-3">
        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div class="flex items-center gap-3">
            <i class="pi pi-desktop text-gray-600 text-xl" />
            <div>
              <p class="font-medium text-secondary-900">Session actuelle</p>
              <p class="text-sm text-gray-600">Chrome sur Linux - Dernière activité: maintenant</p>
            </div>
          </div>
          <span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">Active</span>
        </div>
      </div>

      <div class="flex justify-end">
        <Button
          label="Déconnecter toutes les autres sessions"
          icon="pi pi-sign-out"
          class="bg-red-100 hover:bg-red-200 text-red-700 border-0"
          size="small"
        />
      </div>
    </div>
  </template>
</Card>

Script pour 2FA:
const twoFactorEnabled = ref(false)
-->

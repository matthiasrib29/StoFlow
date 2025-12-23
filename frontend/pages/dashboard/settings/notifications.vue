<template>
  <div class="p-8">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-secondary-900 mb-1">Notifications</h1>
      <p class="text-gray-600">Gérez vos préférences de notifications</p>
    </div>

    <!-- Bientôt disponible -->
    <Card class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <div class="flex flex-col items-center justify-center py-12 text-center">
          <i class="pi pi-clock text-6xl text-gray-300 mb-4" />
          <h3 class="text-xl font-semibold text-secondary-900 mb-2">Bientôt disponible</h3>
          <p class="text-gray-600 max-w-md">
            La gestion des notifications sera disponible dans une prochaine version.
          </p>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})
</script>

<!--
MVP1: Page Notifications désactivée - Code original commenté

<template>
  <div class="p-8">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-secondary-900 mb-1">Notifications</h1>
      <p class="text-gray-600">Gérez vos préférences de notifications</p>
    </div>

    <Card class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <div class="space-y-6">
          <div>
            <h3 class="text-lg font-bold text-secondary-900 mb-4">Notifications par email</h3>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium text-secondary-900">Nouvelles ventes</p>
                  <p class="text-sm text-gray-600">Recevoir un email lors d'une nouvelle vente</p>
                </div>
                <ToggleSwitch v-model="notifications.emailSales" />
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium text-secondary-900">Messages</p>
                  <p class="text-sm text-gray-600">Recevoir un email pour les nouveaux messages</p>
                </div>
                <ToggleSwitch v-model="notifications.emailMessages" />
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium text-secondary-900">Mises à jour produits</p>
                  <p class="text-sm text-gray-600">Notifications sur l'état de vos produits</p>
                </div>
                <ToggleSwitch v-model="notifications.emailProducts" />
              </div>
            </div>
          </div>

          <Divider />

          <div>
            <h3 class="text-lg font-bold text-secondary-900 mb-4">Notifications push</h3>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium text-secondary-900">Alertes importantes</p>
                  <p class="text-sm text-gray-600">Erreurs de synchronisation, problèmes de compte</p>
                </div>
                <ToggleSwitch v-model="notifications.pushAlerts" />
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium text-secondary-900">Rappels</p>
                  <p class="text-sm text-gray-600">Rappels pour les actions en attente</p>
                </div>
                <ToggleSwitch v-model="notifications.pushReminders" />
              </div>
            </div>
          </div>

          <Divider />

          <div class="flex justify-end gap-3">
            <Button
              label="Annuler"
              icon="pi pi-times"
              class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
              @click="resetNotifications"
            />
            <Button
              label="Sauvegarder"
              icon="pi pi-save"
              class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
              @click="saveNotifications"
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

const notifications = ref({
  emailSales: true,
  emailMessages: true,
  emailProducts: false,
  pushAlerts: true,
  pushReminders: false
})

const saveNotifications = () => {
  showSuccess('Notifications sauvegardées', 'Vos préférences ont été mises à jour', 3000)
}

const resetNotifications = () => {
  notifications.value = {
    emailSales: true,
    emailMessages: true,
    emailProducts: false,
    pushAlerts: true,
    pushReminders: false
  }
}
</script>
-->

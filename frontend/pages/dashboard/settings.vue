<template>
  <div class="p-4 lg:p-8">
    <!-- Page Header -->
    <div class="mb-6 lg:mb-8">
      <h1 class="text-2xl lg:text-3xl font-bold text-secondary-900 mb-1">Paramètres</h1>
      <p class="text-gray-600 text-sm lg:text-base">Gérez votre profil et vos préférences</p>
    </div>

    <!-- Tabs -->
    <Tabs v-model:value="activeTab" class="settings-tabs">
      <TabList class="overflow-x-auto flex-nowrap">
        <Tab value="0" class="whitespace-nowrap">Profil</Tab>
        <Tab value="1" class="whitespace-nowrap">Notifications</Tab>
        <Tab value="2" class="whitespace-nowrap">Sécurité</Tab>
        <Tab value="3" class="whitespace-nowrap">Préférences</Tab>
        <Tab value="4" class="whitespace-nowrap">Intégrations</Tab>
      </TabList>
      <TabPanels>
      <!-- Onglet: Profil -->
      <TabPanel value="0">
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="space-y-6">
              <!-- Photo de profil -->
              <div class="flex items-center gap-6">
                <div class="w-24 h-24 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                  <i class="pi pi-user text-primary-600 text-4xl"/>
                </div>
                <div>
                  <h3 class="text-lg font-bold text-secondary-900 mb-1">Photo de profil</h3>
                  <p class="text-sm text-gray-600 mb-3">Choisissez une photo pour votre compte</p>
                  <Button
                    label="Changer la photo"
                    icon="pi pi-upload"
                    class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
                    size="small"
                  />
                </div>
              </div>

              <Divider />

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
      </TabPanel>

      <!-- Onglet: Notifications -->
      <TabPanel value="1">
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="space-y-6">
              <div>
                <h3 class="text-lg font-bold text-secondary-900 mb-1">Email</h3>
                <p class="text-sm text-gray-600 mb-4">Recevez des notifications par email</p>

                <div class="space-y-4">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-semibold text-secondary-900">Ventes</p>
                      <p class="text-sm text-gray-600">Notification quand un produit est vendu</p>
                    </div>
                    <ToggleSwitch v-model="notifications.email.sales" />
                  </div>

                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-semibold text-secondary-900">Nouvelles publications</p>
                      <p class="text-sm text-gray-600">Confirmation de publication sur les plateformes</p>
                    </div>
                    <ToggleSwitch v-model="notifications.email.publications" />
                  </div>

                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-semibold text-secondary-900">Erreurs</p>
                      <p class="text-sm text-gray-600">Alertes en cas d'erreur de synchronisation</p>
                    </div>
                    <ToggleSwitch v-model="notifications.email.errors" />
                  </div>

                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-semibold text-secondary-900">Résumé quotidien</p>
                      <p class="text-sm text-gray-600">Récapitulatif de vos ventes et activités</p>
                    </div>
                    <ToggleSwitch v-model="notifications.email.dailySummary" />
                  </div>
                </div>
              </div>

              <Divider />

              <div class="flex justify-end">
                <Button
                  label="Sauvegarder les préférences"
                  icon="pi pi-save"
                  class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
                  @click="saveNotifications"
                />
              </div>
            </div>
          </template>
        </Card>
      </TabPanel>

      <!-- Onglet: Sécurité -->
      <TabPanel value="2">
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <h3 class="text-lg font-bold text-secondary-900 mb-4">Changer le mot de passe</h3>

            <div class="space-y-4">
              <div>
                <label class="block text-sm font-semibold text-secondary-900 mb-2">Mot de passe actuel</label>
                <Password
                  v-model="security.currentPassword"
                  placeholder="Votre mot de passe actuel"
                  toggle-mask
                  class="w-full"
                  :feedback="false"
                />
              </div>

              <div>
                <label class="block text-sm font-semibold text-secondary-900 mb-2">Nouveau mot de passe</label>
                <Password
                  v-model="security.newPassword"
                  placeholder="Nouveau mot de passe"
                  toggle-mask
                  class="w-full"
                />
              </div>

              <div>
                <label class="block text-sm font-semibold text-secondary-900 mb-2">Confirmer le mot de passe</label>
                <Password
                  v-model="security.confirmPassword"
                  placeholder="Confirmer le mot de passe"
                  toggle-mask
                  class="w-full"
                  :feedback="false"
                />
              </div>

              <Button
                label="Mettre à jour le mot de passe"
                icon="pi pi-lock"
                class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
                @click="changePassword"
              />
            </div>
          </template>
        </Card>
      </TabPanel>

      <!-- Onglet: Préférences -->
      <TabPanel value="3">
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="space-y-6">
              <!-- Langue -->
              <div>
                <label class="block text-sm font-semibold text-secondary-900 mb-2">Langue</label>
                <Select
                  v-model="preferences.language"
                  :options="languages"
                  option-label="name"
                  option-value="code"
                  placeholder="Sélectionnez une langue"
                  class="w-full md:w-80"
                />
              </div>

              <!-- Devise -->
              <div>
                <label class="block text-sm font-semibold text-secondary-900 mb-2">Devise</label>
                <Select
                  v-model="preferences.currency"
                  :options="currencies"
                  option-label="label"
                  option-value="code"
                  placeholder="Sélectionnez une devise"
                  class="w-full md:w-80"
                />
              </div>

              <Divider />

              <div class="flex justify-end">
                <Button
                  label="Sauvegarder les préférences"
                  icon="pi pi-save"
                  class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
                  @click="savePreferences"
                />
              </div>
            </div>
          </template>
        </Card>
      </TabPanel>

      <!-- Onglet: Intégrations -->
      <TabPanel value="4">
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <p class="text-sm text-gray-600 mb-6">
              Connectez vos comptes pour publier vos produits automatiquement sur plusieurs plateformes.
            </p>

            <div class="space-y-4">
              <div
                v-for="integration in integrations"
                :key="integration.platform"
                class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-primary-400 transition"
              >
                <div class="flex items-center gap-4">
                  <div
                    :class="[
                      'w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0',
                      getPlatformColor(integration.platform).bg
                    ]"
                  >
                    <i :class="[getPlatformIcon(integration.platform), 'text-2xl', getPlatformColor(integration.platform).text]"/>
                  </div>

                  <div class="min-w-0">
                    <p class="text-base font-bold text-secondary-900">{{ integration.name }}</p>
                    <p class="text-sm text-gray-500 truncate">
                      {{ integration.is_connected
                        ? `${integration.active_publications || 0} publications actives`
                        : 'Publiez vos produits sur ' + integration.name
                      }}
                    </p>
                    <p v-if="integration.is_connected && integration.last_sync" class="text-xs text-gray-400 mt-1 truncate">
                      Sync : {{ formatDate(integration.last_sync) }}
                    </p>
                  </div>
                </div>

                <div class="flex items-center gap-3 justify-end sm:justify-start">
                  <Badge
                    :value="integration.is_connected ? 'Connecté' : 'Déconnecté'"
                    :severity="integration.is_connected ? 'success' : 'secondary'"
                  />
                  <Button
                    v-if="!integration.is_connected"
                    label="Connecter"
                    icon="pi pi-link"
                    class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold"
                    size="small"
                    :loading="isConnecting === integration.platform"
                    @click="handleConnect(integration.platform)"
                  />
                  <Button
                    v-else
                    label="Déconnecter"
                    icon="pi pi-times"
                    class="bg-secondary-500 hover:bg-secondary-600 text-white border-0"
                    size="small"
                    :loading="isDisconnecting === integration.platform"
                    @click="handleDisconnect(integration.platform)"
                  />
                </div>
              </div>
            </div>
          </template>
        </Card>
      </TabPanel>
    </TabPanels>
    </Tabs>
  </div>
</template>

<script setup lang="ts">

definePageMeta({
  layout: 'dashboard'
})

const { showSuccess, showError, showInfo, showWarn } = useAppToast()
const authStore = useAuthStore()
const publicationsStore = usePublicationsStore()
const { getPlatformIcon, getPlatformColor } = usePlatform()

// State
const activeTab = ref('0')

// Profile data
const profile = ref({
  fullName: authStore.user?.full_name || '',
  email: authStore.user?.email || '',
  phone: '',
  company: authStore.user?.tenant_name || ''
})

// Notifications
const notifications = ref({
  email: {
    sales: true,
    publications: true,
    errors: true,
    dailySummary: false
  }
})

// Security
const security = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// Preferences
const preferences = ref({
  language: 'fr',
  currency: 'EUR'
})

const languages = [
  { name: 'Français', code: 'fr' },
  { name: 'English', code: 'en' },
  { name: 'Español', code: 'es' }
]

const currencies = [
  { label: 'Euro (EUR)', code: 'EUR' },
  { label: 'Dollar US (USD)', code: 'USD' },
  { label: 'Livre Sterling (GBP)', code: 'GBP' }
]

// Integrations
const integrations = computed(() => publicationsStore.integrations)
const isConnecting = ref<string | null>(null)
const isDisconnecting = ref<string | null>(null)

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

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

const saveNotifications = () => {
  showSuccess('Préférences sauvegardées', 'Vos préférences de notification ont été mises à jour', 3000)
}

const changePassword = () => {
  if (!security.value.currentPassword || !security.value.newPassword || !security.value.confirmPassword) {
    toast?.add({
      severity: 'warn',
      summary: 'Champs requis',
      detail: 'Veuillez remplir tous les champs',
      life: 3000
    })
    return
  }

  if (security.value.newPassword !== security.value.confirmPassword) {
    showError('Erreur', 'Les mots de passe ne correspondent pas', 3000)
    return
  }

  showSuccess('Mot de passe modifié', 'Votre mot de passe a été mis à jour avec succès', 3000)

  security.value = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
}

const savePreferences = () => {
  showSuccess('Préférences sauvegardées', 'Vos préférences ont été mises à jour', 3000)
}

const handleConnect = async (platform: string) => {
  isConnecting.value = platform

  try {
    await publicationsStore.connectIntegration(platform as any)

    toast?.add({
      severity: 'success',
      summary: 'Connexion réussie',
      detail: `Votre compte a été connecté avec succès`,
      life: 3000
    })
  } catch (error: any) {
    showError('Erreur', error.message || 'Impossible de connecter le compte', 5000)
  } finally {
    isConnecting.value = null
  }
}

const handleDisconnect = async (platform: string) => {
  isDisconnecting.value = platform

  try {
    await publicationsStore.disconnectIntegration(platform as any)

    toast?.add({
      severity: 'info',
      summary: 'Déconnexion',
      detail: `Le compte a été déconnecté`,
      life: 3000
    })
  } catch (error: any) {
    showError('Erreur', error.message || 'Impossible de déconnecter le compte', 5000)
  } finally {
    isDisconnecting.value = null
  }
}
</script>

<style scoped>
/* Make tabs scrollable on mobile */
.settings-tabs :deep(.p-tablist) {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.settings-tabs :deep(.p-tablist)::-webkit-scrollbar {
  display: none;
}

.settings-tabs :deep(.p-tablist-content) {
  display: flex;
  flex-wrap: nowrap;
}

.settings-tabs :deep(.p-tab) {
  white-space: nowrap;
  flex-shrink: 0;
}
</style>

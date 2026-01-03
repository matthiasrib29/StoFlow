<template>
  <div class="page-container">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <NuxtLink to="/dashboard/platforms/ebay" class="text-gray-500 hover:text-gray-700">
            <i class="pi pi-arrow-left"/>
          </NuxtLink>
          <h1 class="text-2xl font-bold text-secondary-900">Parametres eBay</h1>
        </div>
        <p class="text-gray-500">Configurez votre integration eBay</p>
      </div>
    </div>

    <!-- Not connected -->
    <Card v-if="!ebayStore.isConnected" class="shadow-sm modern-rounded border border-gray-100">
      <template #content>
        <div class="text-center py-12">
          <i class="pi pi-link text-4xl text-gray-300 mb-4"/>
          <h3 class="text-xl font-bold text-secondary-900 mb-2">Connectez votre compte eBay</h3>
          <p class="text-gray-500 mb-4">Accedez aux parametres apres connexion</p>
          <Button
            label="Connecter maintenant"
            icon="pi pi-link"
            class="btn-primary"
            @click="$router.push('/dashboard/platforms/ebay')"
          />
        </div>
      </template>
    </Card>

    <!-- Connected -->
    <template v-else>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Account Info -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <h3 class="text-lg font-bold text-secondary-900 mb-4">
              <i class="pi pi-user mr-2"/>
              Compte eBay
            </h3>

            <div class="space-y-4">
              <div class="flex justify-between items-center py-2 border-b border-gray-100">
                <span class="text-gray-600">Username</span>
                <span class="font-semibold">{{ ebayStore.account?.username || '-' }}</span>
              </div>
              <div class="flex justify-between items-center py-2 border-b border-gray-100">
                <span class="text-gray-600">Email</span>
                <span class="font-semibold">{{ ebayStore.account?.email || '-' }}</span>
              </div>
              <div class="flex justify-between items-center py-2 border-b border-gray-100">
                <span class="text-gray-600">Marketplace</span>
                <span class="font-semibold">{{ ebayStore.account?.marketplace || 'EBAY_FR' }}</span>
              </div>
              <div class="flex justify-between items-center py-2 border-b border-gray-100">
                <span class="text-gray-600">Niveau vendeur</span>
                <Tag :severity="getSellerLevelSeverity()">
                  {{ formatSellerLevel(ebayStore.account?.sellerLevel) }}
                </Tag>
              </div>
              <div class="flex justify-between items-center py-2">
                <span class="text-gray-600">Feedback</span>
                <span class="font-semibold">
                  {{ ebayStore.account?.feedbackScore || 0 }}
                  ({{ ebayStore.account?.feedbackPercentage || 0 }}%)
                </span>
              </div>
            </div>

            <div class="mt-6 pt-4 border-t border-gray-200">
              <Button
                label="Deconnecter le compte"
                icon="pi pi-sign-out"
                class="w-full btn-danger"
                @click="handleDisconnect"
              />
            </div>
          </template>
        </Card>

        <!-- Sync Settings -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <h3 class="text-lg font-bold text-secondary-900 mb-4">
              <i class="pi pi-sync mr-2"/>
              Synchronisation
            </h3>

            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-semibold text-secondary-900">Sync automatique</p>
                  <p class="text-sm text-gray-500">Synchroniser automatiquement vos produits</p>
                </div>
                <ToggleSwitch v-model="syncSettings.autoSync" />
              </div>

              <div v-if="syncSettings.autoSync">
                <label class="block text-sm font-semibold text-secondary-900 mb-2">Frequence</label>
                <Select
                  v-model="syncSettings.syncInterval"
                  :options="syncIntervals"
                  optionLabel="label"
                  optionValue="value"
                  class="w-full"
                />
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <p class="font-semibold text-secondary-900">Sync stocks</p>
                  <p class="text-sm text-gray-500">Synchroniser les quantites</p>
                </div>
                <ToggleSwitch v-model="syncSettings.syncStock" />
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <p class="font-semibold text-secondary-900">Sync prix</p>
                  <p class="text-sm text-gray-500">Synchroniser les prix</p>
                </div>
                <ToggleSwitch v-model="syncSettings.syncPrices" />
              </div>
            </div>

            <div class="mt-6 pt-4 border-t border-gray-200">
              <Button
                label="Sauvegarder"
                icon="pi pi-check"
                class="w-full btn-primary"
                :loading="saving"
                @click="saveSettings"
              />
            </div>
          </template>
        </Card>

        <!-- Shipping Policies -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-bold text-secondary-900">
                <i class="pi pi-truck mr-2"/>
                Politiques d'expedition
              </h3>
              <Button
                icon="pi pi-refresh"
                class="p-button-sm p-button-text"
                :loading="loadingPolicies"
                @click="loadPolicies"
              />
            </div>

            <div v-if="ebayStore.shippingPolicies.length === 0" class="text-center py-6">
              <i class="pi pi-inbox text-gray-300 text-3xl mb-2"/>
              <p class="text-gray-500">Aucune politique configuree</p>
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="policy in ebayStore.shippingPolicies"
                :key="policy.id"
                class="p-3 bg-gray-50 rounded-lg"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <p class="font-semibold text-secondary-900">{{ policy.name }}</p>
                    <p class="text-sm text-gray-500">{{ getShippingTypeLabel(policy) }}</p>
                  </div>
                  <Tag v-if="policy.isDefault" severity="success" value="Par defaut" />
                </div>
              </div>
            </div>

            <div class="mt-4">
              <Button
                label="Gerer sur eBay"
                icon="pi pi-external-link"
                class="w-full btn-secondary"
                @click="openEbaySettings('shipping')"
              />
            </div>
          </template>
        </Card>

        <!-- Return Policies -->
        <Card class="shadow-sm modern-rounded border border-gray-100">
          <template #content>
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-bold text-secondary-900">
                <i class="pi pi-replay mr-2"/>
                Politiques de retour
              </h3>
            </div>

            <div v-if="ebayStore.returnPolicies.length === 0" class="text-center py-6">
              <i class="pi pi-inbox text-gray-300 text-3xl mb-2"/>
              <p class="text-gray-500">Aucune politique configuree</p>
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="policy in ebayStore.returnPolicies"
                :key="policy.id"
                class="p-3 bg-gray-50 rounded-lg"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <p class="font-semibold text-secondary-900">{{ policy.name }}</p>
                    <p class="text-sm text-gray-500">
                      {{ policy.returnsAccepted ? `Retours sous ${policy.returnPeriod || 30} jours` : 'Pas de retours' }}
                    </p>
                  </div>
                  <Tag v-if="policy.isDefault" severity="success" value="Par defaut" />
                </div>
              </div>
            </div>

            <div class="mt-4">
              <Button
                label="Gerer sur eBay"
                icon="pi pi-external-link"
                class="w-full btn-secondary"
                @click="openEbaySettings('return')"
              />
            </div>
          </template>
        </Card>
      </div>
    </template>

    <!-- Confirm Dialog -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'

definePageMeta({
  layout: 'dashboard'
})

const ebayStore = useEbayStore()
const confirm = import.meta.client ? useConfirm() : null
const { showSuccess, showError } = useAppToast()

// State
const saving = ref(false)
const loadingPolicies = ref(false)

const syncSettings = reactive({
  autoSync: true,
  syncInterval: 30,
  syncStock: true,
  syncPrices: true
})

const syncIntervals = [
  { label: 'Toutes les 15 minutes', value: 15 },
  { label: 'Toutes les 30 minutes', value: 30 },
  { label: 'Toutes les heures', value: 60 },
  { label: 'Toutes les 2 heures', value: 120 }
]

// Methods
const loadPolicies = async () => {
  loadingPolicies.value = true
  try {
    await ebayStore.fetchPolicies()
  } catch (e: any) {
    showError('Erreur', 'Impossible de charger les politiques', 5000)
  } finally {
    loadingPolicies.value = false
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    await ebayStore.saveSyncSettings(syncSettings)
    showSuccess('Sauvegarde', 'Parametres enregistres', 3000)
  } catch (e: any) {
    showError('Erreur', e.message || 'Impossible de sauvegarder', 5000)
  } finally {
    saving.value = false
  }
}

const handleDisconnect = () => {
  confirm?.require({
    message: 'Voulez-vous vraiment deconnecter votre compte eBay ?',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Oui, deconnecter',
    rejectLabel: 'Annuler',
    accept: async () => {
      try {
        await ebayStore.disconnect()
        showSuccess('Deconnecte', 'Compte eBay deconnecte', 3000)
        navigateTo('/dashboard/platforms/ebay')
      } catch (e: any) {
        showError('Erreur', e.message || 'Impossible de deconnecter', 5000)
      }
    }
  })
}

const openEbaySettings = (type: string) => {
  const urls: Record<string, string> = {
    shipping: 'https://www.ebay.fr/sh/settings/shipping-preferences',
    return: 'https://www.ebay.fr/sh/settings/return-preferences'
  }
  window.open(urls[type] || 'https://www.ebay.fr/sh/ovw', '_blank')
}

const getSellerLevelSeverity = () => {
  const level = ebayStore.account?.sellerLevel
  if (level === 'top_rated') return 'success'
  if (level === 'above_standard') return 'info'
  if (level === 'standard') return 'warning'
  return 'secondary'
}

const formatSellerLevel = (level?: string) => {
  const labels: Record<string, string> = {
    top_rated: 'Top Rated',
    above_standard: 'Above Standard',
    standard: 'Standard',
    below_standard: 'Below Standard'
  }
  return labels[level || ''] || level || 'Standard'
}

const getShippingTypeLabel = (policy: any): string => {
  if (policy.shippingOptions?.length > 0) {
    const option = policy.shippingOptions[0]
    if (option.costType === 'FREE') return 'Livraison gratuite'
    if (option.costType === 'FLAT_RATE') return 'Forfait'
    if (option.costType === 'CALCULATED') return 'Calcule'
  }
  return policy.type || 'Standard'
}

// Init
onMounted(async () => {
  try {
    await ebayStore.checkConnectionStatus()
    if (ebayStore.isConnected) {
      Object.assign(syncSettings, ebayStore.syncSettings)
      await loadPolicies()
    }
  } catch (e) {
    console.error('Error on mount:', e)
  }
})
</script>

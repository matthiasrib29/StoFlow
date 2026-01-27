<template>
  <PlatformSettingsPage
    platform="ebay"
    :is-connected="ebayStore.isConnected ?? false"
    subtitle="Configurez votre integration eBay"
    back-to="/dashboard/platforms/ebay/products"
    :columns="2"
  >
    <!-- Settings sections -->
    <template #content>
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

        <!-- Business Policies (Tabbed) -->
        <Card class="shadow-sm modern-rounded border border-gray-100 lg:col-span-2">
          <template #content>
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-bold text-secondary-900">
                <i class="pi pi-briefcase mr-2"/>
                Business Policies
              </h3>
              <div class="flex items-center gap-2">
                <Select
                  v-model="selectedMarketplace"
                  :options="ebayMarketplaces"
                  optionLabel="label"
                  optionValue="value"
                  class="w-48"
                  @change="onMarketplaceChange"
                />
                <Button
                  icon="pi pi-refresh"
                  class="p-button-sm p-button-text"
                  :loading="loadingPolicies"
                  @click="loadPolicies"
                />
              </div>
            </div>

            <Tabs value="shipping">
              <TabList>
                <Tab value="shipping">
                  <i class="pi pi-truck mr-1"/>
                  Expedition ({{ ebayStore.shippingPolicies.length }})
                </Tab>
                <Tab value="return">
                  <i class="pi pi-replay mr-1"/>
                  Retour ({{ ebayStore.returnPolicies.length }})
                </Tab>
                <Tab value="payment">
                  <i class="pi pi-credit-card mr-1"/>
                  Paiement ({{ ebayStore.paymentPolicies.length }})
                </Tab>
              </TabList>

              <TabPanels>
                <!-- Shipping Policies -->
                <TabPanel value="shipping">
                  <div v-if="ebayStore.shippingPolicies.length === 0" class="text-center py-6">
                    <i class="pi pi-inbox text-gray-300 text-3xl mb-2"/>
                    <p class="text-gray-500">Aucune politique d'expedition</p>
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
                </TabPanel>

                <!-- Return Policies -->
                <TabPanel value="return">
                  <div v-if="ebayStore.returnPolicies.length === 0" class="text-center py-6">
                    <i class="pi pi-inbox text-gray-300 text-3xl mb-2"/>
                    <p class="text-gray-500">Aucune politique de retour</p>
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
                </TabPanel>

                <!-- Payment Policies -->
                <TabPanel value="payment">
                  <div v-if="ebayStore.paymentPolicies.length === 0" class="text-center py-6">
                    <i class="pi pi-inbox text-gray-300 text-3xl mb-2"/>
                    <p class="text-gray-500">Aucune politique de paiement</p>
                  </div>
                  <div v-else class="space-y-3">
                    <div
                      v-for="policy in ebayStore.paymentPolicies"
                      :key="policy.id"
                      class="p-3 bg-gray-50 rounded-lg"
                    >
                      <div class="flex items-center justify-between">
                        <div>
                          <p class="font-semibold text-secondary-900">{{ policy.name }}</p>
                          <p class="text-sm text-gray-500">
                            {{ formatPaymentMethods(policy.paymentMethods) }}
                            {{ policy.immediatePay ? ' - Paiement immediat' : '' }}
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
                      @click="openEbaySettings('payment')"
                    />
                  </div>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </template>
        </Card>
    </template>

    <!-- Confirm Dialog (outside PlatformSettingsPage content) -->
  </PlatformSettingsPage>

  <ClientOnly>
    <ConfirmDialog />
  </ClientOnly>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { ebayLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

const ebayStore = useEbayStore()
const confirm = import.meta.client ? useConfirm() : null
const { showSuccess, showError } = useAppToast()

// State
const saving = ref(false)
const loadingPolicies = ref(false)
const selectedMarketplace = ref('EBAY_FR')

const ebayMarketplaces = [
  { label: 'France', value: 'EBAY_FR' },
  { label: 'Allemagne', value: 'EBAY_DE' },
  { label: 'Royaume-Uni', value: 'EBAY_GB' },
  { label: 'Italie', value: 'EBAY_IT' },
  { label: 'Espagne', value: 'EBAY_ES' },
  { label: 'Pays-Bas', value: 'EBAY_NL' },
  { label: 'Belgique', value: 'EBAY_BE' },
  { label: 'Autriche', value: 'EBAY_AT' },
]

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
  ebayLogger.info('Loading eBay policies', { marketplace: selectedMarketplace.value })
  loadingPolicies.value = true
  try {
    await ebayStore.fetchPolicies(selectedMarketplace.value)
    ebayLogger.info('eBay policies loaded successfully', {
      marketplace: selectedMarketplace.value,
      shippingPoliciesCount: ebayStore.shippingPolicies.length,
      returnPoliciesCount: ebayStore.returnPolicies.length,
      paymentPoliciesCount: ebayStore.paymentPolicies.length
    })
  } catch (e: any) {
    ebayLogger.error('Failed to load eBay policies', {
      error: e.message,
      stack: e.stack
    })
    showError('Erreur', 'Impossible de charger les politiques', 5000)
  } finally {
    loadingPolicies.value = false
  }
}

const onMarketplaceChange = () => {
  loadPolicies()
}

const saveSettings = async () => {
  ebayLogger.info('Saving eBay sync settings', {
    settings: syncSettings
  })
  saving.value = true
  try {
    await ebayStore.saveSyncSettings(syncSettings)
    ebayLogger.info('eBay sync settings saved successfully')
    showSuccess('Sauvegarde', 'Parametres enregistres', 3000)
  } catch (e: any) {
    ebayLogger.error('Failed to save eBay sync settings', {
      error: e.message,
      stack: e.stack
    })
    showError('Erreur', e.message || 'Impossible de sauvegarder', 5000)
  } finally {
    saving.value = false
  }
}

const handleDisconnect = () => {
  ebayLogger.info('User requested eBay account disconnect')
  confirm?.require({
    message: 'Voulez-vous vraiment deconnecter votre compte eBay ?',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Oui, deconnecter',
    rejectLabel: 'Annuler',
    accept: async () => {
      ebayLogger.info('User confirmed eBay account disconnect')
      try {
        await ebayStore.disconnect()
        ebayLogger.info('eBay account disconnected successfully')
        showSuccess('Deconnecte', 'Compte eBay deconnecte', 3000)
        navigateTo('/dashboard/platforms/ebay')
      } catch (e: any) {
        ebayLogger.error('Failed to disconnect eBay account', {
          error: e.message,
          stack: e.stack
        })
        showError('Erreur', e.message || 'Impossible de deconnecter', 5000)
      }
    },
    reject: () => {
      ebayLogger.debug('User cancelled eBay account disconnect')
    }
  })
}

const openEbaySettings = (type: string) => {
  if (!import.meta.client) return
  const urls: Record<string, string> = {
    shipping: 'https://www.ebay.fr/sh/settings/shipping-preferences',
    return: 'https://www.ebay.fr/sh/settings/return-preferences',
    payment: 'https://www.ebay.fr/sh/settings/payment-preferences'
  }
  window.open(urls[type] || 'https://www.ebay.fr/sh/ovw', '_blank')
}

const formatPaymentMethods = (methods: string[]): string => {
  const labels: Record<string, string> = {
    paypal: 'PayPal',
    credit_card: 'Carte bancaire',
    bank_transfer: 'Virement'
  }
  return methods.map(m => labels[m] || m).join(', ')
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
  ebayLogger.info('eBay Settings page mounted', {
    route: '/dashboard/platforms/ebay/settings'
  })

  try {
    await ebayStore.checkConnectionStatus()
    ebayLogger.debug('Connection status checked', {
      isConnected: ebayStore.isConnected
    })

    if (ebayStore.isConnected) {
      Object.assign(syncSettings, ebayStore.syncSettings)
      ebayLogger.debug('Sync settings loaded', { syncSettings })
      await loadPolicies()
    } else {
      ebayLogger.warn('User not connected to eBay', {
        redirectRequired: true
      })
    }
  } catch (e) {
    ebayLogger.error('Failed to initialize eBay settings', { error: e })
  }
})
</script>

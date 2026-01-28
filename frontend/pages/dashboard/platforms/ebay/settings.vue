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
                  <div class="mb-3">
                    <Button
                      label="Creer une politique d'expedition"
                      icon="pi pi-plus"
                      class="p-button-sm p-button-outlined"
                      :loading="creatingPolicy"
                      @click="openCreateDialog('shipping')"
                    />
                  </div>
                  <div v-if="ebayStore.shippingPolicies.length === 0" class="text-center py-6">
                    <i class="pi pi-inbox text-gray-300 text-3xl mb-2"/>
                    <p class="text-gray-500">Aucune politique d'expedition</p>
                  </div>
                  <div v-else class="space-y-3">
                    <div
                      v-for="policy in ebayStore.shippingPolicies"
                      :key="policy.fulfillmentPolicyId || policy.id"
                      class="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                      @click="openDetailDialog(policy, 'shipping')"
                    >
                      <div class="flex items-center justify-between">
                        <div class="flex-1 min-w-0">
                          <p class="font-semibold text-secondary-900">{{ policy.name }}</p>
                          <p class="text-sm text-gray-500">{{ getShippingTypeLabel(policy) }}</p>
                        </div>
                        <div class="flex items-center gap-2 ml-2">
                          <Tag v-if="policy.isDefault" severity="success" value="Par defaut" />
                          <Button
                            icon="pi pi-trash"
                            class="p-button-sm p-button-text p-button-danger"
                            :loading="ebayStore.isLoading"
                            @click.stop="confirmDeletePolicy('shipping', policy.fulfillmentPolicyId || policy.id, policy.name)"
                          />
                        </div>
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
                  <div class="mb-3">
                    <Button
                      label="Creer une politique de retour"
                      icon="pi pi-plus"
                      class="p-button-sm p-button-outlined"
                      :loading="creatingPolicy"
                      @click="openCreateDialog('return')"
                    />
                  </div>
                  <div v-if="ebayStore.returnPolicies.length === 0" class="text-center py-6">
                    <i class="pi pi-inbox text-gray-300 text-3xl mb-2"/>
                    <p class="text-gray-500">Aucune politique de retour</p>
                  </div>
                  <div v-else class="space-y-3">
                    <div
                      v-for="policy in ebayStore.returnPolicies"
                      :key="policy.returnPolicyId || policy.id"
                      class="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                      @click="openDetailDialog(policy, 'return')"
                    >
                      <div class="flex items-center justify-between">
                        <div class="flex-1 min-w-0">
                          <p class="font-semibold text-secondary-900">{{ policy.name }}</p>
                          <p class="text-sm text-gray-500">
                            {{ policy.returnsAccepted ? `Retours sous ${policy.returnPeriod?.value || policy.returnPeriod || 30} jours` : 'Pas de retours' }}
                          </p>
                        </div>
                        <div class="flex items-center gap-2 ml-2">
                          <Tag v-if="policy.isDefault" severity="success" value="Par defaut" />
                          <Button
                            icon="pi pi-trash"
                            class="p-button-sm p-button-text p-button-danger"
                            :loading="ebayStore.isLoading"
                            @click.stop="confirmDeletePolicy('return', policy.returnPolicyId || policy.id, policy.name)"
                          />
                        </div>
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
                  <div class="mb-3">
                    <Button
                      label="Creer une politique de paiement"
                      icon="pi pi-plus"
                      class="p-button-sm p-button-outlined"
                      :loading="creatingPolicy"
                      @click="openCreateDialog('payment')"
                    />
                  </div>
                  <div v-if="ebayStore.paymentPolicies.length === 0" class="text-center py-6">
                    <i class="pi pi-inbox text-gray-300 text-3xl mb-2"/>
                    <p class="text-gray-500">Aucune politique de paiement</p>
                  </div>
                  <div v-else class="space-y-3">
                    <div
                      v-for="policy in ebayStore.paymentPolicies"
                      :key="policy.paymentPolicyId || policy.id"
                      class="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                      @click="openDetailDialog(policy, 'payment')"
                    >
                      <div class="flex items-center justify-between">
                        <div class="flex-1 min-w-0">
                          <p class="font-semibold text-secondary-900">{{ policy.name }}</p>
                          <p class="text-sm text-gray-500">
                            {{ formatPaymentMethods(policy.paymentMethods) }}
                            {{ policy.immediatePay ? ' - Paiement immediat' : '' }}
                          </p>
                        </div>
                        <div class="flex items-center gap-2 ml-2">
                          <Tag v-if="policy.isDefault" severity="success" value="Par defaut" />
                          <Button
                            icon="pi pi-trash"
                            class="p-button-sm p-button-text p-button-danger"
                            :loading="ebayStore.isLoading"
                            @click.stop="confirmDeletePolicy('payment', policy.paymentPolicyId || policy.id, policy.name)"
                          />
                        </div>
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

    <!-- Policy Detail Dialog -->
    <Dialog
      v-model:visible="detailDialog.visible"
      :header="detailDialog.policy?.name || 'Details'"
      modal
      :style="{ width: '550px' }"
    >
      <div v-if="detailDialog.policy" class="space-y-3">
        <div v-for="(value, key) in formatPolicyDetails(detailDialog.policy, detailDialog.type)" :key="key" class="flex justify-between items-start py-2 border-b border-gray-100 last:border-0">
          <span class="text-gray-600 text-sm font-medium">{{ key }}</span>
          <span class="text-secondary-900 text-sm text-right max-w-[60%]">{{ value }}</span>
        </div>
      </div>
      <template #footer>
        <Button label="Fermer" class="p-button-text" @click="detailDialog.visible = false" />
        <Button
          label="Modifier"
          icon="pi pi-pencil"
          class="p-button-outlined"
          @click="openEditDialog"
        />
        <Button
          label="Appliquer a toutes les annonces"
          icon="pi pi-check-circle"
          :loading="applyingPolicy"
          @click="handleApplyPolicy"
        />
      </template>
    </Dialog>

    <!-- Create Return Policy Dialog -->
    <Dialog
      v-model:visible="createReturnDialog.visible"
      header="Creer une politique de retour"
      modal
      :style="{ width: '400px' }"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Duree de retour</label>
          <Select
            v-model="createReturnDialog.returnPeriod"
            :options="returnPeriodOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
        <p class="text-sm text-gray-500">
          Remboursement : avoir ou remboursement integral. Frais de retour a la charge de l'acheteur.
        </p>
      </div>
      <template #footer>
        <Button label="Annuler" class="p-button-text" @click="createReturnDialog.visible = false" />
        <Button
          label="Creer"
          icon="pi pi-check"
          :loading="creatingPolicy"
          @click="confirmCreateReturnPolicy"
        />
      </template>
    </Dialog>

    <!-- Edit Policy Dialog -->
    <Dialog
      v-model:visible="editDialog.visible"
      header="Modifier la politique"
      modal
      :style="{ width: '450px' }"
    >
      <div class="space-y-4">
        <!-- Name (common to all types) -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Nom</label>
          <InputText v-model="editDialog.name" class="w-full" />
        </div>

        <!-- Payment-specific fields -->
        <div v-if="editDialog.type === 'payment'" class="flex items-center justify-between">
          <div>
            <p class="font-semibold text-secondary-900">Paiement immediat</p>
            <p class="text-sm text-gray-500">Exiger le paiement immediat</p>
          </div>
          <ToggleSwitch v-model="editDialog.immediatePay" />
        </div>

        <!-- Return-specific fields -->
        <template v-if="editDialog.type === 'return'">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Duree de retour</label>
            <Select
              v-model="editDialog.returnPeriod"
              :options="returnPeriodOptions"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Frais de retour payes par</label>
            <Select
              v-model="editDialog.returnCostPayer"
              :options="returnCostPayerOptions"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
        </template>

        <!-- Fulfillment-specific fields -->
        <div v-if="editDialog.type === 'shipping'">
          <label class="block text-sm font-medium text-gray-700 mb-2">Delai de traitement (jours)</label>
          <InputNumber v-model="editDialog.handlingTime" :min="0" :max="30" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Annuler" class="p-button-text" @click="editDialog.visible = false" />
        <Button
          label="Sauvegarder"
          icon="pi pi-check"
          :loading="editingPolicy"
          @click="confirmEditPolicy"
        />
      </template>
    </Dialog>
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

// Detail dialog state
const detailDialog = reactive({
  visible: false,
  policy: null as any,
  type: '' as 'shipping' | 'return' | 'payment'
})

// Create return policy dialog
const createReturnDialog = reactive({
  visible: false,
  returnPeriod: 30,
})

const returnPeriodOptions = [
  { label: '14 jours', value: 14 },
  { label: '30 jours', value: 30 },
  { label: '60 jours', value: 60 },
]

const returnCostPayerOptions = [
  { label: 'Acheteur', value: 'BUYER' },
  { label: 'Vendeur', value: 'SELLER' },
]

// Edit policy dialog
const editDialog = reactive({
  visible: false,
  type: '' as 'payment' | 'return' | 'shipping',
  policyId: '',
  name: '',
  immediatePay: true,
  returnPeriod: 30,
  returnCostPayer: 'BUYER',
  handlingTime: 2,
  // Preserve existing shipping services for fulfillment update
  shippingServices: [] as Array<{
    shipping_carrier_code: string
    shipping_service_code: string
    shipping_cost: number
    currency: string
    free_shipping: boolean
    additional_cost?: number
  }>,
})
const editingPolicy = ref(false)

const openDetailDialog = (policy: any, type: 'shipping' | 'return' | 'payment') => {
  detailDialog.policy = policy
  detailDialog.type = type
  detailDialog.visible = true
}

const formatPolicyDetails = (policy: any, type: string): Record<string, string> => {
  const details: Record<string, string> = {}

  // Common fields
  details['ID'] = policy.fulfillmentPolicyId || policy.returnPolicyId || policy.paymentPolicyId || policy.id || '-'
  details['Nom'] = policy.name || '-'
  if (policy.description) details['Description'] = policy.description
  details['Marketplace'] = policy.marketplaceId || '-'

  if (type === 'shipping') {
    const handlingTime = policy.handlingTime
    if (handlingTime) {
      details['Delai de traitement'] = `${handlingTime.value} ${handlingTime.unit === 'DAY' ? 'jour(s)' : handlingTime.unit}`
    }
    if (policy.shippingOptions?.length > 0) {
      for (let i = 0; i < policy.shippingOptions.length; i++) {
        const opt = policy.shippingOptions[i]
        details[`Option ${i + 1} - Type`] = opt.optionType || opt.costType || '-'
        if (opt.shippingServices?.length > 0) {
          const svc = opt.shippingServices[0]
          details[`Option ${i + 1} - Transporteur`] = svc.shippingCarrierCode || '-'
          details[`Option ${i + 1} - Service`] = svc.shippingServiceCode || '-'
          if (svc.shippingCost) {
            details[`Option ${i + 1} - Cout`] = `${svc.shippingCost.value} ${svc.shippingCost.currency}`
          }
          details[`Option ${i + 1} - Gratuit`] = svc.freeShipping ? 'Oui' : 'Non'
        }
      }
    }
  }

  if (type === 'return') {
    details['Retours acceptes'] = policy.returnsAccepted ? 'Oui' : 'Non'
    if (policy.returnPeriod) {
      const period = typeof policy.returnPeriod === 'object'
        ? `${policy.returnPeriod.value} ${policy.returnPeriod.unit === 'DAY' ? 'jour(s)' : policy.returnPeriod.unit}`
        : `${policy.returnPeriod} jour(s)`
      details['Periode de retour'] = period
    }
    details['Methode de remboursement'] = policy.refundMethod || '-'
    details['Frais de retour payes par'] = policy.returnShippingCostPayer || '-'
  }

  if (type === 'payment') {
    details['Paiement immediat'] = policy.immediatePay ? 'Oui' : 'Non'
    if (policy.paymentMethods?.length > 0) {
      details['Methodes de paiement'] = policy.paymentMethods
        .map((m: any) => typeof m === 'string' ? m : m.paymentMethodType || m)
        .join(', ')
    }
  }

  // Category types
  if (policy.categoryTypes?.length > 0) {
    details['Categories'] = policy.categoryTypes.map((c: any) => c.name || c).join(', ')
  }

  return details
}

// Apply policy to offers
const applyingPolicy = ref(false)

const getPolicyId = (policy: any, type: string): string => {
  if (type === 'shipping') return policy.fulfillmentPolicyId || policy.id
  if (type === 'return') return policy.returnPolicyId || policy.id
  if (type === 'payment') return policy.paymentPolicyId || policy.id
  return policy.id
}

const policyTypeToEbayType: Record<string, 'payment' | 'fulfillment' | 'return'> = {
  shipping: 'fulfillment',
  return: 'return',
  payment: 'payment'
}

const handleApplyPolicy = async () => {
  const policy = detailDialog.policy
  const type = detailDialog.type
  if (!policy || !type) return

  const policyId = getPolicyId(policy, type)
  const ebayType = policyTypeToEbayType[type]

  applyingPolicy.value = true
  try {
    const result = await ebayStore.applyPolicyToOffers(ebayType, policyId, selectedMarketplace.value)
    detailDialog.visible = false

    if (result.status === 'no_offers') {
      showSuccess('Aucune annonce', 'Aucune annonce active trouvee pour cette marketplace')
    } else {
      showSuccess(
        'Tache lancee',
        `Application de la politique en cours sur ${result.total_offers} annonce(s). Suivez la progression dans les taches eBay.`,
      )
    }
  } catch (e: any) {
    ebayLogger.error('Failed to apply policy to offers', { error: e.message })
    showError('Erreur', e.message || 'Impossible d\'appliquer la politique')
  } finally {
    applyingPolicy.value = false
  }
}

// Edit policy helpers
const openEditDialog = () => {
  const policy = detailDialog.policy
  const type = detailDialog.type
  if (!policy || !type) return

  editDialog.type = type
  editDialog.policyId = getPolicyId(policy, type)
  editDialog.name = policy.name || ''

  if (type === 'payment') {
    editDialog.immediatePay = policy.immediatePay ?? true
  } else if (type === 'return') {
    const period = typeof policy.returnPeriod === 'object'
      ? policy.returnPeriod.value
      : policy.returnPeriod
    editDialog.returnPeriod = period ?? 30
    editDialog.returnCostPayer = policy.returnShippingCostPayer || 'BUYER'
  } else if (type === 'shipping') {
    const ht = policy.handlingTime
    editDialog.handlingTime = ht?.value ?? 2

    // Extract existing shipping services to preserve them on update
    editDialog.shippingServices = []
    if (policy.shippingOptions?.length > 0) {
      for (const opt of policy.shippingOptions) {
        if (opt.shippingServices?.length > 0) {
          const svc = opt.shippingServices[0]
          editDialog.shippingServices.push({
            shipping_carrier_code: svc.shippingCarrierCode || 'Colissimo',
            shipping_service_code: svc.shippingServiceCode || 'FR_ColiPoste',
            shipping_cost: parseFloat(svc.shippingCost?.value || '5.99'),
            currency: svc.shippingCost?.currency || 'EUR',
            free_shipping: svc.freeShipping ?? false,
            ...(svc.additionalCost ? { additional_cost: parseFloat(svc.additionalCost.value) } : {}),
          })
        }
      }
    }
    // Fallback if no shipping services found
    if (editDialog.shippingServices.length === 0) {
      editDialog.shippingServices = [{
        shipping_carrier_code: 'Colissimo',
        shipping_service_code: 'FR_ColiPoste',
        shipping_cost: 5.99,
        currency: 'EUR',
        free_shipping: false,
      }]
    }
  }

  detailDialog.visible = false
  editDialog.visible = true
}

const confirmEditPolicy = async () => {
  const type = editDialog.type
  const policyId = editDialog.policyId
  const marketplace = selectedMarketplace.value

  editingPolicy.value = true
  try {
    let data: any

    switch (type) {
      case 'payment':
        data = {
          name: editDialog.name,
          marketplace_id: marketplace,
          immediate_pay: editDialog.immediatePay,
        }
        break
      case 'return':
        data = {
          name: editDialog.name,
          marketplace_id: marketplace,
          returns_accepted: true,
          return_period_value: editDialog.returnPeriod,
          refund_method: 'MONEY_BACK',
          return_shipping_cost_payer: editDialog.returnCostPayer,
        }
        break
      case 'shipping':
        data = {
          name: editDialog.name,
          marketplace_id: marketplace,
          handling_time_value: editDialog.handlingTime,
          shipping_services: editDialog.shippingServices,
        }
        break
    }

    await ebayStore.updatePolicy(type, policyId, data, marketplace)
    editDialog.visible = false
    showSuccess('Politique modifiee', `La politique "${editDialog.name}" a ete modifiee avec succes`)
  } catch (e: any) {
    ebayLogger.error('Failed to update policy', { error: e.message, type, policyId })
    showError('Erreur', e.message || 'Impossible de modifier la politique')
  } finally {
    editingPolicy.value = false
  }
}

// Create policy helpers
const creatingPolicy = ref(false)

const getMarketplaceShortLabel = (marketplaceId: string): string => {
  return marketplaceId.replace('EBAY_', '')
}

const policyTypeLabels: Record<string, string> = {
  shipping: "Expedition",
  return: "Retour",
  payment: "Paiement"
}

const openCreateDialog = async (type: 'shipping' | 'return' | 'payment') => {
  const shortLabel = getMarketplaceShortLabel(selectedMarketplace.value)
  const name = `${policyTypeLabels[type]} Policy ${shortLabel}`
  const marketplace = selectedMarketplace.value

  creatingPolicy.value = true
  try {
    switch (type) {
      case 'payment':
        await ebayStore.createPaymentPolicy({
          name,
          marketplace_id: marketplace,
          immediate_pay: true
        })
        break
      case 'shipping':
        await ebayStore.createFulfillmentPolicy({
          name,
          marketplace_id: marketplace,
          handling_time_value: 2,
          shipping_services: [{
            shipping_carrier_code: 'Colissimo',
            shipping_service_code: 'FR_ColiPoste',
            shipping_cost: 5.99,
            currency: 'EUR',
            free_shipping: false
          }]
        })
        break
      case 'return':
        creatingPolicy.value = false
        createReturnDialog.returnPeriod = 30
        createReturnDialog.visible = true
        return // Don't show success toast here, dialog handles it
    }

    showSuccess('Politique creee', `La politique "${name}" a ete creee avec succes`)
  } catch (e: any) {
    ebayLogger.error('Failed to create policy', { error: e.message, type })
    showError('Erreur', e.message || 'Impossible de creer la politique')
  } finally {
    creatingPolicy.value = false
  }
}

const confirmCreateReturnPolicy = async () => {
  const shortLabel = getMarketplaceShortLabel(selectedMarketplace.value)
  const name = `Retour Policy ${shortLabel}`

  creatingPolicy.value = true
  try {
    await ebayStore.createReturnPolicy({
      name,
      marketplace_id: selectedMarketplace.value,
      returns_accepted: true,
      return_period_value: createReturnDialog.returnPeriod,
      refund_method: 'MONEY_BACK',
      return_shipping_cost_payer: 'BUYER'
    })
    createReturnDialog.visible = false
    showSuccess('Politique creee', `La politique "${name}" a ete creee avec succes`)
  } catch (e: any) {
    ebayLogger.error('Failed to create return policy', { error: e.message })
    showError('Erreur', e.message || 'Impossible de creer la politique')
  } finally {
    creatingPolicy.value = false
  }
}

const confirmDeletePolicy = (type: 'shipping' | 'return' | 'payment', policyId: string, policyName: string) => {
  confirm?.require({
    message: `Voulez-vous vraiment supprimer la politique "${policyName}" ? Si elle est associee a des annonces actives, la suppression echouera.`,
    header: 'Confirmer la suppression',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Oui, supprimer',
    rejectLabel: 'Annuler',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await ebayStore.deletePolicy(type, policyId, selectedMarketplace.value)
        showSuccess('Politique supprimee', `La politique "${policyName}" a ete supprimee`)
      } catch (e: any) {
        ebayLogger.error('Failed to delete policy', { error: e.message, type, policyId })
        showError('Erreur', e.message || 'Impossible de supprimer la politique. Elle est peut-etre associee a des annonces actives.')
      }
    }
  })
}

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

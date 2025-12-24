<template>
  <div class="page-container">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-secondary-900 mb-2">Abonnement</h1>
      <p class="text-gray-600">Gérez votre abonnement et vos crédits IA</p>
    </div>

    <!-- Client-only content to prevent hydration mismatch -->
    <ClientOnly>
      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <ProgressSpinner />
      </div>

      <!-- Error -->
      <Message v-else-if="error" severity="error" :closable="false" class="mb-6">
        {{ error }}
      </Message>

      <!-- Content -->
      <div v-else class="space-y-6">
        <!-- Current Subscription Card -->
        <Card class="shadow-md modern-rounded">
          <template #title>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <i class="pi pi-star-fill text-primary-400 text-2xl"/>
                <span class="text-2xl font-bold text-secondary-900">Votre abonnement</span>
              </div>
              <Tag :value="currentTier.toUpperCase()" :severity="getTierSeverity(currentTier)" class="text-sm font-bold px-4 py-2" />
            </div>
          </template>
          <template #content>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <!-- Products Quota -->
              <div class="p-4 bg-secondary-50 rounded-lg border-l-4 border-primary-400">
                <div class="flex items-center gap-3 mb-2">
                  <i class="pi pi-box text-primary-400 text-xl"/>
                  <span class="text-sm text-gray-600 font-medium">Produits</span>
                </div>
                <p class="text-2xl font-bold text-secondary-900">{{ currentProducts }} / {{ maxProducts }}</p>
                <ProgressBar
                  :value="productProgress"
                  :show-value="false"
                  class="mt-2 h-2"
                  :pt="{
                    value: { class: 'bg-primary-400' }
                  }"
                />
              </div>

              <!-- Platforms Quota -->
              <div class="p-4 bg-secondary-50 rounded-lg border-l-4 border-primary-400">
                <div class="flex items-center gap-3 mb-2">
                  <i class="pi pi-globe text-primary-400 text-xl"/>
                  <span class="text-sm text-gray-600 font-medium">Plateformes</span>
                </div>
                <p class="text-2xl font-bold text-secondary-900">{{ currentPlatforms }} / {{ maxPlatforms }}</p>
                <ProgressBar
                  :value="platformProgress"
                  :show-value="false"
                  class="mt-2 h-2"
                  :pt="{
                    value: { class: 'bg-primary-400' }
                  }"
                />
              </div>

              <!-- AI Credits -->
              <div class="p-4 bg-secondary-50 rounded-lg border-l-4 border-primary-400">
                <div class="flex items-center gap-3 mb-2">
                  <i class="pi pi-sparkles text-primary-400 text-xl"/>
                  <span class="text-sm text-gray-600 font-medium">Crédits IA</span>
                </div>
                <p class="text-2xl font-bold text-secondary-900">{{ aiCreditsRemaining }}</p>
                <p class="text-xs text-gray-500 mt-1">{{ aiCreditsMonthly }} / mois</p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Upgrade Plans Section -->
        <Card class="shadow-md modern-rounded">
          <template #title>
            <div class="flex items-center gap-3">
              <i class="pi pi-arrow-up text-primary-400 text-xl"/>
              <span class="text-xl font-bold text-secondary-900">Changer d'abonnement</span>
            </div>
          </template>
          <template #content>
            <div v-if="loadingTiers" class="text-center py-8">
              <ProgressSpinner style="width: 40px; height: 40px" />
            </div>

            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div
                v-for="tier in availableTiers"
                :key="tier.tier"
                class="relative p-6 rounded-lg border-2 transition-all duration-200"
                :class="[
                  tier.is_current
                    ? 'border-primary-400 bg-primary-50'
                    : 'border-gray-200 hover:border-primary-400 hover:shadow-md cursor-pointer'
                ]"
                @click="!tier.is_current && selectTier(tier)"
              >
                <!-- Current Badge -->
                <div v-if="tier.is_current" class="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Tag value="ACTUEL" severity="success" class="text-xs font-bold" />
                </div>

                <!-- Tier Name -->
                <div class="text-center mb-4">
                  <h3 class="text-xl font-bold text-secondary-900 uppercase">{{ tier.tier }}</h3>
                </div>

                <!-- Features -->
                <div class="space-y-3 mb-6">
                  <div class="flex items-center gap-2">
                    <i class="pi pi-check-circle text-green-600"/>
                    <span class="text-sm text-gray-700">{{ tier.max_products }} produits</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <i class="pi pi-check-circle text-green-600"/>
                    <span class="text-sm text-gray-700">{{ tier.max_platforms }} plateformes</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <i class="pi pi-check-circle text-green-600"/>
                    <span class="text-sm text-gray-700">{{ tier.ai_credits_monthly }} crédits IA/mois</span>
                  </div>
                </div>

                <!-- Action Button -->
                <Button
                  v-if="!tier.is_current"
                  :label="getTierButtonLabel(tier.tier)"
                  class="w-full bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
                  size="small"
                  @click="selectTier(tier)"
                />
                <Button
                  v-else
                  label="Abonnement actuel"
                  class="w-full bg-gray-300 text-gray-600 border-0 font-semibold cursor-not-allowed"
                  size="small"
                  disabled
                />
              </div>
            </div>
          </template>
        </Card>

        <!-- AI Credits Purchase Section -->
        <Card class="shadow-md modern-rounded">
          <template #title>
            <div class="flex items-center gap-3">
              <i class="pi pi-shopping-cart text-primary-400 text-xl"/>
              <span class="text-xl font-bold text-secondary-900">Acheter des crédits IA supplémentaires</span>
            </div>
          </template>
          <template #content>
            <div class="mb-4">
              <p class="text-gray-600">
                Besoin de plus de crédits IA ? Achetez des packs supplémentaires sans changer d'abonnement.
              </p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div
                v-for="pack in creditPacks"
                :key="pack.credits"
                class="relative p-6 rounded-lg border-2 border-gray-200 hover:border-primary-400 hover:shadow-md transition-all duration-200 cursor-pointer"
                @click="selectCreditPack(pack)"
              >
                <!-- Popular Badge -->
                <div v-if="pack.popular" class="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Tag value="POPULAIRE" severity="success" class="text-xs font-bold" />
                </div>

                <!-- Credits Amount -->
                <div class="text-center mb-4">
                  <div class="text-3xl font-bold text-secondary-900 mb-1">{{ pack.credits }}</div>
                  <div class="text-sm text-gray-600">crédits IA</div>
                </div>

                <!-- Price -->
                <div class="text-center mb-4">
                  <div class="text-2xl font-bold text-primary-400">{{ pack.price }}€</div>
                  <div class="text-xs text-gray-500">{{ pack.pricePerCredit }}€ / crédit</div>
                </div>

                <!-- Features -->
                <div class="space-y-2 mb-6">
                  <div class="flex items-center gap-2 text-sm text-gray-600">
                    <i class="pi pi-check-circle text-green-600"/>
                    <span>Pas d'expiration</span>
                  </div>
                  <div class="flex items-center gap-2 text-sm text-gray-600">
                    <i class="pi pi-check-circle text-green-600"/>
                    <span>Utilisable immédiatement</span>
                  </div>
                  <div class="flex items-center gap-2 text-sm text-gray-600">
                    <i class="pi pi-check-circle text-green-600"/>
                    <span>Cumulable</span>
                  </div>
                </div>

                <!-- Buy Button -->
                <Button
                  label="Acheter"
                  class="w-full bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
                  size="small"
                  @click="selectCreditPack(pack)"
                />
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Fallback for SSR -->
      <template #fallback>
        <div class="flex items-center justify-center py-20">
          <ProgressSpinner />
        </div>
      </template>
    </ClientOnly>

    <!-- Upgrade Confirmation Dialog -->
    <Dialog
      v-model:visible="showUpgradeDialog"
      modal
      :header="`Confirmer le changement d'abonnement`"
      :style="{ width: '500px' }"
    >
      <div v-if="selectedTier" class="space-y-4">
        <p class="text-gray-700">
          Voulez-vous vraiment passer à l'abonnement <strong class="text-secondary-900">{{ selectedTier.tier.toUpperCase() }}</strong> ?
        </p>

        <div class="bg-secondary-50 p-4 rounded-lg space-y-2">
          <div class="flex justify-between">
            <span class="text-gray-600">Produits :</span>
            <span class="font-bold text-secondary-900">{{ selectedTier.max_products }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Plateformes :</span>
            <span class="font-bold text-secondary-900">{{ selectedTier.max_platforms }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Crédits IA/mois :</span>
            <span class="font-bold text-secondary-900">{{ selectedTier.ai_credits_monthly }}</span>
          </div>
        </div>

        <Message severity="info" :closable="false">
          Le changement sera effectif immédiatement et vos nouveaux quotas seront disponibles.
        </Message>
      </div>

      <template #footer>
        <Button
          label="Annuler"
          severity="secondary"
          :disabled="isUpgrading"
          @click="showUpgradeDialog = false"
        />
        <Button
          label="Confirmer"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          :loading="isUpgrading"
          @click="confirmUpgrade"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import type { SubscriptionTier } from '~/composables/useSubscription'
import { useToast } from 'primevue/usetoast'

definePageMeta({
  layout: 'dashboard'
})

const { showSuccess, showError, showInfo, showWarn } = useAppToast()
const router = useRouter()
const { getSubscriptionInfo, getAvailableTiers } = useSubscription()

// SSR-safe: useToast requires client-side ToastService
const toast = import.meta.client ? useToast() : null

// State
const loading = ref(true)
const loadingTiers = ref(true)
const error = ref<string | null>(null)
const showUpgradeDialog = ref(false)
const isUpgrading = ref(false)
const selectedTier = ref<SubscriptionTier | null>(null)

// Subscription info
const currentTier = ref('')
const currentPrice = ref(0)
const maxProducts = ref(0)
const maxPlatforms = ref(0)
const aiCreditsMonthly = ref(0)
const aiCreditsRemaining = ref(0)
const currentProducts = ref(0)
const currentPlatforms = ref(0)

// Available tiers
const availableTiers = ref<SubscriptionTier[]>([])

// AI Credit Packs (static data - could be moved to API later)
const creditPacks = ref([
  {
    credits: 100,
    price: 9.99,
    pricePerCredit: '0.10',
    popular: false
  },
  {
    credits: 500,
    price: 39.99,
    pricePerCredit: '0.08',
    popular: true
  },
  {
    credits: 1000,
    price: 69.99,
    pricePerCredit: '0.07',
    popular: false
  },
  {
    credits: 5000,
    price: 299.99,
    pricePerCredit: '0.06',
    popular: false
  }
])

// Computed
const productProgress = computed(() => {
  if (maxProducts.value === 0) return 0
  return Math.min((currentProducts.value / maxProducts.value) * 100, 100)
})

const platformProgress = computed(() => {
  if (maxPlatforms.value === 0) return 0
  return Math.min((currentPlatforms.value / maxPlatforms.value) * 100, 100)
})

// Methods
const getTierSeverity = (tier: string) => {
  const severityMap: Record<string, string> = {
    free: 'secondary',
    starter: 'info',
    pro: 'warning',
    enterprise: 'success'
  }
  return severityMap[tier.toLowerCase()] || 'secondary'
}

const getTierButtonLabel = (tier: string) => {
  const currentIndex = ['free', 'starter', 'pro', 'enterprise'].indexOf(currentTier.value.toLowerCase())
  const targetIndex = ['free', 'starter', 'pro', 'enterprise'].indexOf(tier.toLowerCase())

  if (targetIndex > currentIndex) {
    return 'Passer à ' + tier.toUpperCase()
  } else {
    return 'Rétrograder à ' + tier.toUpperCase()
  }
}

const selectTier = (tier: any) => {
  // Redirect to upgrade intermediate page
  router.push(`/dashboard/subscription/upgrade/${tier.tier}`)
}

const selectCreditPack = (pack: any) => {
  // Redirect to credits intermediate page
  router.push(`/dashboard/subscription/credits/${pack.credits}`)
}

const getTierPrice = (tier: string): number => {
  // Prix fictifs pour les abonnements (mock)
  const prices: Record<string, number> = {
    free: 0,
    starter: 19.99,
    pro: 49.99,
    enterprise: 199.99
  }
  return prices[tier.toLowerCase()] || 0
}

const confirmUpgrade = async () => {
  if (!selectedTier.value) return

  isUpgrading.value = true

  // Simulation du changement d'abonnement (mode mock)
  await new Promise(resolve => setTimeout(resolve, 1500))

  try {
    // Update local state avec les données du tier sélectionné
    currentTier.value = selectedTier.value.tier
    maxProducts.value = selectedTier.value.max_products
    maxPlatforms.value = selectedTier.value.max_platforms
    aiCreditsMonthly.value = selectedTier.value.ai_credits_monthly
    aiCreditsRemaining.value = selectedTier.value.ai_credits_monthly

    // Update is_current flags
    availableTiers.value.forEach(tier => {
      tier.is_current = tier.tier === selectedTier.value?.tier
    })

    showSuccess('Abonnement modifié', `Vous êtes maintenant sur l'abonnement ${selectedTier.value?.tier?.toUpperCase() || ''}`, 3000)

    showUpgradeDialog.value = false
  } catch (err: any) {
    showError('Erreur', err.message || 'Impossible de modifier l\'abonnement', 5000)
  } finally {
    isUpgrading.value = false
  }
}

const loadSubscriptionInfo = async () => {
  try {
    const data = await getSubscriptionInfo()

    currentTier.value = data.current_tier
    currentPrice.value = data.price
    maxProducts.value = data.max_products
    maxPlatforms.value = data.max_platforms
    aiCreditsMonthly.value = data.ai_credits_monthly
    aiCreditsRemaining.value = data.ai_credits_remaining
    currentProducts.value = data.current_products_count
    currentPlatforms.value = data.current_platforms_count
  } catch (err: any) {
    console.error('Error loading subscription info:', err)
    error.value = err.message || 'Impossible de charger les informations d\'abonnement'
  } finally {
    loading.value = false
  }
}

const loadTiers = async () => {
  try {
    const tiers = await getAvailableTiers()
    availableTiers.value = tiers
  } catch (err: any) {
    console.error('Error loading tiers:', err)
    showWarn('Avertissement', 'Impossible de charger les tiers d\'abonnement', 3000)
  } finally {
    loadingTiers.value = false
  }
}

// Fetch subscription data once on page load (client-side only, requires auth token)
if (import.meta.client) {
  await callOnce(async () => {
    await Promise.all([
      loadSubscriptionInfo(),
      loadTiers()
    ])
  })
}
</script>

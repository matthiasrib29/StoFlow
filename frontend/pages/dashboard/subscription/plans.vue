<template>
  <div class="page-container">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-secondary-900 mb-2">Changer d'abonnement</h1>
      <p class="text-gray-600">Choisissez le plan qui correspond le mieux à vos besoins</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <ProgressSpinner />
    </div>

    <!-- Error -->
    <Message v-else-if="error" severity="error" :closable="false" class="mb-6">
      {{ error }}
    </Message>

    <!-- Plans Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div
        v-for="tier in availableTiers"
        :key="tier.tier"
        class="relative p-6 rounded-xl border-2 transition-all duration-200 bg-white"
        :class="[
          tier.is_current
            ? 'border-primary-400 bg-primary-50 shadow-lg'
            : 'border-gray-200 hover:border-primary-400 hover:shadow-lg cursor-pointer'
        ]"
        @click="!tier.is_current && openConfirmDialog(tier)"
      >
        <!-- Current Badge -->
        <div v-if="tier.is_current" class="absolute -top-3 left-1/2 -translate-x-1/2">
          <Tag value="ACTUEL" severity="success" class="text-xs font-bold px-3" />
        </div>

        <!-- Tier Name & Price -->
        <div class="text-center mb-6">
          <h3 class="text-2xl font-bold text-secondary-900 uppercase mb-2">{{ tier.tier }}</h3>
          <div class="text-3xl font-bold text-primary-400">
            {{ getTierPrice(tier.tier) }}€
            <span class="text-sm font-normal text-gray-500">/mois</span>
          </div>
        </div>

        <!-- Features -->
        <div class="space-y-4 mb-6">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
              <i class="pi pi-box text-green-600 text-sm"/>
            </div>
            <span class="text-gray-700">{{ tier.max_products }} produits</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
              <i class="pi pi-globe text-blue-600 text-sm"/>
            </div>
            <span class="text-gray-700">{{ tier.max_platforms }} plateformes</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
              <i class="pi pi-sparkles text-purple-600 text-sm"/>
            </div>
            <span class="text-gray-700">{{ tier.ai_credits_monthly }} crédits IA/mois</span>
          </div>
        </div>

        <!-- Action Button -->
        <Button
          v-if="!tier.is_current"
          :label="getButtonLabel(tier.tier)"
          class="w-full bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          @click.stop="openConfirmDialog(tier)"
        />
        <Button
          v-else
          label="Abonnement actuel"
          class="w-full bg-gray-200 text-gray-500 border-0 font-semibold cursor-not-allowed"
          disabled
        />
      </div>
    </div>

    <!-- Confirmation Dialog -->
    <Dialog
      v-model:visible="showConfirmDialog"
      modal
      header="Confirmer le changement"
      :style="{ width: '450px' }"
      :closable="!isProcessing"
    >
      <div v-if="selectedTier" class="space-y-4">
        <p class="text-gray-700">
          Vous allez passer à l'abonnement <strong class="text-secondary-900">{{ selectedTier.tier.toUpperCase() }}</strong>
        </p>

        <div class="bg-secondary-50 p-4 rounded-lg space-y-3">
          <div class="flex justify-between items-center">
            <span class="text-gray-600">Produits</span>
            <span class="font-bold text-secondary-900">{{ selectedTier.max_products }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600">Plateformes</span>
            <span class="font-bold text-secondary-900">{{ selectedTier.max_platforms }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600">Crédits IA/mois</span>
            <span class="font-bold text-secondary-900">{{ selectedTier.ai_credits_monthly }}</span>
          </div>
          <Divider />
          <div class="flex justify-between items-center">
            <span class="text-gray-600 font-semibold">Prix mensuel</span>
            <span class="font-bold text-primary-400 text-xl">{{ getTierPrice(selectedTier.tier) }}€</span>
          </div>
        </div>
      </div>

      <template #footer>
        <Button
          label="Annuler"
          severity="secondary"
          :disabled="isProcessing"
          @click="showConfirmDialog = false"
        />
        <Button
          label="Confirmer le changement"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          :loading="isProcessing"
          @click="confirmChange"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import type { SubscriptionTier } from '~/composables/useSubscription'

definePageMeta({
  layout: 'dashboard'
})

const { showSuccess, showError } = useAppToast()
const router = useRouter()
const { getSubscriptionInfo, getAvailableTiers } = useSubscription()

// State
const loading = ref(true)
const error = ref<string | null>(null)
const showConfirmDialog = ref(false)
const isProcessing = ref(false)
const selectedTier = ref<SubscriptionTier | null>(null)
const currentTier = ref('')
const availableTiers = ref<SubscriptionTier[]>([])

// Methods
const getTierPrice = (tier: string): number => {
  const prices: Record<string, number> = {
    free: 0,
    starter: 19.99,
    pro: 49.99,
    enterprise: 199.99
  }
  return prices[tier.toLowerCase()] || 0
}

const getButtonLabel = (tier: string): string => {
  const tiers = ['free', 'starter', 'pro', 'enterprise']
  const currentIndex = tiers.indexOf(currentTier.value.toLowerCase())
  const targetIndex = tiers.indexOf(tier.toLowerCase())

  if (targetIndex > currentIndex) {
    return 'Passer au ' + tier.toUpperCase()
  }
  return 'Choisir ' + tier.toUpperCase()
}

const openConfirmDialog = (tier: SubscriptionTier) => {
  selectedTier.value = tier
  showConfirmDialog.value = true
}

const confirmChange = async () => {
  if (!selectedTier.value) return

  isProcessing.value = true

  try {
    // TODO: Call real API when Stripe is integrated
    // For now, redirect to payment page
    router.push({
      path: '/dashboard/subscription/payment',
      query: {
        type: 'upgrade',
        tier: selectedTier.value.tier,
        price: getTierPrice(selectedTier.value.tier)
      }
    })
  } catch (err: any) {
    showError('Erreur', err.message || 'Impossible de changer d\'abonnement')
  } finally {
    isProcessing.value = false
  }
}

const loadData = async () => {
  try {
    const [info, tiers] = await Promise.all([
      getSubscriptionInfo(),
      getAvailableTiers()
    ])

    currentTier.value = info.current_tier
    availableTiers.value = tiers
  } catch (err: any) {
    error.value = err.message || 'Impossible de charger les données'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

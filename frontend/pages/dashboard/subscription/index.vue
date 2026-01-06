<template>
  <div class="page-container">
    <PageHeader
      title="Mon abonnement"
      subtitle="Consultez et gérez votre abonnement StoFlow"
    />

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
                  value: { class: productProgress > 80 ? 'bg-red-500' : 'bg-primary-400' }
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
                  value: { class: platformProgress > 80 ? 'bg-red-500' : 'bg-primary-400' }
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
              <p class="text-xs text-gray-500 mt-1">{{ aiCreditsMonthly }} / mois inclus</p>
            </div>
          </div>
        </template>
      </Card>

      <!-- Quick Actions -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Change Plan Card -->
        <Card class="shadow-md modern-rounded hover:shadow-lg transition-shadow cursor-pointer" @click="router.push('/dashboard/subscription/plans')">
          <template #content>
            <div class="flex items-center gap-4">
              <div class="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center">
                <i class="pi pi-sync text-blue-600 text-2xl"/>
              </div>
              <div class="flex-1">
                <h3 class="text-lg font-bold text-secondary-900 mb-1">Changer d'abonnement</h3>
                <p class="text-sm text-gray-600">Passez à un plan supérieur pour débloquer plus de fonctionnalités</p>
              </div>
              <i class="pi pi-chevron-right text-gray-400 text-xl"/>
            </div>
          </template>
        </Card>

        <!-- Buy Credits Card -->
        <Card class="shadow-md modern-rounded hover:shadow-lg transition-shadow cursor-pointer" @click="router.push('/dashboard/subscription/credits')">
          <template #content>
            <div class="flex items-center gap-4">
              <div class="w-14 h-14 rounded-full bg-purple-100 flex items-center justify-center">
                <i class="pi pi-bolt text-purple-600 text-2xl"/>
              </div>
              <div class="flex-1">
                <h3 class="text-lg font-bold text-secondary-900 mb-1">Crédits IA</h3>
                <p class="text-sm text-gray-600">Besoin de plus de crédits ? Achetez des packs supplémentaires</p>
              </div>
              <i class="pi pi-chevron-right text-gray-400 text-xl"/>
            </div>
          </template>
        </Card>
      </div>

      <!-- Subscription Details -->
      <Card class="shadow-md modern-rounded">
        <template #title>
          <div class="flex items-center gap-3">
            <i class="pi pi-info-circle text-primary-400 text-xl"/>
            <span class="text-xl font-bold text-secondary-900">Détails de l'abonnement</span>
          </div>
        </template>
        <template #content>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-4">
              <div class="flex justify-between py-2 border-b border-gray-100">
                <span class="text-gray-600">Plan actuel</span>
                <span class="font-semibold text-secondary-900">{{ currentTier.toUpperCase() }}</span>
              </div>
              <div class="flex justify-between py-2 border-b border-gray-100">
                <span class="text-gray-600">Prix mensuel</span>
                <span class="font-semibold text-secondary-900">{{ currentPrice }}€</span>
              </div>
              <div class="flex justify-between py-2">
                <span class="text-gray-600">Statut</span>
                <Tag value="Actif" severity="success" />
              </div>
            </div>
            <div class="space-y-4">
              <div class="flex justify-between py-2 border-b border-gray-100">
                <span class="text-gray-600">Produits max</span>
                <span class="font-semibold text-secondary-900">{{ maxProducts }}</span>
              </div>
              <div class="flex justify-between py-2 border-b border-gray-100">
                <span class="text-gray-600">Plateformes max</span>
                <span class="font-semibold text-secondary-900">{{ maxPlatforms }}</span>
              </div>
              <div class="flex justify-between py-2">
                <span class="text-gray-600">Crédits IA / mois</span>
                <span class="font-semibold text-secondary-900">{{ aiCreditsMonthly }}</span>
              </div>
            </div>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { subscriptionLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()
const { getSubscriptionInfo } = useSubscription()

// State
const loading = ref(true)
const error = ref<string | null>(null)

// Subscription info
const currentTier = ref('')
const currentPrice = ref(0)
const maxProducts = ref(0)
const maxPlatforms = ref(0)
const aiCreditsMonthly = ref(0)
const aiCreditsRemaining = ref(0)
const currentProducts = ref(0)
const currentPlatforms = ref(0)

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
    subscriptionLogger.error('Error loading subscription info', { error: err.message })
    error.value = err.message || 'Impossible de charger les informations d\'abonnement'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSubscriptionInfo()
})
</script>

<template>
  <div class="page-container">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-secondary-900 mb-2">Crédits IA</h1>
      <p class="text-gray-600">Achetez des crédits supplémentaires pour utiliser les fonctionnalités IA</p>
    </div>

    <!-- Current Credits Info -->
    <Card class="shadow-md modern-rounded mb-6">
      <template #content>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
              <i class="pi pi-sparkles text-primary-400 text-xl"/>
            </div>
            <div>
              <p class="text-sm text-gray-600">Vos crédits actuels</p>
              <p class="text-2xl font-bold text-secondary-900">{{ currentCredits }}</p>
            </div>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-600">Inclus dans votre abonnement</p>
            <p class="text-lg font-semibold text-gray-700">{{ monthlyCredits }} / mois</p>
          </div>
        </div>
      </template>
    </Card>

    <!-- Credits Packs Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div
        v-for="pack in creditPacks"
        :key="pack.credits"
        class="relative p-6 rounded-xl border-2 border-gray-200 hover:border-primary-400 hover:shadow-lg transition-all duration-200 cursor-pointer bg-white"
        @click="openConfirmDialog(pack)"
      >
        <!-- Popular Badge -->
        <div v-if="pack.popular" class="absolute -top-3 left-1/2 -translate-x-1/2">
          <Tag value="POPULAIRE" severity="success" class="text-xs font-bold px-3" />
        </div>

        <!-- Credits Amount -->
        <div class="text-center mb-4">
          <div class="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-3">
            <i class="pi pi-bolt text-primary-400 text-2xl"/>
          </div>
          <div class="text-4xl font-bold text-secondary-900">{{ pack.credits }}</div>
          <div class="text-sm text-gray-600">crédits IA</div>
        </div>

        <!-- Price -->
        <div class="text-center mb-6">
          <div class="text-3xl font-bold text-primary-400">{{ pack.price }}€</div>
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
            <span>Cumulable avec l'abonnement</span>
          </div>
        </div>

        <!-- Buy Button -->
        <Button
          label="Acheter ce pack"
          class="w-full bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          @click.stop="openConfirmDialog(pack)"
        />
      </div>
    </div>

    <!-- Use Cases Section -->
    <Card class="shadow-md modern-rounded mt-8">
      <template #title>
        <div class="flex items-center gap-3">
          <i class="pi pi-lightbulb text-primary-400 text-xl"/>
          <span class="text-xl font-bold text-secondary-900">Que pouvez-vous faire avec les crédits IA ?</span>
        </div>
      </template>
      <template #content>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="flex items-start gap-3">
            <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
              <i class="pi pi-pencil text-blue-600"/>
            </div>
            <div>
              <h4 class="font-semibold text-secondary-900 mb-1">Descriptions automatiques</h4>
              <p class="text-sm text-gray-600">Générez des descriptions optimisées pour vos produits</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <div class="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center flex-shrink-0">
              <i class="pi pi-language text-green-600"/>
            </div>
            <div>
              <h4 class="font-semibold text-secondary-900 mb-1">Traductions</h4>
              <p class="text-sm text-gray-600">Traduisez vos annonces dans plusieurs langues</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <div class="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0">
              <i class="pi pi-tag text-purple-600"/>
            </div>
            <div>
              <h4 class="font-semibold text-secondary-900 mb-1">Titres optimisés</h4>
              <p class="text-sm text-gray-600">Créez des titres accrocheurs pour vos annonces</p>
            </div>
          </div>
        </div>
      </template>
    </Card>

    <!-- Confirmation Dialog -->
    <Dialog
      v-model:visible="showConfirmDialog"
      modal
      header="Confirmer l'achat"
      :style="{ width: '450px' }"
      :closable="!isProcessing"
    >
      <div v-if="selectedPack" class="space-y-4">
        <div class="text-center py-4">
          <div class="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-4">
            <i class="pi pi-bolt text-primary-400 text-3xl"/>
          </div>
          <div class="text-4xl font-bold text-secondary-900 mb-1">{{ selectedPack.credits }}</div>
          <div class="text-gray-600">crédits IA</div>
        </div>

        <div class="bg-secondary-50 p-4 rounded-lg space-y-3">
          <div class="flex justify-between items-center">
            <span class="text-gray-600">Prix unitaire</span>
            <span class="font-medium text-secondary-900">{{ selectedPack.pricePerCredit }}€ / crédit</span>
          </div>
          <Divider />
          <div class="flex justify-between items-center">
            <span class="text-gray-600 font-semibold">Total à payer</span>
            <span class="font-bold text-primary-400 text-2xl">{{ selectedPack.price }}€</span>
          </div>
        </div>

        <div class="flex items-center gap-2 text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
          <i class="pi pi-info-circle text-blue-600"/>
          <span>Après achat, vous aurez {{ currentCredits + selectedPack.credits }} crédits</span>
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
          label="Procéder au paiement"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          :loading="isProcessing"
          @click="confirmPurchase"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { subscriptionLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard'
})

const { showError } = useAppToast()
const router = useRouter()
const { getSubscriptionInfo } = useSubscription()

// State
const showConfirmDialog = ref(false)
const isProcessing = ref(false)
const currentCredits = ref(0)
const monthlyCredits = ref(0)
const selectedPack = ref<typeof creditPacks.value[0] | null>(null)

// Credit Packs
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

// Methods
const openConfirmDialog = (pack: typeof creditPacks.value[0]) => {
  selectedPack.value = pack
  showConfirmDialog.value = true
}

const confirmPurchase = async () => {
  if (!selectedPack.value) return

  isProcessing.value = true

  try {
    // Redirect to payment page
    router.push({
      path: '/dashboard/subscription/payment',
      query: {
        type: 'credits',
        credits: selectedPack.value.credits,
        price: selectedPack.value.price
      }
    })
  } catch (err: any) {
    showError('Erreur', err.message || 'Impossible de procéder au paiement')
  } finally {
    isProcessing.value = false
  }
}

const loadData = async () => {
  try {
    const info = await getSubscriptionInfo()
    currentCredits.value = info.ai_credits_remaining
    monthlyCredits.value = info.ai_credits_monthly
  } catch (err) {
    subscriptionLogger.error('Error loading subscription info', { error: err })
  }
}

onMounted(() => {
  loadData()
})
</script>

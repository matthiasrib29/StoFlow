<template>
  <div class="p-8 max-w-7xl mx-auto">
    <!-- Header avec navigation -->
    <div class="mb-6">
      <Button
        label="Retour à l'abonnement"
        icon="pi pi-arrow-left"
        class="mb-4"
        severity="secondary"
        text
        @click="goBack"
      />
      <h1 class="text-3xl font-bold text-secondary-900 mb-2">
        {{ isUpgrade ? 'Upgrade' : 'Changement' }} d'abonnement
      </h1>
      <p class="text-gray-600">Vérifiez les détails avant de procéder au paiement</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <ProgressSpinner />
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main Content -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Comparaison Actuel vs Nouveau -->
        <Card class="shadow-md modern-rounded">
          <template #title>
            <div class="flex items-center gap-3">
              <i class="pi pi-arrow-right-arrow-left text-primary-400 text-xl"></i>
              <span class="text-xl font-bold text-secondary-900">Votre changement</span>
            </div>
          </template>
          <template #content>
            <div class="grid grid-cols-2 gap-4">
              <!-- Current Tier -->
              <div class="p-4 bg-gray-50 rounded-lg border-2 border-gray-300">
                <div class="text-center mb-3">
                  <Tag value="ACTUEL" severity="secondary" class="text-xs mb-2" />
                  <div class="text-2xl font-bold text-gray-700 uppercase">{{ currentTier }}</div>
                  <div class="text-lg text-gray-500 mt-1">{{ getTierPrice(currentTier) }}€/mois</div>
                </div>
                <Divider />
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between">
                    <span class="text-gray-600">Produits:</span>
                    <span class="font-semibold">{{ currentTierData?.max_products }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">Plateformes:</span>
                    <span class="font-semibold">{{ currentTierData?.max_platforms }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">Crédits IA/mois:</span>
                    <span class="font-semibold">{{ currentTierData?.ai_credits_monthly }}</span>
                  </div>
                </div>
              </div>

              <!-- New Tier -->
              <div class="p-4 bg-primary-50 rounded-lg border-2 border-primary-400">
                <div class="text-center mb-3">
                  <Tag :value="isUpgrade ? 'NOUVEAU' : 'NOUVEAU'" severity="success" class="text-xs mb-2" />
                  <div class="text-2xl font-bold text-secondary-900 uppercase">{{ selectedTier }}</div>
                  <div class="text-lg text-primary-400 font-bold mt-1">{{ getTierPrice(selectedTier) }}€/mois</div>
                </div>
                <Divider />
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between">
                    <span class="text-gray-600">Produits:</span>
                    <span class="font-semibold text-green-600">{{ selectedTierData?.max_products }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">Plateformes:</span>
                    <span class="font-semibold text-green-600">{{ selectedTierData?.max_platforms }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">Crédits IA/mois:</span>
                    <span class="font-semibold text-green-600">{{ selectedTierData?.ai_credits_monthly }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Gains/Pertes -->
            <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 class="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                <i class="pi pi-arrow-up text-blue-600"></i>
                Ce qui change pour vous
              </h4>
              <div class="grid grid-cols-3 gap-3 text-sm">
                <div class="text-center">
                  <div class="text-2xl font-bold" :class="productsDiff > 0 ? 'text-green-600' : 'text-red-600'">
                    {{ productsDiff > 0 ? '+' : '' }}{{ productsDiff }}
                  </div>
                  <div class="text-gray-600">produits</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold" :class="platformsDiff > 0 ? 'text-green-600' : 'text-red-600'">
                    {{ platformsDiff > 0 ? '+' : '' }}{{ platformsDiff }}
                  </div>
                  <div class="text-gray-600">plateformes</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold" :class="creditsDiff > 0 ? 'text-green-600' : 'text-red-600'">
                    {{ creditsDiff > 0 ? '+' : '' }}{{ creditsDiff }}
                  </div>
                  <div class="text-gray-600">crédits IA</div>
                </div>
              </div>
            </div>
          </template>
        </Card>

        <!-- Tableau comparatif complet -->
        <Card class="shadow-md modern-rounded">
          <template #title>
            <div class="flex items-center gap-3">
              <i class="pi pi-table text-primary-400 text-xl"></i>
              <span class="text-xl font-bold text-secondary-900">Comparaison de tous les abonnements</span>
            </div>
          </template>
          <template #content>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b-2 border-gray-200">
                    <th class="text-left py-3 px-2 font-semibold text-gray-700">Fonctionnalité</th>
                    <th v-for="tier in allTiers" :key="tier.tier"
                        class="text-center py-3 px-2 font-semibold"
                        :class="tier.tier === selectedTier ? 'bg-primary-50' : ''">
                      <div class="uppercase text-xs mb-1">{{ tier.tier }}</div>
                      <div class="text-primary-400 font-bold">{{ getTierPrice(tier.tier) }}€</div>
                      <Tag v-if="tier.tier === currentTier" value="Actuel" severity="secondary" class="text-xs mt-1" />
                      <Tag v-if="tier.tier === selectedTier" value="Nouveau" severity="success" class="text-xs mt-1" />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-b border-gray-100">
                    <td class="py-3 px-2 font-medium text-gray-700">Produits maximum</td>
                    <td v-for="tier in allTiers" :key="`products-${tier.tier}`"
                        class="text-center py-3 px-2"
                        :class="tier.tier === selectedTier ? 'bg-primary-50 font-bold text-green-600' : ''">
                      {{ tier.max_products === 999999 ? 'Illimité' : tier.max_products }}
                    </td>
                  </tr>
                  <tr class="border-b border-gray-100">
                    <td class="py-3 px-2 font-medium text-gray-700">Plateformes connectées</td>
                    <td v-for="tier in allTiers" :key="`platforms-${tier.tier}`"
                        class="text-center py-3 px-2"
                        :class="tier.tier === selectedTier ? 'bg-primary-50 font-bold text-green-600' : ''">
                      {{ tier.max_platforms === 999 ? 'Illimité' : tier.max_platforms }}
                    </td>
                  </tr>
                  <tr class="border-b border-gray-100">
                    <td class="py-3 px-2 font-medium text-gray-700">Crédits IA par mois</td>
                    <td v-for="tier in allTiers" :key="`credits-${tier.tier}`"
                        class="text-center py-3 px-2"
                        :class="tier.tier === selectedTier ? 'bg-primary-50 font-bold text-green-600' : ''">
                      {{ tier.ai_credits_monthly }}
                    </td>
                  </tr>
                  <tr class="border-b border-gray-100">
                    <td class="py-3 px-2 font-medium text-gray-700">Support prioritaire</td>
                    <td v-for="tier in allTiers" :key="`support-${tier.tier}`"
                        class="text-center py-3 px-2"
                        :class="tier.tier === selectedTier ? 'bg-primary-50' : ''">
                      <i v-if="['pro', 'enterprise'].includes(tier.tier)" class="pi pi-check text-green-600 text-lg"></i>
                      <i v-else class="pi pi-minus text-gray-400"></i>
                    </td>
                  </tr>
                  <tr class="border-b border-gray-100">
                    <td class="py-3 px-2 font-medium text-gray-700">API Access</td>
                    <td v-for="tier in allTiers" :key="`api-${tier.tier}`"
                        class="text-center py-3 px-2"
                        :class="tier.tier === selectedTier ? 'bg-primary-50' : ''">
                      <i v-if="tier.tier === 'enterprise'" class="pi pi-check text-green-600 text-lg"></i>
                      <i v-else class="pi pi-minus text-gray-400"></i>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Action buttons pour changer de tier -->
            <div class="mt-4 flex gap-2 flex-wrap justify-center">
              <Button
                v-for="tier in allTiers.filter(t => t.tier !== selectedTier)"
                :key="`change-${tier.tier}`"
                :label="`Choisir ${tier.tier.toUpperCase()}`"
                size="small"
                outlined
                @click="changeTier(tier.tier)"
              />
            </div>
          </template>
        </Card>

        <!-- Facturation et conditions -->
        <Card class="shadow-md modern-rounded">
          <template #title>
            <div class="flex items-center gap-3">
              <i class="pi pi-info-circle text-primary-400 text-xl"></i>
              <span class="text-xl font-bold text-secondary-900">Informations importantes</span>
            </div>
          </template>
          <template #content>
            <!-- Calcul prorata -->
            <div class="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-4">
              <h4 class="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                <i class="pi pi-calculator"></i>
                Calcul prorata
              </h4>
              <p class="text-sm text-gray-700 mb-3">
                Votre changement d'abonnement prend effet immédiatement. Le montant est calculé au prorata
                des jours restants dans le mois en cours.
              </p>
              <div class="bg-white rounded p-3 space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-600">Jours restants ce mois:</span>
                  <span class="font-semibold">{{ daysRemainingInMonth }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Crédit abonnement actuel:</span>
                  <span class="font-semibold text-green-600">-{{ prorataCredit.toFixed(2) }}€</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Coût nouvel abonnement (prorata):</span>
                  <span class="font-semibold">+{{ prorataCost.toFixed(2) }}€</span>
                </div>
                <Divider />
                <div class="flex justify-between text-base">
                  <span class="font-bold text-gray-900">À payer aujourd'hui:</span>
                  <span class="font-bold text-primary-400">{{ prorataTotal.toFixed(2) }}€</span>
                </div>
                <div class="text-xs text-gray-500 mt-2">
                  * À partir du mois prochain: {{ getTierPrice(selectedTier) }}€/mois
                </div>
              </div>
            </div>

            <!-- Politique d'annulation -->
            <Accordion :multiple="true">
              <AccordionTab header="🔄 Politique d'annulation et remboursement">
                <div class="text-sm text-gray-700 space-y-2">
                  <p>
                    <strong>Annulation:</strong> Vous pouvez annuler votre abonnement à tout moment depuis vos paramètres.
                    L'annulation prend effet à la fin de la période de facturation en cours.
                  </p>
                  <p>
                    <strong>Remboursement:</strong> Si vous changez d'avis dans les 14 jours suivant un upgrade,
                    vous pouvez demander un remboursement complet. Passé ce délai, aucun remboursement n'est possible.
                  </p>
                  <p>
                    <strong>Downgrade:</strong> Si vous passez à un abonnement inférieur, le changement prend effet
                    au prochain cycle de facturation. Vous conservez vos avantages actuels jusqu'à la fin du mois.
                  </p>
                </div>
              </AccordionTab>
              <AccordionTab header="💳 Modes de paiement acceptés">
                <div class="text-sm text-gray-700">
                  <p class="mb-2">Nous acceptons les modes de paiement suivants:</p>
                  <ul class="list-disc list-inside space-y-1">
                    <li>Cartes bancaires (Visa, Mastercard, American Express)</li>
                    <li>PayPal</li>
                    <li>Virement bancaire (pour les abonnements Enterprise)</li>
                  </ul>
                  <p class="mt-2 text-xs text-gray-500">
                    * Tous les paiements sont sécurisés et cryptés
                  </p>
                </div>
              </AccordionTab>
              <AccordionTab header="📅 Cycle de facturation">
                <div class="text-sm text-gray-700">
                  <p class="mb-2">Votre abonnement est facturé mensuellement:</p>
                  <ul class="list-disc list-inside space-y-1">
                    <li>Date de renouvellement: Le {{ dayOfMonth }} de chaque mois</li>
                    <li>Vous recevez une facture par email avant chaque prélèvement</li>
                    <li>Vous pouvez consulter l'historique dans vos paramètres</li>
                  </ul>
                </div>
              </AccordionTab>
            </Accordion>
          </template>
        </Card>
      </div>

      <!-- Sidebar - Récapitulatif et CTA -->
      <div class="lg:col-span-1">
        <Card class="shadow-md modern-rounded sticky top-8">
          <template #title>
            <span class="text-xl font-bold text-secondary-900">Récapitulatif</span>
          </template>
          <template #content>
            <div class="space-y-4">
              <!-- Tier sélectionné -->
              <div class="p-4 bg-primary-50 rounded-lg border-2 border-primary-400 text-center">
                <div class="text-xs text-gray-600 mb-1">Abonnement</div>
                <div class="text-2xl font-bold text-secondary-900 uppercase mb-2">{{ selectedTier }}</div>
                <div class="text-3xl font-bold text-primary-400 mb-1">{{ getTierPrice(selectedTier) }}€</div>
                <div class="text-xs text-gray-600">par mois</div>
              </div>

              <Divider />

              <!-- À payer aujourd'hui -->
              <div class="p-3 bg-white border-2 border-primary-400 rounded-lg">
                <div class="text-center">
                  <div class="text-xs text-gray-600 mb-1">À payer aujourd'hui (prorata)</div>
                  <div class="text-2xl font-bold text-primary-400">{{ prorataTotal.toFixed(2) }}€</div>
                  <div class="text-xs text-gray-500 mt-1">puis {{ getTierPrice(selectedTier) }}€/mois</div>
                </div>
              </div>

              <!-- Avantages -->
              <div class="space-y-2">
                <div class="flex items-center gap-2 text-sm text-gray-700">
                  <i class="pi pi-check-circle text-green-600"></i>
                  <span>Activation immédiate</span>
                </div>
                <div class="flex items-center gap-2 text-sm text-gray-700">
                  <i class="pi pi-check-circle text-green-600"></i>
                  <span>Annulable à tout moment</span>
                </div>
                <div class="flex items-center gap-2 text-sm text-gray-700">
                  <i class="pi pi-check-circle text-green-600"></i>
                  <span>Remboursement sous 14 jours</span>
                </div>
                <div class="flex items-center gap-2 text-sm text-gray-700">
                  <i class="pi pi-check-circle text-green-600"></i>
                  <span>Support client inclus</span>
                </div>
              </div>

              <Divider />

              <!-- CTA Buttons -->
              <div class="space-y-3">
                <Button
                  label="Procéder au paiement"
                  icon="pi pi-arrow-right"
                  iconPos="right"
                  class="w-full bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
                  size="large"
                  @click="proceedToPayment"
                />
                <Button
                  label="Retour"
                  icon="pi pi-arrow-left"
                  class="w-full"
                  severity="secondary"
                  outlined
                  @click="goBack"
                />
              </div>

              <!-- Sécurité -->
              <div class="flex items-center justify-center gap-2 text-xs text-gray-500 pt-2">
                <i class="pi pi-lock"></i>
                <span>Paiement 100% sécurisé</span>
              </div>
            </div>
          </template>
        </Card>
      </div>
    </div> <!-- v-else grid -->
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()
const route = useRoute()
const { getSubscriptionInfo, getAvailableTiers } = useSubscription()

// State
const loading = ref(true)
const currentTier = ref('')
const allTiers = ref<any[]>([])

// Prix des tiers (sera chargé depuis l'API)
const tierPrices = ref<Record<string, number>>({})

// Selected tier from route
const selectedTier = computed(() => route.params.tier as string)
const selectedTierData = computed(() => allTiers.value.find(t => t.tier === selectedTier.value))
const currentTierData = computed(() => allTiers.value.find(t => t.tier === currentTier.value))

// Check if upgrade or downgrade
const isUpgrade = computed(() => {
  const tiers = ['free', 'starter', 'pro', 'enterprise']
  const currentIndex = tiers.indexOf(currentTier.value)
  const selectedIndex = tiers.indexOf(selectedTier.value)
  return selectedIndex > currentIndex
})

// Differences
const productsDiff = computed(() =>
  (selectedTierData.value?.max_products || 0) - (currentTierData.value?.max_products || 0)
)
const platformsDiff = computed(() =>
  (selectedTierData.value?.max_platforms || 0) - (currentTierData.value?.max_platforms || 0)
)
const creditsDiff = computed(() =>
  (selectedTierData.value?.ai_credits_monthly || 0) - (currentTierData.value?.ai_credits_monthly || 0)
)

// Prorata calculation
const daysRemainingInMonth = computed(() => {
  const today = new Date()
  const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0)
  return lastDay.getDate() - today.getDate() + 1
})

const dayOfMonth = computed(() => new Date().getDate())

const prorataCredit = computed(() => {
  const currentPrice = tierPrices.value[currentTier.value] || 0
  const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate()
  return (currentPrice / daysInMonth) * daysRemainingInMonth.value
})

const prorataCost = computed(() => {
  const newPrice = tierPrices.value[selectedTier.value] || 0
  const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate()
  return (newPrice / daysInMonth) * daysRemainingInMonth.value
})

const prorataTotal = computed(() => {
  return Math.max(0, prorataCost.value - prorataCredit.value)
})

// Methods
const getTierPrice = (tier: string): number => {
  return tierPrices.value[tier.toLowerCase()] || 0
}

const loadData = async () => {
  try {
    // Load subscription info and available tiers in parallel
    const [subscriptionInfo, tiers] = await Promise.all([
      getSubscriptionInfo(),
      getAvailableTiers()
    ])

    // Set current tier
    currentTier.value = subscriptionInfo.current_tier

    // Set all tiers
    allTiers.value = tiers

    // Build price map
    const priceMap: Record<string, number> = {}
    tiers.forEach(tier => {
      priceMap[tier.tier] = tier.price
    })
    tierPrices.value = priceMap
  } catch (err) {
    console.error('Error loading subscription data:', err)
    // Redirect back if there's an error
    router.push('/dashboard/subscription')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/dashboard/subscription')
}

const changeTier = (tier: string) => {
  router.push(`/dashboard/subscription/upgrade/${tier}`)
}

const proceedToPayment = () => {
  router.push({
    path: '/dashboard/subscription/payment',
    query: {
      type: 'upgrade',
      tier: selectedTier.value,
      price: prorataTotal.value.toFixed(2),
      description: `Abonnement ${selectedTier.value.toUpperCase()}`
    }
  })
}

// Load data and validate on mount
onMounted(async () => {
  await loadData()

  // Validate that selected tier exists
  if (!selectedTierData.value) {
    router.push('/dashboard/subscription')
  }
})
</script>

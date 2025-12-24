<template>
  <div class="p-8 max-w-6xl mx-auto">
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
      <h1 class="text-3xl font-bold text-secondary-900 mb-2">Achat de crédits IA</h1>
      <p class="text-gray-600">Confirmez votre pack de crédits avant de procéder au paiement</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main Content -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Pack sélectionné -->
        <Card class="shadow-md modern-rounded">
          <template #title>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <i class="pi pi-sparkles text-primary-400 text-2xl"/>
                <span class="text-xl font-bold text-secondary-900">Pack sélectionné</span>
              </div>
              <Tag v-if="selectedPack?.popular" value="POPULAIRE" severity="success" class="text-xs font-bold" />
            </div>
          </template>
          <template #content>
            <div class="bg-primary-50 border-2 border-primary-400 rounded-lg p-6">
              <div class="text-center mb-4">
                <div class="text-4xl font-bold text-secondary-900 mb-2">{{ selectedPack?.credits }} crédits</div>
                <div class="text-2xl font-bold text-primary-400">{{ selectedPack?.price }}€</div>
                <div class="text-sm text-gray-600 mt-1">{{ selectedPack?.pricePerCredit }}€ par crédit</div>
              </div>

              <!-- État actuel -->
              <div class="bg-white rounded-lg p-4 mb-4">
                <h4 class="font-semibold text-secondary-900 mb-3">Vos crédits</h4>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-gray-600">Crédits actuels :</span>
                  <span class="font-bold text-secondary-900">{{ currentCredits }}</span>
                </div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-gray-600">Crédits du pack :</span>
                  <span class="font-bold text-primary-400">+{{ selectedPack?.credits }}</span>
                </div>
                <Divider />
                <div class="flex items-center justify-between">
                  <span class="font-semibold text-gray-700">Total après achat :</span>
                  <span class="font-bold text-lg text-secondary-900">{{ totalCreditsAfterPurchase }}</span>
                </div>
              </div>

              <!-- Exemples d'utilisation -->
              <div class="bg-white rounded-lg p-4">
                <h4 class="font-semibold text-secondary-900 mb-3 flex items-center gap-2">
                  <i class="pi pi-lightbulb text-primary-400"/>
                  Ce que vous pouvez faire avec {{ selectedPack?.credits }} crédits
                </h4>
                <div class="space-y-2">
                  <div class="flex items-center gap-2 text-sm text-gray-700">
                    <i class="pi pi-check-circle text-green-600"/>
                    <span><strong>~{{ Math.floor((selectedPack?.credits || 0) / 5) }}</strong> descriptions complètes de produits</span>
                  </div>
                  <div class="flex items-center gap-2 text-sm text-gray-700">
                    <i class="pi pi-check-circle text-green-600"/>
                    <span><strong>~{{ Math.floor((selectedPack?.credits || 0) / 2) }}</strong> optimisations de titres</span>
                  </div>
                  <div class="flex items-center gap-2 text-sm text-gray-700">
                    <i class="pi pi-check-circle text-green-600"/>
                    <span><strong>~{{ Math.floor((selectedPack?.credits || 0) / 3) }}</strong> traductions multilingues</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </Card>

        <!-- Autres packs disponibles -->
        <Card class="shadow-md modern-rounded">
          <template #title>
            <div class="flex items-center gap-3">
              <i class="pi pi-th-large text-primary-400 text-xl"/>
              <span class="text-xl font-bold text-secondary-900">Autres packs disponibles</span>
            </div>
          </template>
          <template #content>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                v-for="pack in otherPacks"
                :key="pack.credits"
                class="p-4 rounded-lg border-2 transition-all duration-200 cursor-pointer"
                :class="pack.popular ? 'border-green-400 bg-green-50' : 'border-gray-200 hover:border-primary-400'"
                @click="changePack(pack)"
              >
                <div class="flex items-center justify-between mb-2">
                  <div class="font-bold text-secondary-900">{{ pack.credits }} crédits</div>
                  <Tag v-if="pack.popular" value="POPULAIRE" severity="success" class="text-xs" />
                </div>
                <div class="text-lg font-bold text-primary-400 mb-1">{{ pack.price }}€</div>
                <div class="text-xs text-gray-600">{{ pack.pricePerCredit }}€ / crédit</div>
                <Button
                  label="Choisir ce pack"
                  class="w-full mt-3 bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
                  size="small"
                  @click="changePack(pack)"
                />
              </div>
            </div>
          </template>
        </Card>

        <!-- FAQ et conditions -->
        <Card class="shadow-md modern-rounded">
          <template #title>
            <div class="flex items-center gap-3">
              <i class="pi pi-info-circle text-primary-400 text-xl"/>
              <span class="text-xl font-bold text-secondary-900">Informations importantes</span>
            </div>
          </template>
          <template #content>
            <Accordion :multiple="true">
              <AccordionTab header="💳 Politique de remboursement">
                <p class="text-gray-700">
                  Les crédits IA sont remboursables sous 14 jours si aucun crédit n'a été utilisé.
                  Une fois que vous commencez à utiliser vos crédits, le remboursement n'est plus possible.
                </p>
              </AccordionTab>
              <AccordionTab header="⏰ Expiration des crédits">
                <p class="text-gray-700">
                  <strong class="text-green-600">Bonne nouvelle !</strong> Vos crédits achetés n'expirent jamais.
                  Ils s'ajoutent à vos crédits mensuels et restent disponibles jusqu'à ce que vous les utilisiez.
                </p>
              </AccordionTab>
              <AccordionTab header="🔄 Cumul avec l'abonnement">
                <p class="text-gray-700">
                  Les crédits achetés s'ajoutent à vos crédits mensuels inclus dans votre abonnement.
                  Si vous changez d'abonnement, vos crédits achetés restent disponibles.
                </p>
              </AccordionTab>
              <AccordionTab header="📊 Suivi de l'utilisation">
                <p class="text-gray-700">
                  Vous pouvez suivre votre consommation de crédits en temps réel sur votre tableau de bord.
                  Un historique détaillé est disponible dans vos paramètres.
                </p>
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
              <!-- Pack info -->
              <div class="p-4 bg-primary-50 rounded-lg text-center">
                <div class="text-3xl font-bold text-secondary-900 mb-1">{{ selectedPack?.credits }}</div>
                <div class="text-sm text-gray-600 mb-3">crédits IA</div>
                <div class="text-2xl font-bold text-primary-400">{{ selectedPack?.price }}€</div>
              </div>

              <Divider />

              <!-- Économies -->
              <div v-if="savingsComparedToSmallest > 0" class="p-3 bg-green-50 border border-green-200 rounded-lg">
                <div class="flex items-center gap-2 text-green-700 mb-1">
                  <i class="pi pi-check-circle"/>
                  <span class="font-semibold text-sm">Vous économisez</span>
                </div>
                <div class="text-2xl font-bold text-green-600">{{ savingsComparedToSmallest.toFixed(2) }}€</div>
                <div class="text-xs text-green-600">par rapport au pack de base</div>
              </div>

              <!-- Avantages -->
              <div class="space-y-2">
                <div class="flex items-center gap-2 text-sm text-gray-700">
                  <i class="pi pi-check-circle text-green-600"/>
                  <span>Activation immédiate</span>
                </div>
                <div class="flex items-center gap-2 text-sm text-gray-700">
                  <i class="pi pi-check-circle text-green-600"/>
                  <span>Pas d'expiration</span>
                </div>
                <div class="flex items-center gap-2 text-sm text-gray-700">
                  <i class="pi pi-check-circle text-green-600"/>
                  <span>Cumulable avec abonnement</span>
                </div>
                <div class="flex items-center gap-2 text-sm text-gray-700">
                  <i class="pi pi-check-circle text-green-600"/>
                  <span>Remboursable sous 14 jours</span>
                </div>
              </div>

              <Divider />

              <!-- CTA Buttons -->
              <div class="space-y-3">
                <Button
                  label="Procéder au paiement"
                  icon="pi pi-arrow-right"
                  icon-pos="right"
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
                <i class="pi pi-lock"/>
                <span>Paiement 100% sécurisé</span>
              </div>
            </div>
          </template>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()
const route = useRoute()

// Current credits from user (mock data)
const currentCredits = ref(750)

// All available packs
const allPacks = ref([
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

// Get selected pack from route params
const selectedCredits = computed(() => parseInt(route.params.credits as string))
const selectedPack = computed(() => {
  return allPacks.value.find(pack => pack.credits === selectedCredits.value)
})

// Other packs (excluding selected)
const otherPacks = computed(() => {
  return allPacks.value.filter(pack => pack.credits !== selectedCredits.value)
})

// Total credits after purchase
const totalCreditsAfterPurchase = computed(() => {
  return currentCredits.value + (selectedPack.value?.credits || 0)
})

// Savings calculation
const savingsComparedToSmallest = computed(() => {
  if (!selectedPack.value) return 0
  const smallestPack = allPacks.value[0]
  if (!smallestPack) return 0
  const smallestPackCost = smallestPack.price
  const costForSameCredits = (selectedPack.value.credits / smallestPack.credits) * smallestPackCost
  return costForSameCredits - selectedPack.value.price
})

// Methods
const goBack = () => {
  router.push('/dashboard/subscription')
}

const changePack = (pack: any) => {
  router.push(`/dashboard/subscription/credits/${pack.credits}`)
}

const proceedToPayment = () => {
  if (!selectedPack.value) return

  router.push({
    path: '/dashboard/subscription/payment',
    query: {
      type: 'credits',
      credits: selectedPack.value.credits,
      price: selectedPack.value.price,
      description: `Pack de ${selectedPack.value.credits} crédits IA`
    }
  })
}

// Validation on mount
onMounted(() => {
  if (!selectedPack.value) {
    router.push('/dashboard/subscription')
  }
})
</script>

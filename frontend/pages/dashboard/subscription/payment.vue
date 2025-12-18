<template>
  <div class="p-8 max-w-4xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <Button
        label="Retour"
        icon="pi pi-arrow-left"
        class="mb-4"
        severity="secondary"
        text
        @click="goBack"
      />
      <h1 class="text-3xl font-bold text-secondary-900 mb-2">Paiement sécurisé</h1>
      <p class="text-gray-600">Complétez votre commande</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Payment Form -->
      <div class="lg:col-span-2">
        <Card class="shadow-md modern-rounded">
          <template #title>
            <div class="flex items-center gap-3">
              <i class="pi pi-credit-card text-primary-400 text-xl"/>
              <span class="text-xl font-bold text-secondary-900">Informations de paiement</span>
            </div>
          </template>
          <template #content>
            <form class="space-y-6" @submit.prevent="handlePayment">
              <!-- Card Number -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Numéro de carte
                </label>
                <InputText
                  v-model="cardNumber"
                  placeholder="1234 5678 9012 3456"
                  class="w-full"
                  maxlength="19"
                  required
                  @input="formatCardNumber"
                />
              </div>

              <!-- Card Holder -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Titulaire de la carte
                </label>
                <InputText
                  v-model="cardHolder"
                  placeholder="Jean Dupont"
                  class="w-full"
                  required
                />
              </div>

              <!-- Expiry and CVV -->
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Date d'expiration
                  </label>
                  <InputText
                    v-model="expiryDate"
                    placeholder="MM/YY"
                    class="w-full"
                    maxlength="5"
                    required
                    @input="formatExpiryDate"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    CVV
                  </label>
                  <InputText
                    v-model="cvv"
                    placeholder="123"
                    class="w-full"
                    maxlength="3"
                    type="password"
                    required
                  />
                </div>
              </div>

              <!-- Billing Address -->
              <Divider />
              <h3 class="text-lg font-semibold text-secondary-900">Adresse de facturation</h3>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Adresse
                </label>
                <InputText
                  v-model="billingAddress"
                  placeholder="123 Rue de la Paix"
                  class="w-full"
                  required
                />
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Code postal
                  </label>
                  <InputText
                    v-model="zipCode"
                    placeholder="75001"
                    class="w-full"
                    required
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Ville
                  </label>
                  <InputText
                    v-model="city"
                    placeholder="Paris"
                    class="w-full"
                    required
                  />
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Pays
                </label>
                <Select
                  v-model="country"
                  :options="countries"
                  option-label="name"
                  option-value="code"
                  placeholder="Sélectionnez un pays"
                  class="w-full"
                  required
                />
              </div>

              <!-- Terms -->
              <div class="flex items-start gap-3">
                <Checkbox v-model="acceptTerms" :binary="true" input-id="terms" />
                <label for="terms" class="text-sm text-gray-700">
                  J'accepte les <a href="#" class="text-primary-400 hover:underline">conditions générales</a>
                  et la <a href="#" class="text-primary-400 hover:underline">politique de confidentialité</a>
                </label>
              </div>

              <!-- Submit Button -->
              <Button
                type="submit"
                :label="`Payer ${totalPrice}€`"
                class="w-full bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
                size="large"
                :loading="processing"
                :disabled="!acceptTerms"
              />

              <!-- Security Notice -->
              <div class="flex items-center justify-center gap-2 text-sm text-gray-500">
                <i class="pi pi-lock"/>
                <span>Paiement sécurisé - Vos données sont protégées</span>
              </div>
            </form>
          </template>
        </Card>
      </div>

      <!-- Order Summary -->
      <div class="lg:col-span-1">
        <Card class="shadow-md modern-rounded sticky top-8">
          <template #title>
            <span class="text-xl font-bold text-secondary-900">Récapitulatif</span>
          </template>
          <template #content>
            <div class="space-y-4">
              <!-- Item -->
              <div class="p-4 bg-secondary-50 rounded-lg">
                <div class="flex items-start gap-3">
                  <i :class="[itemIcon, 'text-primary-400 text-xl']"/>
                  <div class="flex-1">
                    <h4 class="font-semibold text-secondary-900 mb-1">{{ itemDescription }}</h4>
                    <p class="text-sm text-gray-600">{{ itemDetails }}</p>
                  </div>
                </div>
              </div>

              <!-- Price Breakdown -->
              <Divider />
              <div class="space-y-2">
                <div class="flex justify-between text-gray-700">
                  <span>Sous-total</span>
                  <span class="font-medium">{{ subtotal }}€</span>
                </div>
                <div class="flex justify-between text-gray-700">
                  <span>TVA (20%)</span>
                  <span class="font-medium">{{ taxAmount }}€</span>
                </div>
              </div>
              <Divider />
              <div class="flex justify-between text-lg font-bold text-secondary-900">
                <span>Total</span>
                <span class="text-primary-400">{{ totalPrice }}€</span>
              </div>

              <!-- Features -->
              <div class="pt-4 space-y-2">
                <div class="flex items-center gap-2 text-sm text-gray-600">
                  <i class="pi pi-check-circle text-green-600"/>
                  <span>Activation immédiate</span>
                </div>
                <div class="flex items-center gap-2 text-sm text-gray-600">
                  <i class="pi pi-check-circle text-green-600"/>
                  <span>Support client 24/7</span>
                </div>
                <div class="flex items-center gap-2 text-sm text-gray-600">
                  <i class="pi pi-check-circle text-green-600"/>
                  <span>Annulation possible</span>
                </div>
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

const { showSuccess, showError, showInfo, showWarn } = useAppToast()
const router = useRouter()
const route = useRoute()

// Form state
const cardNumber = ref('')
const cardHolder = ref('')
const expiryDate = ref('')
const cvv = ref('')
const billingAddress = ref('')
const zipCode = ref('')
const city = ref('')
const country = ref('FR')
const acceptTerms = ref(false)
const processing = ref(false)

// Payment info from query params
const paymentType = computed(() => route.query.type as string)
const tierName = computed(() => route.query.tier as string)
const credits = computed(() => route.query.credits as string)
const itemDescription = computed(() => route.query.description as string)
const basePrice = computed(() => parseFloat(route.query.price as string || '0'))

// Countries
const countries = ref([
  { name: 'France', code: 'FR' },
  { name: 'Belgique', code: 'BE' },
  { name: 'Suisse', code: 'CH' },
  { name: 'Luxembourg', code: 'LU' },
  { name: 'Canada', code: 'CA' }
])

// Computed
const itemIcon = computed(() => {
  return paymentType.value === 'upgrade' ? 'pi pi-star' : 'pi pi-sparkles'
})

const itemDetails = computed(() => {
  if (paymentType.value === 'upgrade') {
    return `Abonnement mensuel - Renouvellement automatique`
  } else {
    return `${credits.value} crédits IA - Pas d'expiration`
  }
})

const subtotal = computed(() => {
  return (basePrice.value / 1.20).toFixed(2)
})

const taxAmount = computed(() => {
  return (basePrice.value - parseFloat(subtotal.value)).toFixed(2)
})

const totalPrice = computed(() => {
  return basePrice.value.toFixed(2)
})

// Methods
const goBack = () => {
  // Retour vers la page de détails appropriée
  if (paymentType.value === 'upgrade' && tierName.value) {
    router.push(`/dashboard/subscription/upgrade/${tierName.value}`)
  } else if (paymentType.value === 'credits' && credits.value) {
    router.push(`/dashboard/subscription/credits/${credits.value}`)
  } else {
    router.push('/dashboard/subscription')
  }
}

const formatCardNumber = (event: any) => {
  const value = event.target.value.replace(/\s/g, '')
  const formattedValue = value.match(/.{1,4}/g)?.join(' ') || value
  cardNumber.value = formattedValue
}

const formatExpiryDate = (event: any) => {
  let value = event.target.value.replace(/\D/g, '')
  if (value.length >= 2) {
    value = value.slice(0, 2) + '/' + value.slice(2, 4)
  }
  expiryDate.value = value
}

const handlePayment = async () => {
  processing.value = true

  try {
    const { redirectToCheckout } = useStripe()

    // Préparer la requête selon le type de paiement
    if (paymentType.value === 'upgrade' && tierName.value) {
      // Rediriger vers Stripe Checkout pour l'upgrade
      await redirectToCheckout({
        payment_type: 'subscription',
        tier: tierName.value
      })
    } else if (paymentType.value === 'credits' && credits.value) {
      // Rediriger vers Stripe Checkout pour l'achat de crédits
      await redirectToCheckout({
        payment_type: 'credits',
        credits: parseInt(credits.value)
      })
    }

    // La redirection vers Stripe se fait automatiquement
    // L'utilisateur reviendra sur la page success ou cancel après le paiement
  } catch (err: any) {
    console.error('Payment error:', err)
    showError('Erreur de paiement', err.data?.detail || err.message || 'Une erreur est survenue lors de la création de la session de paiement', 5000)
    processing.value = false
  }
}

// Validation on mount
onMounted(() => {
  if (!route.query.type || !route.query.price) {
    toast?.add({
      severity: 'warn',
      summary: 'Informations manquantes',
      detail: 'Redirection vers la page d\'abonnement',
      life: 3000
    })
    router.push('/dashboard/subscription')
  }
})
</script>

<template>
  <div>
    <h1 class="sr-only">Créer un compte Stoflow</h1>
    <Card class="w-full max-w-2xl border-2 border-secondary-900 shadow-xl">
      <template #title>
        <div class="flex items-center gap-2 bg-primary-400 -mx-6 -mt-6 px-6 py-4 mb-4">
          <i class="pi pi-user-plus text-secondary-900 text-2xl"/>
          <span class="text-secondary-900 font-bold text-2xl">Créer un compte</span>
        </div>
      </template>
      <template #content>
        <form class="space-y-4" @submit.prevent="handleRegister">
          <!-- Type de compte -->
          <div class="mb-6">
            <label class="block text-sm font-medium mb-3">
              Type de compte *
            </label>
            <div class="flex gap-4">
              <div
                :class="[
                  'flex-1 p-4 border-2 rounded-lg cursor-pointer transition-all',
                  accountType === 'individual'
                    ? 'border-primary-400 bg-primary-50'
                    : 'border-gray-300 hover:border-primary-400'
                ]"
                @click="accountType = 'individual'"
              >
                <div class="flex items-center gap-2 mb-2">
                  <i class="pi pi-user text-2xl" :class="accountType === 'individual' ? 'text-primary-600' : 'text-gray-400'"/>
                  <span class="font-bold">Particulier</span>
                </div>
                <p class="text-sm text-gray-600">Pour usage personnel</p>
              </div>
              <div
                :class="[
                  'flex-1 p-4 border-2 rounded-lg cursor-pointer transition-all',
                  accountType === 'professional'
                    ? 'border-primary-400 bg-primary-50'
                    : 'border-gray-300 hover:border-primary-400'
                ]"
                @click="accountType = 'professional'"
              >
                <div class="flex items-center gap-2 mb-2">
                  <i class="pi pi-briefcase text-2xl" :class="accountType === 'professional' ? 'text-primary-600' : 'text-gray-400'"/>
                  <span class="font-bold">Professionnel</span>
                </div>
                <p class="text-sm text-gray-600">Pour votre entreprise</p>
              </div>
            </div>
          </div>

          <!-- Informations de base -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="fullName" class="block text-sm font-medium mb-2">
                Votre nom complet *
              </label>
              <InputText
                id="fullName"
                v-model="fullName"
                placeholder="John Doe"
                class="w-full"
                required
                :disabled="authStore.isLoading"
              />
            </div>

            <div>
              <label for="businessName" class="block text-sm font-medium mb-2">
                Nom de votre boutique{{ accountType === 'professional' ? ' *' : '' }}
              </label>
              <InputText
                id="businessName"
                v-model="businessName"
                placeholder="Ma Super Boutique"
                class="w-full"
                :required="accountType === 'professional'"
                :disabled="authStore.isLoading"
              />
            </div>
          </div>

          <!-- Email et mot de passe -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="email" class="block text-sm font-medium mb-2">
                Email *
              </label>
              <InputText
                id="email"
                v-model="email"
                type="email"
                placeholder="votre@email.com"
                class="w-full"
                required
                :disabled="authStore.isLoading"
              />
            </div>

            <div>
              <label for="phone" class="block text-sm font-medium mb-2">
                Téléphone
              </label>
              <InputText
                id="phone"
                v-model="phone"
                placeholder="+33 6 12 34 56 78"
                class="w-full"
                :disabled="authStore.isLoading"
              />
            </div>
          </div>

          <div>
            <label for="password" class="block text-sm font-medium mb-2">
              Mot de passe *
            </label>
            <Password
              id="password"
              v-model="password"
              placeholder="••••••••"
              :class="['w-full', { 'p-invalid': passwordTouched && !isPasswordValid }]"
              toggle-mask
              :feedback="false"
              required
              :disabled="authStore.isLoading"
              @blur="passwordTouched = true"
            />
            <!-- Password requirements checklist -->
            <div v-if="password.length > 0 || passwordTouched" class="mt-2 space-y-1">
              <p
                :class="['text-xs flex items-center gap-1', passwordRules.minLength ? 'text-green-600' : 'text-red-500']"
              >
                <i :class="['pi', passwordRules.minLength ? 'pi-check' : 'pi-times']" />
                Minimum 12 caractères
              </p>
              <p
                :class="['text-xs flex items-center gap-1', passwordRules.hasUppercase ? 'text-green-600' : 'text-red-500']"
              >
                <i :class="['pi', passwordRules.hasUppercase ? 'pi-check' : 'pi-times']" />
                1 majuscule (A-Z)
              </p>
              <p
                :class="['text-xs flex items-center gap-1', passwordRules.hasLowercase ? 'text-green-600' : 'text-red-500']"
              >
                <i :class="['pi', passwordRules.hasLowercase ? 'pi-check' : 'pi-times']" />
                1 minuscule (a-z)
              </p>
              <p
                :class="['text-xs flex items-center gap-1', passwordRules.hasDigit ? 'text-green-600' : 'text-red-500']"
              >
                <i :class="['pi', passwordRules.hasDigit ? 'pi-check' : 'pi-times']" />
                1 chiffre (0-9)
              </p>
              <p
                :class="['text-xs flex items-center gap-1', passwordRules.hasSpecial ? 'text-green-600' : 'text-red-500']"
              >
                <i :class="['pi', passwordRules.hasSpecial ? 'pi-check' : 'pi-times']" />
                1 caractère spécial (!@#$%^&*)
              </p>
            </div>
          </div>

          <!-- Informations professionnelles (conditionnelles) -->
          <div v-if="accountType === 'professional'" class="space-y-4 p-4 bg-gray-50 rounded-lg border">
            <h3 class="font-bold text-secondary-900 mb-3">
              <i class="pi pi-briefcase mr-2"/>
              Informations professionnelles
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label for="siret" class="block text-sm font-medium mb-2">
                  SIRET
                </label>
                <InputText
                  id="siret"
                  v-model="siret"
                  placeholder="12345678901234"
                  class="w-full"
                  :disabled="authStore.isLoading"
                  maxlength="14"
                />
                <small class="text-xs text-gray-500">14 chiffres (France uniquement)</small>
              </div>

              <div>
                <label for="vatNumber" class="block text-sm font-medium mb-2">
                  Numéro de TVA
                </label>
                <InputText
                  id="vatNumber"
                  v-model="vatNumber"
                  placeholder="FR12345678901"
                  class="w-full"
                  :disabled="authStore.isLoading"
                />
                <small class="text-xs text-gray-500">TVA intracommunautaire</small>
              </div>
            </div>
          </div>

          <!-- Type d'activité -->
          <div>
            <label for="businessType" class="block text-sm font-medium mb-2">
              Type d'activité *
            </label>
            <Select
              id="businessType"
              v-model="businessType"
              :options="businessTypeOptions"
              option-label="label"
              option-value="value"
              placeholder="Sélectionnez votre activité"
              class="w-full"
              required
              :disabled="authStore.isLoading"
            />
          </div>

          <!-- Nombre de produits estimé -->
          <div>
            <label for="estimatedProducts" class="block text-sm font-medium mb-2">
              Nombre de produits estimé *
            </label>
            <Select
              id="estimatedProducts"
              v-model="estimatedProducts"
              :options="estimatedProductsOptions"
              option-label="label"
              option-value="value"
              placeholder="Combien de produits gérez-vous ?"
              class="w-full"
              required
              :disabled="authStore.isLoading"
            />
          </div>

          <div v-if="authStore.error" class="p-3 bg-secondary-50 border border-primary-200 rounded-lg">
            <p class="text-secondary-600 text-sm">
              <i class="pi pi-exclamation-triangle mr-2"/>
              {{ authStore.error }}
            </p>
          </div>

          <Button
            type="submit"
            label="Créer mon compte"
            icon="pi pi-user-plus"
            class="w-full bg-secondary-900 hover:bg-secondary-800 border-0 font-bold"
            :loading="authStore.isLoading"
          />
        </form>
      </template>
      <template #footer>
        <div class="text-center text-sm text-secondary-900 border-t-2 border-primary-400 pt-4">
          Déjà un compte ?
          <NuxtLink to="/login" class="text-primary-600 hover:text-primary-700 underline font-bold">
            Se connecter
          </NuxtLink>
        </div>
      </template>
  </Card>
  </div>
</template>

<script setup lang="ts">
import type { RegisterData } from '~/stores/auth'

definePageMeta({
  layout: 'auth'
})

// SEO Meta Tags
useSeoHead({
  title: 'Inscription',
  description: 'Créez votre compte Stoflow gratuitement et commencez à gérer vos ventes sur Vinted, eBay et Etsy. Essai gratuit 14 jours.',
  noindex: true // Page privée, pas besoin d'indexation
})

const authStore = useAuthStore()
const router = useRouter()
const { showSuccess, showError } = useAppToast()

// Type de compte
const accountType = ref<'individual' | 'professional'>('individual')

// Champs de base
const fullName = ref('')
const businessName = ref('')
const email = ref('')
const password = ref('')
const phone = ref('')

// Champs professionnels
const siret = ref('')
const vatNumber = ref('')

// Type d'activité
const businessType = ref('')
const businessTypeOptions = [
  { label: 'Revente', value: 'resale' },
  { label: 'Dropshipping', value: 'dropshipping' },
  { label: 'Artisanat', value: 'artisan' },
  { label: 'Commerce de détail', value: 'retail' },
  { label: 'Autre', value: 'other' }
]

// Nombre de produits
const estimatedProducts = ref('')
const estimatedProductsOptions = [
  { label: '0-50 produits', value: '0-50' },
  { label: '50-200 produits', value: '50-200' },
  { label: '200-500 produits', value: '200-500' },
  { label: '500+ produits', value: '500+' }
]

// Password validation rules (same as backend)
const passwordRules = computed(() => ({
  minLength: password.value.length >= 12,
  hasUppercase: /[A-Z]/.test(password.value),
  hasLowercase: /[a-z]/.test(password.value),
  hasDigit: /[0-9]/.test(password.value),
  hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password.value)
}))

const isPasswordValid = computed(() => {
  const rules = passwordRules.value
  return rules.minLength && rules.hasUppercase && rules.hasLowercase && rules.hasDigit && rules.hasSpecial
})

const passwordTouched = ref(false)

const handleRegister = async () => {
  // Validate password before submitting
  passwordTouched.value = true
  if (!isPasswordValid.value) {
    authStore.error = 'Le mot de passe ne respecte pas les critères de sécurité'
    return
  }

  try {
    // Préparer les données d'inscription
    const registerData: RegisterData = {
      email: email.value,
      password: password.value,
      full_name: fullName.value,
      business_name: businessName.value || undefined,
      account_type: accountType.value,
      business_type: businessType.value as any || undefined,
      estimated_products: estimatedProducts.value as any || undefined,
      phone: phone.value || undefined,
      country: 'FR',
      language: 'fr'
    }

    // Ajouter les champs professionnels si le type est 'professional'
    if (accountType.value === 'professional') {
      registerData.siret = siret.value || undefined
      registerData.vat_number = vatNumber.value || undefined
    }

    const result = await authStore.register(registerData)

    // Rediriger vers la page de vérification d'email
    if (result.requiresVerification) {
      showSuccess('Compte créé', 'Vérifiez votre boîte email pour activer votre compte')
      router.push(`/auth/check-email?email=${encodeURIComponent(result.email)}`)
    }
  } catch (error: any) {
    showError('Erreur', error.message || 'Impossible de créer le compte')
  }
}

</script>

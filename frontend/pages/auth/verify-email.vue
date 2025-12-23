<template>
  <div class="min-h-screen flex items-center justify-center bg-white">
    <Card class="w-full max-w-md border-2 border-secondary-900 shadow-xl">
      <template #title>
        <div class="flex items-center gap-2 bg-primary-400 -mx-6 -mt-6 px-6 py-4 mb-4">
          <i :class="headerIcon" class="text-secondary-900 text-2xl"/>
          <span class="text-secondary-900 font-bold text-2xl">{{ headerTitle }}</span>
        </div>
      </template>
      <template #content>
        <!-- Loading state -->
        <div v-if="isLoading" class="text-center py-8">
          <i class="pi pi-spin pi-spinner text-4xl text-primary-600 mb-4"/>
          <p class="text-secondary-600">Vérification en cours...</p>
        </div>

        <!-- Success state -->
        <div v-else-if="isSuccess" class="text-center py-8">
          <i class="pi pi-check-circle text-5xl text-green-600 mb-4"/>
          <h3 class="text-xl font-semibold text-secondary-900 mb-2">
            Email vérifié !
          </h3>
          <p class="text-secondary-600 mb-6">
            Votre adresse email <strong>{{ verifiedEmail }}</strong> a été confirmée avec succès.
          </p>
          <Button
            label="Se connecter"
            icon="pi pi-sign-in"
            class="bg-secondary-900 hover:bg-secondary-800 border-0 font-bold"
            @click="goToLogin"
          />
        </div>

        <!-- Error state -->
        <div v-else-if="isError" class="text-center py-8">
          <i class="pi pi-times-circle text-5xl text-red-600 mb-4"/>
          <h3 class="text-xl font-semibold text-secondary-900 mb-2">
            Vérification échouée
          </h3>
          <p class="text-secondary-600 mb-6">
            {{ errorMessage }}
          </p>
          <div class="flex flex-col gap-3">
            <Button
              label="Renvoyer un email"
              icon="pi pi-envelope"
              class="bg-primary-600 hover:bg-primary-700 border-0 font-bold"
              @click="showResendForm = true"
              :disabled="showResendForm"
            />
            <Button
              label="Retour à la connexion"
              icon="pi pi-arrow-left"
              severity="secondary"
              outlined
              @click="goToLogin"
            />
          </div>
        </div>

        <!-- Resend form -->
        <div v-if="showResendForm && isError" class="mt-6 pt-6 border-t border-secondary-200">
          <h4 class="font-semibold text-secondary-900 mb-3">Renvoyer l'email de vérification</h4>
          <form @submit.prevent="resendVerification" class="space-y-4">
            <div>
              <label for="resend-email" class="block text-sm font-medium mb-2">
                Votre adresse email
              </label>
              <InputText
                id="resend-email"
                v-model="resendEmail"
                type="email"
                placeholder="votre@email.com"
                class="w-full"
                required
                :disabled="isResending"
              />
            </div>
            <Button
              type="submit"
              label="Envoyer"
              icon="pi pi-send"
              class="w-full bg-secondary-900 hover:bg-secondary-800 border-0 font-bold"
              :loading="isResending"
            />
          </form>
          <p v-if="resendSuccess" class="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            <i class="pi pi-check mr-2"/>
            Si cet email existe, un nouveau lien de vérification a été envoyé.
          </p>
        </div>

        <!-- No token state -->
        <div v-if="!token && !isLoading" class="text-center py-8">
          <i class="pi pi-exclamation-triangle text-5xl text-yellow-600 mb-4"/>
          <h3 class="text-xl font-semibold text-secondary-900 mb-2">
            Lien invalide
          </h3>
          <p class="text-secondary-600 mb-6">
            Ce lien de vérification est incomplet ou invalide.
          </p>
          <Button
            label="Retour à la connexion"
            icon="pi pi-arrow-left"
            class="bg-secondary-900 hover:bg-secondary-800 border-0 font-bold"
            @click="goToLogin"
          />
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()
const { showSuccess, showError } = useAppToast()

// State
const token = computed(() => route.query.token as string | undefined)
const isLoading = ref(false)
const isSuccess = ref(false)
const isError = ref(false)
const errorMessage = ref('')
const verifiedEmail = ref('')

// Resend form
const showResendForm = ref(false)
const resendEmail = ref('')
const isResending = ref(false)
const resendSuccess = ref(false)

// Computed
const headerTitle = computed(() => {
  if (isLoading.value) return 'Vérification...'
  if (isSuccess.value) return 'Email confirmé'
  if (isError.value) return 'Erreur'
  return 'Vérification email'
})

const headerIcon = computed(() => {
  if (isLoading.value) return 'pi pi-spin pi-spinner'
  if (isSuccess.value) return 'pi pi-check-circle'
  if (isError.value) return 'pi pi-times-circle'
  return 'pi pi-envelope'
})

// Methods
const verifyEmail = async () => {
  if (!token.value) return

  isLoading.value = true
  isError.value = false
  isSuccess.value = false

  try {
    const response = await fetch(
      `${config.public.apiUrl}/api/auth/verify-email?token=${encodeURIComponent(token.value)}`,
      { method: 'GET' }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Token invalide ou expiré')
    }

    const data = await response.json()
    verifiedEmail.value = data.email
    isSuccess.value = true
    showSuccess('Email vérifié', 'Votre adresse email a été confirmée avec succès')
  } catch (error: any) {
    isError.value = true
    errorMessage.value = error.message || 'Une erreur est survenue lors de la vérification'
    showError('Erreur', errorMessage.value)
  } finally {
    isLoading.value = false
  }
}

const resendVerification = async () => {
  if (!resendEmail.value) return

  isResending.value = true
  resendSuccess.value = false

  try {
    const response = await fetch(
      `${config.public.apiUrl}/api/auth/resend-verification?email=${encodeURIComponent(resendEmail.value)}`,
      { method: 'POST' }
    )

    // Always show success (backend returns same message to prevent email enumeration)
    resendSuccess.value = true
  } catch (error) {
    // Still show success to prevent email enumeration
    resendSuccess.value = true
  } finally {
    isResending.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}

// Verify on mount if token present
onMounted(() => {
  if (token.value) {
    verifyEmail()
  }
})
</script>

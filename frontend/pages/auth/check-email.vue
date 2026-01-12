<template>
  <Card class="w-full max-w-md border-2 border-secondary-900 shadow-xl">
      <template #title>
        <div class="flex items-center gap-2 bg-primary-400 -mx-6 -mt-6 px-6 py-4 mb-4">
          <i class="pi pi-envelope text-secondary-900 text-2xl"/>
          <span class="text-secondary-900 font-bold text-2xl">Vérifiez votre email</span>
        </div>
      </template>
      <template #content>
        <div class="text-center py-4">
          <i class="pi pi-envelope text-5xl text-primary-600 mb-6"/>

          <h3 class="text-xl font-semibold text-secondary-900 mb-4">
            Inscription réussie !
          </h3>

          <p class="text-secondary-600 mb-2">
            Un email de confirmation a été envoyé à :
          </p>

          <p class="text-lg font-semibold text-secondary-900 mb-6">
            {{ email }}
          </p>

          <p class="text-secondary-600 mb-6">
            Cliquez sur le lien dans l'email pour activer votre compte et pouvoir vous connecter.
          </p>

          <div class="alert alert-warning mb-6">
            <i class="pi pi-info-circle"/>
            <p class="text-sm">
              Pensez à vérifier vos <strong>spams</strong> si vous ne trouvez pas l'email.
            </p>
          </div>

          <!-- Resend section -->
          <div class="border-t border-secondary-200 pt-6">
            <p class="text-secondary-600 text-sm mb-4">
              Vous n'avez pas reçu l'email ?
            </p>

            <Button
              label="Renvoyer l'email"
              icon="pi pi-refresh"
              class="bg-secondary-900 hover:bg-secondary-800 border-0 font-bold"
              :loading="isResending"
              :disabled="resendCooldown > 0"
              @click="resendEmail"
            />

            <p v-if="resendCooldown > 0" class="text-secondary-500 text-sm mt-2">
              Réessayer dans {{ resendCooldown }}s
            </p>

            <p v-if="resendSuccess" class="text-success-600 text-sm mt-2">
              <i class="pi pi-check mr-1"/>
              Email renvoyé !
            </p>
          </div>
        </div>
      </template>
      <template #footer>
        <div class="text-center text-sm text-secondary-900 border-t-2 border-primary-400 pt-4">
          <NuxtLink to="/login" class="text-primary-600 hover:text-primary-700 underline font-bold">
            Retour à la connexion
          </NuxtLink>
        </div>
      </template>
  </Card>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'auth'
})
const route = useRoute()
const config = useRuntimeConfig()

// Get email from query params
const email = computed(() => route.query.email as string || '')

// Resend state
const isResending = ref(false)
const resendSuccess = ref(false)
const resendCooldown = ref(0)

let cooldownInterval: NodeJS.Timeout | null = null

const resendEmail = async () => {
  if (!email.value || resendCooldown.value > 0) return

  isResending.value = true
  resendSuccess.value = false

  try {
    await fetch(
      `${config.public.apiBaseUrl}/auth/resend-verification?email=${encodeURIComponent(email.value)}`,
      { method: 'POST' }
    )

    resendSuccess.value = true

    // Start cooldown (60 seconds)
    resendCooldown.value = 60
    cooldownInterval = setInterval(() => {
      resendCooldown.value--
      if (resendCooldown.value <= 0 && cooldownInterval) {
        clearInterval(cooldownInterval)
        cooldownInterval = null
      }
    }, 1000)
  } catch (error) {
    // Still show success to prevent email enumeration
    resendSuccess.value = true
  } finally {
    isResending.value = false
  }
}

// Cleanup on unmount
onUnmounted(() => {
  if (cooldownInterval) {
    clearInterval(cooldownInterval)
  }
})
</script>

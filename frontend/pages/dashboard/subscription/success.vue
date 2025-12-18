<template>
  <div class="flex items-center justify-center min-h-[80vh] p-8">
    <Card class="max-w-2xl w-full shadow-lg modern-rounded">
      <template #content>
        <div class="text-center space-y-6 py-8">
          <!-- Success Icon -->
          <div class="flex justify-center">
            <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
              <i class="pi pi-check text-green-600 text-4xl"></i>
            </div>
          </div>

          <!-- Title -->
          <div>
            <h1 class="text-3xl font-bold text-secondary-900 mb-2">
              Paiement réussi !
            </h1>
            <p class="text-gray-600">
              Votre transaction a été effectuée avec succès
            </p>
          </div>

          <!-- Loading state -->
          <div v-if="loading" class="space-y-4">
            <ProgressSpinner style="width: 50px; height: 50px" />
            <p class="text-gray-600">Mise à jour de votre compte...</p>
          </div>

          <!-- Success details -->
          <div v-else class="space-y-4">
            <div class="p-6 bg-green-50 rounded-lg">
              <div class="space-y-2">
                <div class="flex items-center justify-center gap-2 text-green-700">
                  <i class="pi pi-check-circle"></i>
                  <span class="font-semibold">Paiement confirmé</span>
                </div>
                <p class="text-sm text-gray-600">
                  Votre abonnement ou vos crédits ont été activés immédiatement
                </p>
              </div>
            </div>

            <!-- Action buttons -->
            <div class="flex flex-col sm:flex-row gap-4 justify-center pt-4">
              <Button
                label="Retour à l'abonnement"
                icon="pi pi-arrow-left"
                class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
                @click="router.push('/dashboard/subscription')"
              />
              <Button
                label="Aller au tableau de bord"
                icon="pi pi-home"
                severity="secondary"
                outlined
                @click="router.push('/dashboard')"
              />
            </div>
          </div>

          <!-- Additional info -->
          <div class="pt-6 border-t">
            <div class="space-y-2 text-sm text-gray-600">
              <div class="flex items-center justify-center gap-2">
                <i class="pi pi-envelope"></i>
                <span>Un reçu a été envoyé à votre adresse email</span>
              </div>
              <div class="flex items-center justify-center gap-2">
                <i class="pi pi-shield"></i>
                <span>Transaction sécurisée par Stripe</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">

definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()
const route = useRoute()
const { showSuccess, showError, showInfo, showWarn } = useAppToast()
const loading = ref(true)

// Récupérer le session_id depuis l'URL
const sessionId = computed(() => route.query.session_id as string)

onMounted(async () => {
  // Vérifier que le session_id est présent
  if (!sessionId.value) {
    toast?.add({
      severity: 'warn',
      summary: 'Session invalide',
      detail: 'Aucune session de paiement trouvée',
      life: 3000
    })
    router.push('/dashboard/subscription')
    return
  }

  // Attendre un peu pour que le webhook Stripe soit traité
  // En production, vous pourriez vérifier l'état via une API
  setTimeout(() => {
    loading.value = false
    showSuccess('Succès', 'Votre paiement a été traité avec succès', 5000)
  }, 2000)
})
</script>

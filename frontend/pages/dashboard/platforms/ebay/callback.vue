<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <Card class="w-full max-w-md shadow-lg">
      <template #content>
        <div class="text-center py-8">
          <!-- Loading -->
          <div v-if="isProcessing" class="space-y-4">
            <LoadingAnimation type="stoflow" size="large" variant="primary" />
            <h2 class="text-xl font-bold text-secondary-900">Connexion en cours...</h2>
            <p class="text-gray-600">Veuillez patienter pendant que nous configurons votre compte eBay</p>
          </div>

          <!-- Success -->
          <div v-else-if="isSuccess" class="space-y-4">
            <div class="w-20 h-20 mx-auto rounded-full bg-green-100 flex items-center justify-center">
              <i class="pi pi-check text-green-600 text-4xl"></i>
            </div>
            <h2 class="text-xl font-bold text-secondary-900">Connexion réussie !</h2>
            <p class="text-gray-600">Votre compte eBay a été connecté avec succès</p>
            <p class="text-sm text-gray-500">Cette fenêtre va se fermer automatiquement...</p>
          </div>

          <!-- Error -->
          <div v-else-if="error" class="space-y-4">
            <div class="w-20 h-20 mx-auto rounded-full bg-red-100 flex items-center justify-center">
              <i class="pi pi-times text-red-600 text-4xl"></i>
            </div>
            <h2 class="text-xl font-bold text-secondary-900">Erreur de connexion</h2>
            <p class="text-red-600">{{ error }}</p>
            <Button
              label="Réessayer"
              icon="pi pi-refresh"
              class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
              @click="retry"
            />
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

const route = useRoute()
const ebayStore = useEbayStore()

const isProcessing = ref(true)
const isSuccess = ref(false)
const error = ref<string | null>(null)

const processCallback = async () => {
  const code = route.query.code as string
  const errorParam = route.query.error as string

  if (errorParam) {
    error.value = route.query.error_description as string || 'Connexion refusée par l\'utilisateur'
    isProcessing.value = false
    return
  }

  if (!code) {
    error.value = 'Code d\'autorisation manquant'
    isProcessing.value = false
    return
  }

  try {
    await ebayStore.exchangeCodeForTokens(code)
    isSuccess.value = true

    // Fermer la fenêtre après 2 secondes
    setTimeout(() => {
      window.close()
    }, 2000)

  } catch (err: any) {
    error.value = err.message || 'Erreur lors de la connexion'
  } finally {
    isProcessing.value = false
  }
}

const retry = () => {
  window.close()
}

onMounted(() => {
  processCallback()
})
</script>

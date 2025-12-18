<template>
  <div class="flex items-center justify-center min-h-[80vh] p-8">
    <Card class="max-w-2xl w-full shadow-lg modern-rounded">
      <template #content>
        <div class="text-center space-y-6 py-8">
          <!-- Cancel Icon -->
          <div class="flex justify-center">
            <div class="w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center">
              <i class="pi pi-times text-orange-600 text-4xl"></i>
            </div>
          </div>

          <!-- Title -->
          <div>
            <h1 class="text-3xl font-bold text-secondary-900 mb-2">
              Paiement annulé
            </h1>
            <p class="text-gray-600">
              Vous avez annulé la transaction
            </p>
          </div>

          <!-- Info message -->
          <div class="p-6 bg-orange-50 rounded-lg">
            <div class="space-y-2">
              <div class="flex items-center justify-center gap-2 text-orange-700">
                <i class="pi pi-info-circle"></i>
                <span class="font-semibold">Aucun montant n'a été débité</span>
              </div>
              <p class="text-sm text-gray-600">
                Votre paiement a été annulé et aucune charge n'a été effectuée sur votre compte
              </p>
            </div>
          </div>

          <!-- Reasons -->
          <div class="text-left max-w-md mx-auto">
            <p class="text-sm font-medium text-gray-700 mb-2">Vous avez annulé car :</p>
            <ul class="space-y-2 text-sm text-gray-600">
              <li class="flex items-start gap-2">
                <i class="pi pi-circle-fill text-xs mt-1"></i>
                <span>Vous souhaitez choisir un autre abonnement ?</span>
              </li>
              <li class="flex items-start gap-2">
                <i class="pi pi-circle-fill text-xs mt-1"></i>
                <span>Vous avez des questions sur les fonctionnalités ?</span>
              </li>
              <li class="flex items-start gap-2">
                <i class="pi pi-circle-fill text-xs mt-1"></i>
                <span>Vous rencontrez un problème technique ?</span>
              </li>
            </ul>
          </div>

          <!-- Action buttons -->
          <div class="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Button
              label="Réessayer"
              icon="pi pi-refresh"
              class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
              @click="goBack"
            />
            <Button
              label="Voir les abonnements"
              icon="pi pi-shopping-cart"
              severity="secondary"
              outlined
              @click="router.push('/dashboard/subscription')"
            />
          </div>

          <!-- Additional help -->
          <div class="pt-6 border-t">
            <div class="space-y-2 text-sm text-gray-600">
              <p class="font-medium text-gray-700">Besoin d'aide ?</p>
              <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
                <a href="#" class="flex items-center gap-2 text-primary-400 hover:underline">
                  <i class="pi pi-envelope"></i>
                  <span>Contactez le support</span>
                </a>
                <a href="#" class="flex items-center gap-2 text-primary-400 hover:underline">
                  <i class="pi pi-question-circle"></i>
                  <span>FAQ</span>
                </a>
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

// Récupérer les infos depuis l'URL si disponibles
const previousType = computed(() => route.query.type as string)
const previousTier = computed(() => route.query.tier as string)
const previousCredits = computed(() => route.query.credits as string)

const goBack = () => {
  // Retourner vers la page appropriée selon le type de paiement
  if (previousType.value === 'upgrade' && previousTier.value) {
    router.push(`/dashboard/subscription/upgrade/${previousTier.value}`)
  } else if (previousType.value === 'credits' && previousCredits.value) {
    router.push(`/dashboard/subscription/credits/${previousCredits.value}`)
  } else {
    router.push('/dashboard/subscription')
  }
}

onMounted(() => {
  showInfo('Paiement annulé', 'Vous pouvez réessayer quand vous voulez', 3000)
})
</script>

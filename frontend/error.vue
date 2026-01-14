<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="text-center px-6">
      <!-- Logo StoFlow -->
      <div class="mb-8">
        <span class="font-display text-2xl font-bold text-secondary-900">Sto</span>
        <span class="font-display text-2xl font-bold text-primary-400">flow</span>
      </div>

      <!-- Error code -->
      <h1 class="error-code mb-4">
        {{ error?.statusCode || 404 }}
      </h1>

      <!-- Error message -->
      <h2 class="error-title mb-4">
        {{ errorTitle }}
      </h2>

      <p class="error-description mb-8">
        {{ errorMessage }}
      </p>

      <!-- Back to dashboard button -->
      <NuxtLink to="/dashboard">
        <Button
          label="Retour au tableau de bord"
          icon="pi pi-home"
          class="btn-primary"
        />
      </NuxtLink>

      <!-- Clear error link -->
      <div class="mt-4">
        <button
          class="text-sm text-gray-500 hover:text-secondary-900 transition-colors"
          @click="handleError"
        >
          Réessayer
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NuxtError } from '#app'

defineProps<{
  error: NuxtError
}>()

const errorTitle = computed(() => {
  const statusCode = error?.statusCode
  switch (statusCode) {
    case 404:
      return 'Page non trouvée'
    case 500:
      return 'Erreur serveur'
    case 403:
      return 'Accès refusé'
    case 401:
      return 'Non autorisé'
    default:
      return 'Une erreur est survenue'
  }
})

const errorMessage = computed(() => {
  const statusCode = error?.statusCode
  switch (statusCode) {
    case 404:
      return 'Désolé, la page que vous recherchez n\'existe pas ou a été déplacée.'
    case 500:
      return 'Une erreur interne s\'est produite. Veuillez réessayer plus tard.'
    case 403:
      return 'Vous n\'avez pas la permission d\'accéder à cette ressource.'
    case 401:
      return 'Veuillez vous connecter pour accéder à cette page.'
    default:
      return 'Quelque chose s\'est mal passé. Veuillez réessayer.'
  }
})

const handleError = () => clearError({ redirect: '/dashboard' })
</script>

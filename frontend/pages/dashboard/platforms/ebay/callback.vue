<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <Card class="w-full max-w-md shadow-lg">
      <template #content>
        <div class="text-center py-8">
          <LoadingAnimation type="stoflow" size="large" variant="primary" />
          <h2 class="text-xl font-bold text-secondary-900">Connexion en cours...</h2>
          <p class="text-gray-600">Vérification de votre connexion eBay</p>
          <p class="text-sm text-gray-500 mt-4">Cette fenêtre va se fermer automatiquement...</p>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

// This page is just a landing page after eBay redirect
// The backend has already processed the callback and sent postMessage
// We just show a loading state and close the popup

onMounted(() => {
  // Close after 2 seconds (backend postMessage should have fired already)
  setTimeout(() => {
    if (import.meta.client) {
      window.close()
    }
  }, 2000)
})
</script>

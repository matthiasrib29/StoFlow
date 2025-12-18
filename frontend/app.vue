<template>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
    <Toast />
    <ConfirmDialog />
  </div>
</template>

<style>
/* ============================================
   PAGE TRANSITIONS CONTEXTUELLES
   Transitions différentes selon la navigation
   ============================================ */

/* 1. Default page transition - fade & slide up */
.page-enter-active,
.page-leave-active {
  transition: all 0.25s ease-out;
}

.page-enter-from {
  opacity: 0;
  transform: scale(0.98);
}

.page-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

/* 2. Fade simple (auth pages) */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease-out;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 3. Slide-up (création/édition - modal-like) */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.25s ease-out;
}

.slide-up-enter-from {
  opacity: 0;
  transform: scale(0.98);
}

.slide-up-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

/* 4. Slide horizontal (navigation entre platforms) */
.slide-horizontal-enter-active,
.slide-horizontal-leave-active {
  transition: all 0.25s ease-out;
}

.slide-horizontal-enter-from {
  opacity: 0;
  transform: scale(0.98);
}

.slide-horizontal-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

/* 5. Slide-left (retour vers dashboard, settings) */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.25s ease-out;
}

.slide-left-enter-from {
  opacity: 0;
  transform: scale(0.98);
}

.slide-left-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

/* 6. Slide-right (dashboard → produits/publications) */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.25s ease-out;
}

.slide-right-enter-from {
  opacity: 0;
  transform: scale(0.98);
}

.slide-right-leave-to {
  opacity: 0;
  transform: scale(0.98);
}
</style>

<script setup lang="ts">
// Nuxt auto-importe useAuthStore depuis stores/
const authStore = useAuthStore()

// Charger la session au démarrage
onMounted(() => {
  authStore.loadFromStorage()
})
</script>

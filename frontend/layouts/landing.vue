<template>
  <div class="min-h-screen bg-white">
    <!-- Skip to content (accessibility) -->
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-500 focus:text-white focus:rounded-lg focus:shadow-lg"
    >
      Aller au contenu principal
    </a>

    <!-- Header Navigation -->
    <LayoutHeaderPublic />

    <!-- Main Content -->
    <main id="main-content" class="pt-16">
      <slot />
    </main>

    <!-- Footer -->
    <LayoutFooterFull />
  </div>
</template>

<script setup lang="ts">
// Redirect if already authenticated
const authStore = useAuthStore()

onMounted(() => {
  if (authStore.isAuthenticated) {
    navigateTo('/dashboard')
  }
})
</script>

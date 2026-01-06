<template>
  <div class="min-h-screen bg-white">
    <!-- Header Navigation -->
    <LayoutHeaderPublic />

    <!-- Main Content -->
    <main class="pt-16">
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

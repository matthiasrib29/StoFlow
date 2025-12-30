<template>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
    <Toast />
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
// Note: loadFromStorage() is called by auth.global.ts middleware
// No need to duplicate here - middleware handles session restoration
</script>

<style>
/* Page transitions disabled globally via nuxt.config.ts */
/* Individual pages can define their own transitions if needed */
</style>

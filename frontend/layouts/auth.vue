<template>
  <div class="min-h-screen bg-gradient-to-br from-white via-gray-50 to-white flex flex-col">
    <!-- Header -->
    <LayoutHeaderAuth />

    <!-- Main Content -->
    <main class="flex-1 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <slot />
    </main>

    <!-- Minimal Footer -->
    <LayoutFooterMinimal />
  </div>
</template>

<script setup lang="ts">
// Note: Auth redirect is handled by the global auth middleware
// No need to duplicate here
</script>

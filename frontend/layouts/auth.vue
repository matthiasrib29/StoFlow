<template>
  <div class="min-h-screen bg-gradient-to-br from-white via-gray-50 to-white flex flex-col">
    <!-- Header -->
    <header class="bg-white/95 backdrop-blur-sm border-b border-gray-100">
      <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <!-- Logo -->
          <NuxtLink to="/" class="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity">
            <div class="w-10 h-10 bg-secondary-900 rounded-lg flex items-center justify-center">
              <span class="text-primary-400 font-bold text-xl">S</span>
            </div>
            <span class="text-2xl font-bold text-secondary-900">Stoflow</span>
          </NuxtLink>

          <!-- Back to home button -->
          <NuxtLink
            to="/"
            class="flex items-center gap-2 text-secondary-700 hover:text-secondary-900 transition-colors text-sm font-medium"
          >
            <i class="pi pi-arrow-left text-sm" />
            <span class="hidden sm:inline">Retour à l'accueil</span>
            <span class="sm:hidden">Accueil</span>
          </NuxtLink>
        </div>
      </nav>
    </header>

    <!-- Main Content -->
    <main class="flex-1 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <slot />
    </main>

    <!-- Minimal Footer -->
    <footer class="py-4 text-center text-sm text-gray-500 border-t border-gray-100">
      <p>&copy; {{ new Date().getFullYear() }} Stoflow. Tous droits reserves.</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
// Note: Auth redirect is handled by the global auth middleware
// No need to duplicate here
</script>

<template>
  <footer class="bg-white border-t border-gray-200 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex flex-col sm:flex-row justify-between items-center gap-4">
        <!-- Logo & Copyright -->
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 bg-secondary-900 rounded flex items-center justify-center">
            <span class="text-primary-400 font-bold text-xs">S</span>
          </div>
          <span class="text-gray-500 text-sm">
            &copy; {{ new Date().getFullYear() }} Stoflow. Tous droits réservés.
          </span>
        </div>

        <!-- Links -->
        <div class="flex items-center gap-6 text-sm">
          <NuxtLink to="/" class="text-gray-500 hover:text-secondary-900 transition-colors">
            Accueil
          </NuxtLink>
          <NuxtLink to="/#pricing" class="text-gray-500 hover:text-secondary-900 transition-colors">
            Tarifs
          </NuxtLink>
          <NuxtLink to="/docs" class="text-gray-500 hover:text-secondary-900 transition-colors">
            Aide
          </NuxtLink>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
// FooterMinimal - Minimal footer for auth pages and secondary pages
</script>

<template>
  <footer class="bg-secondary-900 text-white py-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
        <!-- Logo & Description -->
        <div class="col-span-1 md:col-span-2">
          <div class="flex items-center gap-2 mb-4">
            <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
              <span class="text-secondary-900 font-bold text-xl">S</span>
            </div>
            <span class="text-2xl font-bold">Stoflow</span>
          </div>
          <p class="text-gray-400 max-w-md">
            La plateforme SaaS qui simplifie la vente multi-marketplace.
            Gérez tous vos produits depuis un seul endroit.
          </p>
        </div>

        <!-- Product Links -->
        <div>
          <h4 class="font-bold mb-4 text-white">Produit</h4>
          <ul class="space-y-2 text-gray-400">
            <li><a href="#features" class="hover:text-white transition-colors">Fonctionnalités</a></li>
            <li><a href="#pricing" class="hover:text-white transition-colors">Tarifs</a></li>
            <li><a href="#faq" class="hover:text-white transition-colors">FAQ</a></li>
            <li><NuxtLink to="/docs" class="hover:text-white transition-colors">Documentation</NuxtLink></li>
          </ul>
        </div>

        <!-- Legal Links -->
        <div>
          <h4 class="font-bold mb-4 text-white">Légal</h4>
          <ul class="space-y-2 text-gray-400">
            <li><a href="#" class="hover:text-white transition-colors">Mentions légales</a></li>
            <li><a href="#" class="hover:text-white transition-colors">CGU</a></li>
            <li><a href="#" class="hover:text-white transition-colors">Politique de confidentialité</a></li>
          </ul>
        </div>
      </div>

      <!-- Copyright -->
      <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-500">
        <p>&copy; {{ new Date().getFullYear() }} Stoflow. Tous droits réservés.</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
// FooterFull - Full footer for public pages (landing, docs)
</script>

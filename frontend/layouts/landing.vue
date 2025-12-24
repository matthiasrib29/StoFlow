<template>
  <div class="min-h-screen bg-white">
    <!-- Header Navigation -->
    <header class="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-gray-100">
      <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <!-- Logo -->
          <div class="flex items-center gap-2 cursor-pointer" @click="navigateTo('/')">
            <div class="w-10 h-10 bg-secondary-900 rounded-lg flex items-center justify-center">
              <span class="text-primary-400 font-bold text-xl">S</span>
            </div>
            <span class="text-2xl font-bold text-secondary-900">Stoflow</span>
          </div>

          <!-- Desktop Navigation -->
          <div class="hidden md:flex items-center gap-8">
            <a href="#features" class="text-secondary-700 hover:text-secondary-900 transition-colors">
              Fonctionnalités
            </a>
            <a href="#how-it-works" class="text-secondary-700 hover:text-secondary-900 transition-colors">
              Comment ça marche
            </a>
            <a href="#pricing" class="text-secondary-700 hover:text-secondary-900 transition-colors">
              Tarifs
            </a>
            <a href="#faq" class="text-secondary-700 hover:text-secondary-900 transition-colors">
              FAQ
            </a>
            <NuxtLink to="/docs" class="text-secondary-700 hover:text-secondary-900 transition-colors">
              Documentation
            </NuxtLink>
          </div>

          <!-- CTA Buttons -->
          <div class="flex items-center gap-3">
            <Button
              label="Connexion"
              class="hidden sm:flex bg-transparent text-secondary-900 border border-gray-300 hover:bg-gray-100"
              @click="navigateTo('/login')"
            />
            <Button
              label="Essai gratuit"
              icon="pi pi-arrow-right"
              icon-pos="right"
              class="bg-secondary-900 hover:bg-secondary-800 text-white border-0 font-bold"
              @click="navigateTo('/register')"
            />
          </div>

          <!-- Mobile Menu Button -->
          <button
            class="md:hidden p-2 text-secondary-900"
            @click="mobileMenuOpen = !mobileMenuOpen"
          >
            <i :class="mobileMenuOpen ? 'pi pi-times' : 'pi pi-bars'" class="text-xl" />
          </button>
        </div>

        <!-- Mobile Menu -->
        <div
          v-if="mobileMenuOpen"
          class="md:hidden py-4 border-t border-gray-100"
        >
          <div class="flex flex-col gap-4">
            <a href="#features" class="text-secondary-700 hover:text-secondary-900" @click="mobileMenuOpen = false">
              Fonctionnalités
            </a>
            <a href="#how-it-works" class="text-secondary-700 hover:text-secondary-900" @click="mobileMenuOpen = false">
              Comment ça marche
            </a>
            <a href="#pricing" class="text-secondary-700 hover:text-secondary-900" @click="mobileMenuOpen = false">
              Tarifs
            </a>
            <a href="#faq" class="text-secondary-700 hover:text-secondary-900" @click="mobileMenuOpen = false">
              FAQ
            </a>
            <NuxtLink to="/docs" class="text-secondary-700 hover:text-secondary-900" @click="mobileMenuOpen = false">
              Documentation
            </NuxtLink>
            <Button
              label="Connexion"
              class="w-full bg-transparent text-secondary-900 border-2 border-secondary-900"
              @click="navigateTo('/login')"
            />
          </div>
        </div>
      </nav>
    </header>

    <!-- Main Content -->
    <main class="pt-16">
      <slot />
    </main>

    <!-- Footer -->
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

          <!-- Links -->
          <div>
            <h4 class="font-bold mb-4 text-white">Produit</h4>
            <ul class="space-y-2 text-gray-400">
              <li><a href="#features" class="hover:text-white transition-colors">Fonctionnalités</a></li>
              <li><a href="#pricing" class="hover:text-white transition-colors">Tarifs</a></li>
              <li><a href="#faq" class="hover:text-white transition-colors">FAQ</a></li>
              <li><NuxtLink to="/docs" class="hover:text-white transition-colors">Documentation</NuxtLink></li>
            </ul>
          </div>

          <!-- Legal -->
          <div>
            <h4 class="font-bold mb-4 text-white">Légal</h4>
            <ul class="space-y-2 text-gray-400">
              <li><a href="#" class="hover:text-white transition-colors">Mentions légales</a></li>
              <li><a href="#" class="hover:text-white transition-colors">CGU</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Politique de confidentialité</a></li>
            </ul>
          </div>
        </div>

        <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-500">
          <p>&copy; {{ new Date().getFullYear() }} Stoflow. Tous droits réservés.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
const mobileMenuOpen = ref(false)

// Redirect if already authenticated
const authStore = useAuthStore()

onMounted(() => {
  if (authStore.isAuthenticated) {
    navigateTo('/dashboard')
  }
})
</script>

<template>
  <header class="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-gray-100">
    <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Logo -->
        <NuxtLink to="/" class="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div class="w-10 h-10 bg-secondary-900 rounded-lg flex items-center justify-center">
            <span class="text-primary-400 font-bold text-xl">S</span>
          </div>
          <span class="text-2xl font-bold text-secondary-900">Stoflow</span>
        </NuxtLink>

        <!-- Desktop Navigation -->
        <div class="hidden md:flex items-center gap-8">
          <NuxtLink
            to="/#features"
            class="text-secondary-700 hover:text-secondary-900 transition-colors"
          >
            Fonctionnalités
          </NuxtLink>
          <NuxtLink
            to="/#pricing"
            class="text-secondary-700 hover:text-secondary-900 transition-colors"
          >
            Tarifs
          </NuxtLink>
          <NuxtLink
            to="/docs"
            class="transition-colors px-3 py-1.5 rounded-lg"
            :class="isDocsPage
              ? 'bg-primary-100 text-primary-700 font-semibold'
              : 'text-secondary-700 hover:text-secondary-900 hover:bg-gray-100'"
          >
            Documentation
          </NuxtLink>
          <NuxtLink
            to="/#faq"
            class="text-secondary-700 hover:text-secondary-900 transition-colors"
          >
            FAQ
          </NuxtLink>
        </div>

        <!-- CTA Buttons -->
        <div class="hidden sm:flex items-center gap-3">
          <Button
            label="Connexion"
            class="bg-transparent text-secondary-900 border border-gray-300 hover:bg-gray-100"
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
      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="opacity-0 -translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition-all duration-150 ease-in"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-2"
      >
        <div
          v-if="mobileMenuOpen"
          class="md:hidden py-4 border-t border-gray-100"
        >
          <div class="flex flex-col gap-4">
            <NuxtLink
              to="/#features"
              class="text-secondary-700 hover:text-secondary-900"
              @click="mobileMenuOpen = false"
            >
              Fonctionnalités
            </NuxtLink>
            <NuxtLink
              to="/#pricing"
              class="text-secondary-700 hover:text-secondary-900"
              @click="mobileMenuOpen = false"
            >
              Tarifs
            </NuxtLink>
            <NuxtLink
              to="/docs"
              class="px-3 py-2 rounded-lg transition-colors"
              :class="isDocsPage
                ? 'bg-primary-100 text-primary-700 font-semibold'
                : 'text-secondary-700 hover:text-secondary-900 hover:bg-gray-100'"
              @click="mobileMenuOpen = false"
            >
              Documentation
            </NuxtLink>
            <NuxtLink
              to="/#faq"
              class="text-secondary-700 hover:text-secondary-900"
              @click="mobileMenuOpen = false"
            >
              FAQ
            </NuxtLink>
            <div class="flex flex-col gap-2 pt-2 border-t border-gray-100">
              <Button
                label="Connexion"
                class="w-full bg-transparent text-secondary-900 border border-gray-300"
                @click="navigateTo('/login')"
              />
              <Button
                label="Essai gratuit"
                icon="pi pi-arrow-right"
                icon-pos="right"
                class="w-full bg-secondary-900 text-white border-0 font-bold"
                @click="navigateTo('/register')"
              />
            </div>
          </div>
        </div>
      </Transition>
    </nav>
  </header>
</template>

<script setup lang="ts">
// HeaderPublic - Public pages header (landing, docs)

const route = useRoute()
const mobileMenuOpen = ref(false)

const isDocsPage = computed(() => route.path.startsWith('/docs'))

// Close mobile menu on route change
watch(() => route.path, () => {
  mobileMenuOpen.value = false
})
</script>

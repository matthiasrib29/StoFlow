<template>
  <section id="how-it-works" class="py-20 lg:py-32 bg-white">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-16 animate-on-scroll">
        <span class="inline-block text-sm font-semibold text-secondary-700 uppercase tracking-wider mb-3">Simplicité</span>
        <h2 class="text-3xl sm:text-4xl font-bold text-secondary-900 mb-4">
          Comment ça marche ?
        </h2>
        <p class="text-xl text-secondary-700 max-w-2xl mx-auto">
          Commencez à vendre en quelques minutes
        </p>
      </div>

      <div class="grid md:grid-cols-3 gap-8 lg:gap-12">
        <div
          v-for="(step, index) in steps"
          :key="step.title"
          class="relative animate-on-scroll"
          :class="{ 'animation-delay-200': index === 1, 'animation-delay-400': index === 2 }"
        >
          <div class="bg-gray-50 rounded-2xl p-8 border border-gray-200">
            <div class="absolute -top-5 -left-5 w-12 h-12 bg-secondary-900 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-lg">
              {{ index + 1 }}
            </div>
            <div class="pt-4">
              <i :class="['pi', step.icon, 'text-4xl text-secondary-900 mb-4']" />
              <h3 class="text-xl font-bold text-secondary-900 mb-3">{{ step.title }}</h3>
              <p class="text-secondary-700">{{ step.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const steps = [
  {
    icon: 'pi-user-plus',
    title: 'Créez votre compte',
    description: 'Inscrivez-vous gratuitement en quelques secondes. Aucune carte bancaire requise.'
  },
  {
    icon: 'pi-link',
    title: 'Connectez vos comptes',
    description: 'Liez vos comptes Vinted, eBay et Etsy en toute sécurité via notre extension navigateur.'
  },
  {
    icon: 'pi-send',
    title: 'Publiez et vendez',
    description: 'Créez vos annonces et publiez-les partout en un clic. C\'est aussi simple que ça !'
  }
]
</script>

<template>
  <section class="py-20 lg:py-32 bg-white">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-16 animate-on-scroll">
        <span class="inline-block text-sm font-semibold text-secondary-700 uppercase tracking-wider mb-3">Témoignages</span>
        <h2 class="text-3xl sm:text-4xl font-bold text-secondary-900 mb-4">
          Ils nous font confiance
        </h2>
        <p class="text-xl text-secondary-700 max-w-2xl mx-auto">
          Découvrez ce que nos utilisateurs pensent de Stoflow
        </p>
      </div>

      <div class="grid md:grid-cols-3 gap-8">
        <div
          v-for="(testimonial, index) in testimonials"
          :key="testimonial.name"
          class="bg-white rounded-2xl p-8 border-2 border-gray-100 shadow-sm hover:shadow-lg hover:border-primary-400 transition-all duration-300 animate-on-scroll"
          :class="{ 'animation-delay-200': index === 1, 'animation-delay-400': index === 2 }"
        >
          <div class="flex items-center gap-1 mb-4">
            <i v-for="n in 5" :key="n" class="pi pi-star-fill text-primary-400" />
          </div>
          <blockquote class="text-secondary-600 mb-6 leading-relaxed">
            {{ testimonial.quote }}
          </blockquote>
          <div class="flex items-center gap-4">
            <div class="relative">
              <div :class="['w-14 h-14 rounded-full flex items-center justify-center shadow-md', testimonial.avatarGradient]">
                <span class="text-white font-bold text-lg">{{ testimonial.initials }}</span>
              </div>
              <div :class="['absolute -bottom-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center border-2 border-white', testimonial.platformColor]">
                <i class="pi pi-check text-white text-xs" />
              </div>
            </div>
            <div>
              <div class="font-bold text-secondary-900">{{ testimonial.name }}</div>
              <div class="text-sm text-secondary-600">{{ testimonial.role }}</div>
              <div class="text-xs text-primary-600 font-medium mt-1">{{ testimonial.stats }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const testimonials = [
  {
    name: 'Marie L.',
    initials: 'ML',
    role: 'Vendeuse Vinted',
    stats: '2 400+ ventes',
    quote: 'Je gère maintenant 200+ articles sur 3 plateformes. J\'économise 5h par semaine grâce à Stoflow. Plus besoin de jongler entre les apps !',
    avatarGradient: 'bg-gradient-to-br from-pink-400 to-rose-500',
    platformColor: 'bg-platform-vinted'
  },
  {
    name: 'Thomas D.',
    initials: 'TD',
    role: 'Vendeur eBay Pro',
    stats: '500+ articles actifs',
    quote: 'La génération IA est bluffante. Mes annonces sont plus pro et j\'ai vu mes ventes augmenter de +35% le premier mois. ROI immédiat !',
    avatarGradient: 'bg-gradient-to-br from-blue-400 to-indigo-500',
    platformColor: 'bg-platform-ebay'
  },
  {
    name: 'Sophie B.',
    initials: 'SB',
    role: 'Créatrice Etsy',
    stats: '3 boutiques connectées',
    quote: 'Enfin une solution qui comprend les vendeurs multi-plateformes. Je synchronise Etsy + Vinted en un clic. Support au top, mises à jour fréquentes.',
    avatarGradient: 'bg-gradient-to-br from-orange-400 to-amber-500',
    platformColor: 'bg-platform-etsy'
  }
]
</script>

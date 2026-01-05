<template>
  <section id="features" class="py-20 lg:py-32 bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-16 animate-on-scroll">
        <span class="inline-block text-sm font-semibold text-secondary-700 uppercase tracking-wider mb-3">Fonctionnalités</span>
        <h2 class="text-3xl sm:text-4xl font-bold text-secondary-900 mb-4">
          Tout ce dont vous avez besoin
        </h2>
        <p class="text-xl text-secondary-700 max-w-2xl mx-auto">
          Une seule plateforme pour gérer toutes vos ventes en ligne
        </p>
      </div>

      <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
        <div
          v-for="feature in features"
          :key="feature.title"
          class="group bg-white rounded-2xl p-8 border border-gray-200 hover:border-secondary-900 hover:shadow-xl transition-all duration-300 animate-on-scroll"
        >
          <div class="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center mb-6 group-hover:bg-secondary-900 transition-colors">
            <i :class="['pi', feature.icon, 'text-2xl text-secondary-600 group-hover:text-primary-400']" />
          </div>
          <h3 class="text-xl font-bold text-secondary-900 mb-3">{{ feature.title }}</h3>
          <p class="text-secondary-700">{{ feature.description }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const features = [
  {
    icon: 'pi-sync',
    title: 'Synchronisation automatique',
    description: 'Vos stocks sont synchronisés en temps réel sur toutes vos plateformes. Plus de survente ni de gestion manuelle.'
  },
  {
    icon: 'pi-bolt',
    title: 'Publication en un clic',
    description: 'Créez une annonce une fois, publiez-la sur Vinted, eBay et Etsy automatiquement avec les bons formats.'
  },
  {
    icon: 'pi-sparkles',
    title: 'Descriptions IA',
    description: 'Générez des descriptions optimisées pour chaque marketplace grâce à notre intelligence artificielle.'
  },
  {
    icon: 'pi-comments',
    title: 'Messagerie unifiée',
    description: 'Répondez à tous vos clients depuis une seule boîte de réception. Fini les allers-retours entre applications.'
  },
  {
    icon: 'pi-chart-line',
    title: 'Statistiques détaillées',
    description: 'Suivez vos performances, analysez vos ventes et optimisez votre stratégie avec des tableaux de bord clairs.'
  },
  {
    icon: 'pi-shield',
    title: 'Sécurisé',
    description: 'Vos données sont protégées avec un chiffrement de niveau bancaire. Conformité RGPD garantie.'
  }
]
</script>

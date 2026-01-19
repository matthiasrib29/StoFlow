<template>
  <section class="relative overflow-hidden bg-gradient-to-br from-white via-gray-50 to-white py-20 lg:py-32">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid lg:grid-cols-2 gap-12 items-center">
        <!-- Left: Text Content -->
        <div class="animate-fade-in-up">
          <div class="inline-flex items-center gap-2 bg-secondary-900 text-white px-4 py-2 rounded-full text-sm font-medium mb-6">
            <i class="pi pi-sparkles text-primary-400" />
            Nouveau : Génération IA des descriptions
          </div>
          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold text-secondary-900 leading-tight mb-6">
            Vendez sur
            <span class="bg-gradient-to-r from-secondary-900 to-secondary-700 bg-clip-text text-transparent">plusieurs marketplaces</span>
            en un clic
          </h1>
          <!-- PMV2: Etsy removed from description -->
          <p class="text-xl text-secondary-600 mb-4 max-w-lg">
            Gérez vos produits Vinted et eBay depuis une seule plateforme.
            Synchronisez vos stocks, automatisez vos publications.
          </p>
          <p class="text-sm text-primary-600 font-medium mb-8 flex items-center gap-2">
            <i class="pi pi-users" />
            Déjà 500+ vendeurs économisent 5h/semaine
          </p>
          <div class="flex flex-col sm:flex-row gap-4">
            <Button
              label="Commencer gratuitement"
              icon="pi pi-arrow-right"
              icon-pos="right"
              class="bg-secondary-900 hover:bg-secondary-800 text-white border-0 font-bold text-lg px-8 py-3"
              @click="navigateTo('/register')"
            />
            <Button
              label="Voir la démo"
              class="bg-transparent text-secondary-900 border-2 border-secondary-900 hover:bg-secondary-100 font-bold text-lg px-8 py-3 group"
              @click="$emit('showDemo')"
            >
              <template #icon>
                <span class="inline-flex items-center justify-center w-6 h-6 bg-secondary-900 text-white rounded-full mr-2 group-hover:bg-primary-400 group-hover:text-secondary-900 transition-colors">
                  <i class="pi pi-play text-xs" />
                </span>
              </template>
            </Button>
          </div>
          <!-- Trust badges -->
          <div class="mt-10 flex items-center gap-6 text-secondary-700">
            <div class="flex items-center gap-2">
              <i class="pi pi-check-circle text-primary-500" />
              <span>Gratuit 14 jours</span>
            </div>
            <div class="flex items-center gap-2">
              <i class="pi pi-check-circle text-primary-500" />
              <span>Sans engagement</span>
            </div>
          </div>
        </div>

        <!-- Right: Visual -->
        <div class="relative animate-fade-in-up animation-delay-200">
          <div class="relative bg-white rounded-2xl shadow-2xl border-2 border-secondary-900 p-6">
            <!-- Mock Dashboard Preview -->
            <div class="bg-gray-50 rounded-lg p-4 mb-4">
              <div class="flex items-center justify-between mb-4">
                <span class="font-bold text-secondary-900">Tableau de bord</span>
                <!-- PMV2: Etsy dot removed -->
                <div class="flex gap-2">
                  <div class="w-3 h-3 rounded-full bg-platform-vinted" />
                  <div class="w-3 h-3 rounded-full bg-platform-ebay" />
                </div>
              </div>
              <div class="grid grid-cols-3 gap-3">
                <div class="bg-white rounded-lg p-3 text-center border border-gray-200">
                  <div class="text-2xl font-bold text-secondary-900">156</div>
                  <div class="text-xs text-secondary-700">Produits</div>
                </div>
                <div class="bg-white rounded-lg p-3 text-center border border-gray-200">
                  <div class="text-2xl font-bold text-primary-500">42</div>
                  <div class="text-xs text-secondary-700">Ventes</div>
                </div>
                <div class="bg-white rounded-lg p-3 text-center border border-gray-200">
                  <div class="text-2xl font-bold text-secondary-900">3</div>
                  <div class="text-xs text-secondary-700">Plateformes</div>
                </div>
              </div>
            </div>
            <!-- Floating badges -->
            <div class="absolute -top-4 -right-4 bg-secondary-900 text-white px-4 py-2 rounded-full font-bold shadow-lg animate-bounce-slow border-2 border-primary-400">
              Multi-marketplace
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Background decoration -->
    <div class="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-gray-100/50 to-transparent -z-10" />
  </section>
</template>

<script setup lang="ts">
defineEmits<{
  showDemo: []
}>()
</script>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.8s ease-out forwards;
}

.animation-delay-200 {
  animation-delay: 0.2s;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-bounce-slow {
  animation: bounceSlow 3s ease-in-out infinite;
}

@keyframes bounceSlow {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}
</style>

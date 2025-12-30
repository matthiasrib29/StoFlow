<template>
  <NuxtLayout name="landing">
    <!-- Hero Section -->
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
            <p class="text-xl text-secondary-600 mb-4 max-w-lg">
              Gérez vos produits Vinted, eBay et Etsy depuis une seule plateforme.
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
                  <div class="flex gap-2">
                    <div class="w-3 h-3 rounded-full bg-platform-vinted" />
                    <div class="w-3 h-3 rounded-full bg-platform-ebay" />
                    <div class="w-3 h-3 rounded-full bg-platform-etsy" />
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

    <!-- Stats Counter Section -->
    <LandingStatsCounter />

    <!-- Trust Badges Section -->
    <LandingTrustBadges />

    <!-- Platforms Section -->
    <section class="py-16 bg-white border-y border-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <p class="text-center text-secondary-700 mb-10 text-lg">Connectez-vous à vos marketplaces préférées</p>
        <div class="flex flex-wrap justify-center items-center gap-10 md:gap-20">
          <div class="flex items-center gap-4 opacity-70 hover:opacity-100 transition-all hover:scale-105 cursor-pointer">
            <img src="/images/platforms/vinted-logo.png" alt="Vinted" class="h-10 w-auto" />
          </div>
          <div class="flex items-center gap-4 opacity-70 hover:opacity-100 transition-all hover:scale-105 cursor-pointer">
            <img src="/images/platforms/ebay-logo.png" alt="eBay" class="h-10 w-auto" />
          </div>
          <div class="flex items-center gap-4 opacity-70 hover:opacity-100 transition-all hover:scale-105 cursor-pointer">
            <img src="/images/platforms/etsy-logo.png" alt="Etsy" class="h-10 w-auto" />
          </div>
          <div class="flex items-center gap-3 text-secondary-400">
            <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center border-2 border-dashed border-gray-300">
              <span class="font-bold text-lg text-secondary-400">+</span>
            </div>
            <span class="text-lg font-medium">Bientôt plus...</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
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
          <!-- Feature 1 -->
          <div class="group bg-white rounded-2xl p-8 border border-gray-200 hover:border-secondary-900 hover:shadow-xl transition-all duration-300 animate-on-scroll">
            <div class="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center mb-6 group-hover:bg-secondary-900 transition-colors">
              <i class="pi pi-sync text-2xl text-secondary-600 group-hover:text-primary-400" />
            </div>
            <h3 class="text-xl font-bold text-secondary-900 mb-3">Synchronisation automatique</h3>
            <p class="text-secondary-700">
              Vos stocks sont synchronisés en temps réel sur toutes vos plateformes.
              Plus de survente ni de gestion manuelle.
            </p>
          </div>

          <!-- Feature 2 -->
          <div class="group bg-white rounded-2xl p-8 border border-gray-200 hover:border-secondary-900 hover:shadow-xl transition-all duration-300 animate-on-scroll">
            <div class="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center mb-6 group-hover:bg-secondary-900 transition-colors">
              <i class="pi pi-bolt text-2xl text-secondary-600 group-hover:text-primary-400" />
            </div>
            <h3 class="text-xl font-bold text-secondary-900 mb-3">Publication en un clic</h3>
            <p class="text-secondary-700">
              Créez une annonce une fois, publiez-la sur Vinted, eBay et Etsy
              automatiquement avec les bons formats.
            </p>
          </div>

          <!-- Feature 3 -->
          <div class="group bg-white rounded-2xl p-8 border border-gray-200 hover:border-secondary-900 hover:shadow-xl transition-all duration-300 animate-on-scroll">
            <div class="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center mb-6 group-hover:bg-secondary-900 transition-colors">
              <i class="pi pi-sparkles text-2xl text-secondary-600 group-hover:text-primary-400" />
            </div>
            <h3 class="text-xl font-bold text-secondary-900 mb-3">Descriptions IA</h3>
            <p class="text-secondary-700">
              Générez des descriptions optimisées pour chaque marketplace
              grâce à notre intelligence artificielle.
            </p>
          </div>

          <!-- Feature 4 -->
          <div class="group bg-white rounded-2xl p-8 border border-gray-200 hover:border-secondary-900 hover:shadow-xl transition-all duration-300 animate-on-scroll">
            <div class="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center mb-6 group-hover:bg-secondary-900 transition-colors">
              <i class="pi pi-comments text-2xl text-secondary-600 group-hover:text-primary-400" />
            </div>
            <h3 class="text-xl font-bold text-secondary-900 mb-3">Messagerie unifiée</h3>
            <p class="text-secondary-700">
              Répondez à tous vos clients depuis une seule boîte de réception.
              Fini les allers-retours entre applications.
            </p>
          </div>

          <!-- Feature 5 -->
          <div class="group bg-white rounded-2xl p-8 border border-gray-200 hover:border-secondary-900 hover:shadow-xl transition-all duration-300 animate-on-scroll">
            <div class="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center mb-6 group-hover:bg-secondary-900 transition-colors">
              <i class="pi pi-chart-line text-2xl text-secondary-600 group-hover:text-primary-400" />
            </div>
            <h3 class="text-xl font-bold text-secondary-900 mb-3">Statistiques détaillées</h3>
            <p class="text-secondary-700">
              Suivez vos performances, analysez vos ventes et optimisez
              votre stratégie avec des tableaux de bord clairs.
            </p>
          </div>

          <!-- Feature 6 -->
          <div class="group bg-white rounded-2xl p-8 border border-gray-200 hover:border-secondary-900 hover:shadow-xl transition-all duration-300 animate-on-scroll">
            <div class="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center mb-6 group-hover:bg-secondary-900 transition-colors">
              <i class="pi pi-shield text-2xl text-secondary-600 group-hover:text-primary-400" />
            </div>
            <h3 class="text-xl font-bold text-secondary-900 mb-3">Sécurisé</h3>
            <p class="text-secondary-700">
              Vos données sont protégées avec un chiffrement de niveau bancaire.
              Conformité RGPD garantie.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Why Stoflow Section -->
    <LandingWhyStoflow />

    <!-- How It Works Section -->
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
          <!-- Step 1 -->
          <div class="relative animate-on-scroll">
            <div class="bg-gray-50 rounded-2xl p-8 border border-gray-200">
              <div class="absolute -top-5 -left-5 w-12 h-12 bg-secondary-900 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-lg">
                1
              </div>
              <div class="pt-4">
                <i class="pi pi-user-plus text-4xl text-secondary-900 mb-4" />
                <h3 class="text-xl font-bold text-secondary-900 mb-3">Créez votre compte</h3>
                <p class="text-secondary-700">
                  Inscrivez-vous gratuitement en quelques secondes.
                  Aucune carte bancaire requise.
                </p>
              </div>
            </div>
          </div>

          <!-- Step 2 -->
          <div class="relative animate-on-scroll animation-delay-200">
            <div class="bg-gray-50 rounded-2xl p-8 border border-gray-200">
              <div class="absolute -top-5 -left-5 w-12 h-12 bg-secondary-900 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-lg">
                2
              </div>
              <div class="pt-4">
                <i class="pi pi-link text-4xl text-secondary-900 mb-4" />
                <h3 class="text-xl font-bold text-secondary-900 mb-3">Connectez vos comptes</h3>
                <p class="text-secondary-700">
                  Liez vos comptes Vinted, eBay et Etsy en toute sécurité
                  via notre extension navigateur.
                </p>
              </div>
            </div>
          </div>

          <!-- Step 3 -->
          <div class="relative animate-on-scroll animation-delay-400">
            <div class="bg-gray-50 rounded-2xl p-8 border border-gray-200">
              <div class="absolute -top-5 -left-5 w-12 h-12 bg-secondary-900 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-lg">
                3
              </div>
              <div class="pt-4">
                <i class="pi pi-send text-4xl text-secondary-900 mb-4" />
                <h3 class="text-xl font-bold text-secondary-900 mb-3">Publiez et vendez</h3>
                <p class="text-secondary-700">
                  Créez vos annonces et publiez-les partout en un clic.
                  C'est aussi simple que ça !
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Pricing Section - Dynamic from API -->
    <section id="pricing" class="py-20 lg:py-32 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12 animate-on-scroll">
          <span class="inline-block text-sm font-semibold text-secondary-700 uppercase tracking-wider mb-3">Tarification</span>
          <h2 class="text-3xl sm:text-4xl font-bold text-secondary-900 mb-4">
            Tarifs simples et transparents
          </h2>
          <p class="text-xl text-secondary-700 max-w-2xl mx-auto">
            Pas de frais cachés. Annulez à tout moment.
          </p>
        </div>

        <!-- Billing Toggle -->
        <div class="flex justify-center mb-12">
          <div class="inline-flex items-center bg-white rounded-full p-1 border-2 border-gray-200 shadow-sm">
            <button
              :class="[
                'px-6 py-2 rounded-full text-sm font-semibold transition-all',
                !isYearly ? 'bg-secondary-900 text-white' : 'text-secondary-600 hover:text-secondary-900'
              ]"
              @click="isYearly = false"
            >
              Mensuel
            </button>
            <button
              :class="[
                'px-6 py-2 rounded-full text-sm font-semibold transition-all flex items-center gap-2',
                isYearly ? 'bg-secondary-900 text-white' : 'text-secondary-600 hover:text-secondary-900'
              ]"
              @click="isYearly = true"
            >
              Annuel
              <span class="bg-primary-400 text-secondary-900 text-xs font-bold px-2 py-0.5 rounded-full">
                -20%
              </span>
            </button>
          </div>
        </div>

        <!-- Loading state -->
        <div v-if="pricingLoading" class="flex justify-center py-12">
          <i class="pi pi-spin pi-spinner text-4xl text-secondary-400" />
        </div>

        <!-- Pricing cards -->
        <div v-else class="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          <div
            v-for="plan in plans"
            :key="plan.tier"
            :class="[
              'rounded-2xl p-8 border-2 animate-on-scroll transition-all duration-300',
              plan.is_popular
                ? 'bg-secondary-900 border-primary-400 shadow-xl transform lg:-translate-y-4'
                : 'bg-white border-gray-200 hover:border-secondary-300'
            ]"
          >
            <!-- Popular badge -->
            <div v-if="plan.is_popular" class="inline-block bg-primary-400 text-secondary-900 text-sm font-bold px-3 py-1 rounded-full mb-4">
              Populaire
            </div>

            <!-- Plan name -->
            <h3 :class="['text-xl font-bold mb-2', plan.is_popular ? 'text-white' : 'text-secondary-900']">
              {{ plan.display_name }}
            </h3>

            <!-- Description -->
            <p :class="['mb-6', plan.is_popular ? 'text-gray-400' : 'text-secondary-700']">
              {{ plan.description }}
            </p>

            <!-- Price -->
            <div class="mb-2">
              <span
                v-if="isYearly && plan.annual_discount_percent > 0"
                :class="['text-lg line-through mr-2', plan.is_popular ? 'text-gray-500' : 'text-gray-400']"
              >
                {{ plan.price }}€
              </span>
              <span :class="['text-4xl font-bold', plan.is_popular ? 'text-white' : 'text-secondary-900']">
                {{ isYearly && plan.annual_discount_percent > 0 ? getAnnualPrice(plan) : plan.price }}€
              </span>
              <span :class="[plan.is_popular ? 'text-gray-400' : 'text-secondary-700']">/mois</span>
            </div>

            <!-- Savings -->
            <p
              v-if="isYearly && plan.annual_discount_percent > 0"
              :class="['text-sm mb-6 font-medium', plan.is_popular ? 'text-primary-400' : 'text-primary-600']"
            >
              Économisez {{ getAnnualSavings(plan) }}€/an
            </p>
            <div v-else class="mb-6" />

            <!-- Features -->
            <ul class="space-y-3 mb-8">
              <li
                v-for="feature in plan.features"
                :key="feature.feature_text"
                :class="['flex items-center gap-2', plan.is_popular ? 'text-gray-300' : 'text-secondary-600']"
              >
                <i :class="['pi pi-check', plan.is_popular ? 'text-primary-400' : 'text-primary-500']" />
                <span>{{ feature.feature_text }}</span>
              </li>
            </ul>

            <!-- CTA Button -->
            <Button
              :label="plan.cta_text || 'Commencer'"
              :icon="plan.tier !== 'free' ? 'pi pi-arrow-right' : undefined"
              :icon-pos="plan.tier !== 'free' ? 'right' : undefined"
              :class="[
                'w-full font-bold',
                plan.is_popular
                  ? 'bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0'
                  : 'bg-transparent text-secondary-900 border-2 border-secondary-900 hover:bg-secondary-900 hover:text-white'
              ]"
              @click="handlePlanClick(plan)"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- Testimonials Section -->
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
          <!-- Testimonial 1 - Marie -->
          <div class="bg-white rounded-2xl p-8 border-2 border-gray-100 shadow-sm hover:shadow-lg hover:border-primary-400 transition-all duration-300 animate-on-scroll">
            <div class="flex items-center gap-1 mb-4">
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
            </div>
            <blockquote class="text-secondary-600 mb-6 leading-relaxed">
              "Je gère maintenant <strong class="text-secondary-900">200+ articles</strong> sur 3 plateformes.
              J'économise <strong class="text-secondary-900">5h par semaine</strong> grâce à Stoflow.
              Plus besoin de jongler entre les apps !"
            </blockquote>
            <div class="flex items-center gap-4">
              <div class="relative">
                <div class="w-14 h-14 bg-gradient-to-br from-pink-400 to-rose-500 rounded-full flex items-center justify-center shadow-md">
                  <span class="text-white font-bold text-lg">ML</span>
                </div>
                <div class="absolute -bottom-1 -right-1 w-5 h-5 bg-platform-vinted rounded-full flex items-center justify-center border-2 border-white">
                  <i class="pi pi-check text-white text-xs" />
                </div>
              </div>
              <div>
                <div class="font-bold text-secondary-900">Marie L.</div>
                <div class="text-sm text-secondary-600">Vendeuse Vinted</div>
                <div class="text-xs text-primary-600 font-medium mt-1">2 400+ ventes</div>
              </div>
            </div>
          </div>

          <!-- Testimonial 2 - Thomas -->
          <div class="bg-white rounded-2xl p-8 border-2 border-gray-100 shadow-sm hover:shadow-lg hover:border-primary-400 transition-all duration-300 animate-on-scroll animation-delay-200">
            <div class="flex items-center gap-1 mb-4">
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
            </div>
            <blockquote class="text-secondary-600 mb-6 leading-relaxed">
              "La génération IA est bluffante. Mes annonces sont plus pro et
              j'ai vu mes ventes augmenter de <strong class="text-secondary-900">+35%</strong>
              le premier mois. ROI immédiat !"
            </blockquote>
            <div class="flex items-center gap-4">
              <div class="relative">
                <div class="w-14 h-14 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center shadow-md">
                  <span class="text-white font-bold text-lg">TD</span>
                </div>
                <div class="absolute -bottom-1 -right-1 w-5 h-5 bg-platform-ebay rounded-full flex items-center justify-center border-2 border-white">
                  <i class="pi pi-check text-white text-xs" />
                </div>
              </div>
              <div>
                <div class="font-bold text-secondary-900">Thomas D.</div>
                <div class="text-sm text-secondary-600">Vendeur eBay Pro</div>
                <div class="text-xs text-primary-600 font-medium mt-1">500+ articles actifs</div>
              </div>
            </div>
          </div>

          <!-- Testimonial 3 - Sophie -->
          <div class="bg-white rounded-2xl p-8 border-2 border-gray-100 shadow-sm hover:shadow-lg hover:border-primary-400 transition-all duration-300 animate-on-scroll animation-delay-400">
            <div class="flex items-center gap-1 mb-4">
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
            </div>
            <blockquote class="text-secondary-600 mb-6 leading-relaxed">
              "Enfin une solution qui comprend les vendeurs multi-plateformes.
              Je synchronise <strong class="text-secondary-900">Etsy + Vinted</strong>
              en un clic. Support au top, mises à jour fréquentes."
            </blockquote>
            <div class="flex items-center gap-4">
              <div class="relative">
                <div class="w-14 h-14 bg-gradient-to-br from-orange-400 to-amber-500 rounded-full flex items-center justify-center shadow-md">
                  <span class="text-white font-bold text-lg">SB</span>
                </div>
                <div class="absolute -bottom-1 -right-1 w-5 h-5 bg-platform-etsy rounded-full flex items-center justify-center border-2 border-white">
                  <i class="pi pi-check text-white text-xs" />
                </div>
              </div>
              <div>
                <div class="font-bold text-secondary-900">Sophie B.</div>
                <div class="text-sm text-secondary-600">Créatrice Etsy</div>
                <div class="text-xs text-primary-600 font-medium mt-1">3 boutiques connectées</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- FAQ Section -->
    <section id="faq" class="py-20 lg:py-32 bg-white">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16 animate-on-scroll">
          <h2 class="text-3xl sm:text-4xl font-bold text-secondary-900 mb-4">
            Questions fréquentes
          </h2>
          <p class="text-xl text-secondary-600">
            Vous avez des questions ? Nous avons les réponses.
          </p>
        </div>

        <div class="space-y-4">
          <div
            v-for="(faq, index) in faqs"
            :key="index"
            class="border-2 border-gray-200 rounded-xl overflow-hidden animate-on-scroll"
          >
            <button
              class="w-full flex items-center justify-between p-6 text-left bg-white hover:bg-gray-50 transition-colors gap-4"
              @click="toggleFaq(index)"
            >
              <div class="flex items-center gap-4">
                <div class="flex-shrink-0 w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <i :class="['pi', faq.icon, 'text-secondary-700']" />
                </div>
                <span class="font-bold text-secondary-900">{{ faq.question }}</span>
              </div>
              <i
                :class="openFaq === index ? 'pi pi-minus' : 'pi pi-plus'"
                class="text-primary-500 flex-shrink-0"
              />
            </button>
            <div
              v-show="openFaq === index"
              class="px-6 pb-6 pl-20 text-secondary-600"
            >
              {{ faq.answer }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="py-20 bg-secondary-900">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center animate-on-scroll">
        <h2 class="text-3xl sm:text-4xl font-bold text-white mb-6">
          Prêt à booster vos ventes ?
        </h2>
        <p class="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
          Rejoignez des centaines de vendeurs qui ont déjà simplifié leur gestion multi-marketplace avec Stoflow.
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            label="Commencer gratuitement"
            icon="pi pi-arrow-right"
            icon-pos="right"
            class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold text-lg px-8 py-3"
            @click="navigateTo('/register')"
          />
          <Button
            label="Voir la démo"
            icon="pi pi-play"
            class="bg-transparent text-white border-2 border-white hover:bg-white hover:text-secondary-900 font-bold text-lg px-8 py-3"
          />
        </div>
      </div>
    </section>

    <!-- Sticky CTA Mobile -->
    <LandingStickyCTA />

    <!-- Exit Intent Popup -->
    <LandingExitIntentPopup />
  </NuxtLayout>
</template>

<script setup lang="ts">
import type { PricingPlan } from '~/composables/usePricing'

// Disable default layout and page transitions for instant navigation
definePageMeta({
  layout: false,
  pageTransition: false
})

// Pricing - Dynamic from API
const { plans, loading: pricingLoading, fetchPricingPlans, getAnnualPrice, getAnnualSavings } = usePricing()
const isYearly = ref(true) // Default to yearly (better value)

// Fetch pricing plans and setup scroll animations on mount
onMounted(async () => {
  // Fetch pricing plans from API
  await fetchPricingPlans()

  // Setup scroll animation observer (small delay to ensure DOM is ready)
  setTimeout(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-visible')
            observer.unobserve(entry.target) // Only animate once
          }
        })
      },
      { threshold: 0.1, rootMargin: '50px' }
    )

    document.querySelectorAll('.animate-on-scroll').forEach((el) => {
      observer.observe(el)
    })
  }, 100)
})

// Handle plan CTA click
const handlePlanClick = (plan: PricingPlan) => {
  if (plan.tier === 'enterprise') {
    // Enterprise: contact page or mailto
    window.location.href = 'mailto:contact@stoflow.io?subject=Enterprise Plan'
  } else {
    // Other plans: go to register
    navigateTo('/register')
  }
}

// FAQ data with icons
const faqs = [
  {
    icon: 'pi-wallet',
    question: 'Stoflow est-il vraiment gratuit ?',
    answer: 'Oui ! Notre plan gratuit vous permet de gérer jusqu\'à 10 produits sur une marketplace sans aucun frais. C\'est parfait pour découvrir la plateforme. Pour plus de fonctionnalités, nos plans payants commencent à 19€/mois.'
  },
  {
    icon: 'pi-link',
    question: 'Comment fonctionne la connexion aux marketplaces ?',
    answer: 'Nous utilisons une extension navigateur sécurisée pour Vinted (qui n\'a pas d\'API publique) et des connexions OAuth officielles pour eBay et Etsy. Vos identifiants ne transitent jamais par nos serveurs.'
  },
  {
    icon: 'pi-shield',
    question: 'Mes données sont-elles sécurisées ?',
    answer: 'Absolument. Nous utilisons un chiffrement de niveau bancaire (AES-256) pour toutes vos données. Nos serveurs sont hébergés en Europe et nous sommes 100% conformes RGPD.'
  },
  {
    icon: 'pi-times-circle',
    question: 'Puis-je annuler à tout moment ?',
    answer: 'Oui, vous pouvez annuler votre abonnement à tout moment depuis votre espace client. Pas de période d\'engagement, pas de frais cachés. Vous gardez l\'accès jusqu\'à la fin de votre période payée.'
  },
  {
    icon: 'pi-sparkles',
    question: 'La génération IA est-elle incluse ?',
    answer: 'La génération de descriptions par IA est incluse dans les plans Pro (100 générations/mois) et Business (illimité). Le plan gratuit n\'inclut pas cette fonctionnalité.'
  },
  {
    icon: 'pi-clock',
    question: 'Combien de temps pour configurer Stoflow ?',
    answer: 'Moins de 5 minutes ! Créez votre compte, installez l\'extension navigateur, connectez vos marketplaces et vous êtes prêt. L\'import de vos produits existants est automatique.'
  },
  {
    icon: 'pi-desktop',
    question: 'L\'extension fonctionne-t-elle sur tous les navigateurs ?',
    answer: 'Notre extension est disponible sur Chrome et Firefox (les deux navigateurs les plus utilisés). Une version Edge est en cours de développement.'
  },
  {
    icon: 'pi-shopping-cart',
    question: 'Que se passe-t-il si un produit est vendu ?',
    answer: 'Lorsqu\'un produit est vendu sur une plateforme, Stoflow met automatiquement à jour le stock sur toutes vos autres marketplaces. Fini les surventes et les annulations !'
  }
]

const openFaq = ref<number | null>(null)

const toggleFaq = (index: number) => {
  openFaq.value = openFaq.value === index ? null : index
}

</script>

<style scoped>
/* Fade in up animation */
.animate-fade-in-up {
  animation: fadeInUp 0.8s ease-out forwards;
}

.animation-delay-200 {
  animation-delay: 0.2s;
}

.animation-delay-400 {
  animation-delay: 0.4s;
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

/* Bounce slow animation */
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

/* Scroll-triggered animations */
.animate-on-scroll {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 0.6s ease-out, transform 0.6s ease-out;
}

.animate-on-scroll:not(.animate-visible) {
  opacity: 0;
  transform: translateY(30px);
}

@media (prefers-reduced-motion: reduce) {
  .animate-on-scroll {
    opacity: 1 !important;
    transform: none !important;
  }
}

.animate-on-scroll.animation-delay-200 {
  transition-delay: 0.2s;
}

.animate-on-scroll.animation-delay-400 {
  transition-delay: 0.4s;
}
</style>

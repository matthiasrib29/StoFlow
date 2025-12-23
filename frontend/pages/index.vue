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
            <p class="text-xl text-secondary-600 mb-8 max-w-lg">
              Gérez vos produits Vinted, eBay et Etsy depuis une seule plateforme.
              Synchronisez vos stocks, automatisez vos publications.
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
                icon="pi pi-play"
                class="bg-transparent text-secondary-900 border-2 border-secondary-900 hover:bg-secondary-100 font-bold text-lg px-8 py-3"
              />
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

    <!-- Pricing Section -->
    <section id="pricing" class="py-20 lg:py-32 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16 animate-on-scroll">
          <span class="inline-block text-sm font-semibold text-secondary-700 uppercase tracking-wider mb-3">Tarification</span>
          <h2 class="text-3xl sm:text-4xl font-bold text-secondary-900 mb-4">
            Tarifs simples et transparents
          </h2>
          <p class="text-xl text-secondary-700 max-w-2xl mx-auto">
            Pas de frais cachés. Annulez à tout moment.
          </p>
        </div>

        <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <!-- Free Plan -->
          <div class="bg-white rounded-2xl p-8 border-2 border-gray-200 animate-on-scroll">
            <h3 class="text-xl font-bold text-secondary-900 mb-2">Gratuit</h3>
            <p class="text-secondary-700 mb-6">Pour découvrir Stoflow</p>
            <div class="mb-6">
              <span class="text-4xl font-bold text-secondary-900">0€</span>
              <span class="text-secondary-700">/mois</span>
            </div>
            <ul class="space-y-3 mb-8">
              <li class="flex items-center gap-2 text-secondary-600">
                <i class="pi pi-check text-primary-500" />
                <span>Jusqu'à 10 produits</span>
              </li>
              <li class="flex items-center gap-2 text-secondary-600">
                <i class="pi pi-check text-primary-500" />
                <span>1 marketplace</span>
              </li>
              <li class="flex items-center gap-2 text-secondary-600">
                <i class="pi pi-check text-primary-500" />
                <span>Support email</span>
              </li>
            </ul>
            <Button
              label="Commencer"
              class="w-full bg-transparent text-secondary-900 border-2 border-secondary-900 hover:bg-secondary-900 hover:text-white"
              @click="navigateTo('/register')"
            />
          </div>

          <!-- Pro Plan (Featured) -->
          <div class="bg-secondary-900 rounded-2xl p-8 border-2 border-primary-400 shadow-xl transform md:-translate-y-4 animate-on-scroll">
            <div class="inline-block bg-primary-400 text-secondary-900 text-sm font-bold px-3 py-1 rounded-full mb-4">
              Populaire
            </div>
            <h3 class="text-xl font-bold text-white mb-2">Pro</h3>
            <p class="text-gray-400 mb-6">Pour les vendeurs actifs</p>
            <div class="mb-6">
              <span class="text-4xl font-bold text-white">19€</span>
              <span class="text-gray-400">/mois</span>
            </div>
            <ul class="space-y-3 mb-8">
              <li class="flex items-center gap-2 text-gray-300">
                <i class="pi pi-check text-primary-400" />
                <span>Produits illimités</span>
              </li>
              <li class="flex items-center gap-2 text-gray-300">
                <i class="pi pi-check text-primary-400" />
                <span>Toutes les marketplaces</span>
              </li>
              <li class="flex items-center gap-2 text-gray-300">
                <i class="pi pi-check text-primary-400" />
                <span>Génération IA (100/mois)</span>
              </li>
              <li class="flex items-center gap-2 text-gray-300">
                <i class="pi pi-check text-primary-400" />
                <span>Support prioritaire</span>
              </li>
            </ul>
            <Button
              label="Essai gratuit 14 jours"
              icon="pi pi-arrow-right"
              icon-pos="right"
              class="w-full bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-bold"
              @click="navigateTo('/register')"
            />
          </div>

          <!-- Business Plan -->
          <div class="bg-white rounded-2xl p-8 border-2 border-gray-200 animate-on-scroll">
            <h3 class="text-xl font-bold text-secondary-900 mb-2">Business</h3>
            <p class="text-secondary-700 mb-6">Pour les professionnels</p>
            <div class="mb-6">
              <span class="text-4xl font-bold text-secondary-900">49€</span>
              <span class="text-secondary-700">/mois</span>
            </div>
            <ul class="space-y-3 mb-8">
              <li class="flex items-center gap-2 text-secondary-600">
                <i class="pi pi-check text-primary-500" />
                <span>Tout le plan Pro</span>
              </li>
              <li class="flex items-center gap-2 text-secondary-600">
                <i class="pi pi-check text-primary-500" />
                <span>Génération IA illimitée</span>
              </li>
              <li class="flex items-center gap-2 text-secondary-600">
                <i class="pi pi-check text-primary-500" />
                <span>API access</span>
              </li>
              <li class="flex items-center gap-2 text-secondary-600">
                <i class="pi pi-check text-primary-500" />
                <span>Support dédié</span>
              </li>
            </ul>
            <Button
              label="Contacter"
              class="w-full bg-transparent text-secondary-900 border-2 border-secondary-900 hover:bg-secondary-900 hover:text-white"
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
          <!-- Testimonial 1 -->
          <div class="bg-gray-50 rounded-2xl p-8 border border-gray-200 animate-on-scroll">
            <div class="flex items-center gap-1 mb-4">
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
            </div>
            <p class="text-secondary-600 mb-6 italic">
              "Stoflow m'a fait gagner un temps fou ! Je gérais mes annonces sur 3 plateformes, c'était un cauchemar. Maintenant tout est centralisé."
            </p>
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-secondary-900 rounded-full flex items-center justify-center">
                <span class="text-white font-bold">ML</span>
              </div>
              <div>
                <div class="font-bold text-secondary-900">Marie L.</div>
                <div class="text-sm text-secondary-700">Vendeuse Vinted</div>
              </div>
            </div>
          </div>

          <!-- Testimonial 2 -->
          <div class="bg-gray-50 rounded-2xl p-8 border border-gray-200 animate-on-scroll animation-delay-200">
            <div class="flex items-center gap-1 mb-4">
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
            </div>
            <p class="text-secondary-600 mb-6 italic">
              "La génération de descriptions par IA est bluffante. Mes annonces sont plus pro et je vends plus vite. ROI immédiat !"
            </p>
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-secondary-900 rounded-full flex items-center justify-center">
                <span class="text-white font-bold">TD</span>
              </div>
              <div>
                <div class="font-bold text-secondary-900">Thomas D.</div>
                <div class="text-sm text-secondary-700">Vendeur eBay Pro</div>
              </div>
            </div>
          </div>

          <!-- Testimonial 3 -->
          <div class="bg-gray-50 rounded-2xl p-8 border border-gray-200 animate-on-scroll animation-delay-400">
            <div class="flex items-center gap-1 mb-4">
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
              <i class="pi pi-star-fill text-primary-400" />
            </div>
            <p class="text-secondary-600 mb-6 italic">
              "Enfin une solution qui comprend les besoins des vendeurs multi-plateformes. L'équipe est réactive et les mises à jour fréquentes."
            </p>
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-secondary-900 rounded-full flex items-center justify-center">
                <span class="text-white font-bold">SB</span>
              </div>
              <div>
                <div class="font-bold text-secondary-900">Sophie B.</div>
                <div class="text-sm text-secondary-700">Créatrice Etsy</div>
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
              class="w-full flex items-center justify-between p-6 text-left bg-white hover:bg-gray-50 transition-colors"
              @click="toggleFaq(index)"
            >
              <span class="font-bold text-secondary-900">{{ faq.question }}</span>
              <i
                :class="openFaq === index ? 'pi pi-minus' : 'pi pi-plus'"
                class="text-primary-500"
              />
            </button>
            <div
              v-show="openFaq === index"
              class="px-6 pb-6 text-secondary-600"
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
  </NuxtLayout>
</template>

<script setup lang="ts">
// Disable default layout
definePageMeta({
  layout: false
})

// FAQ data
const faqs = [
  {
    question: 'Stoflow est-il vraiment gratuit ?',
    answer: 'Oui ! Notre plan gratuit vous permet de gérer jusqu\'à 10 produits sur une marketplace sans aucun frais. C\'est parfait pour découvrir la plateforme. Pour plus de fonctionnalités, nos plans payants commencent à 19€/mois.'
  },
  {
    question: 'Comment fonctionne la connexion aux marketplaces ?',
    answer: 'Nous utilisons une extension navigateur sécurisée pour Vinted (qui n\'a pas d\'API publique) et des connexions OAuth officielles pour eBay et Etsy. Vos identifiants ne transitent jamais par nos serveurs.'
  },
  {
    question: 'Mes données sont-elles sécurisées ?',
    answer: 'Absolument. Nous utilisons un chiffrement de niveau bancaire (AES-256) pour toutes vos données. Nos serveurs sont hébergés en Europe et nous sommes 100% conformes RGPD.'
  },
  {
    question: 'Puis-je annuler à tout moment ?',
    answer: 'Oui, vous pouvez annuler votre abonnement à tout moment depuis votre espace client. Pas de période d\'engagement, pas de frais cachés. Vous gardez l\'accès jusqu\'à la fin de votre période payée.'
  },
  {
    question: 'La génération IA est-elle incluse ?',
    answer: 'La génération de descriptions par IA est incluse dans les plans Pro (100 générations/mois) et Business (illimité). Le plan gratuit n\'inclut pas cette fonctionnalité.'
  }
]

const openFaq = ref<number | null>(null)

const toggleFaq = (index: number) => {
  openFaq.value = openFaq.value === index ? null : index
}

// Scroll animation observer
onMounted(() => {
  // Small delay to ensure DOM is ready
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

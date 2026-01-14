<template>
  <div>
    <LayoutHeaderPublic />

    <main class="min-h-screen bg-gray-50 pt-24 pb-16">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <!-- Header -->
        <div class="text-center mb-12">
          <h1 class="text-4xl font-bold text-secondary-900 mb-4">
            Informations Légales
          </h1>
          <p class="text-xl text-gray-600">
            Retrouvez toutes les informations légales relatives à l'utilisation de StoFlow.
          </p>
        </div>

        <!-- Legal Pages Grid -->
        <div class="grid md:grid-cols-2 gap-6">
          <!-- Mentions légales -->
          <NuxtLink
            to="/legal/mentions"
            class="block bg-white rounded-xl p-6 border-2 border-gray-200 hover:border-primary-400 hover:shadow-lg transition-all duration-300"
          >
            <div class="flex items-start gap-4">
              <div class="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <i class="pi pi-building text-primary-600 text-xl" />
              </div>
              <div>
                <h2 class="text-xl font-bold text-secondary-900 mb-2">Mentions légales</h2>
                <p class="text-gray-600">
                  Informations sur l'éditeur du site, l'hébergeur et le directeur de publication.
                </p>
              </div>
            </div>
          </NuxtLink>

          <!-- CGU -->
          <NuxtLink
            to="/legal/cgu"
            class="block bg-white rounded-xl p-6 border-2 border-gray-200 hover:border-primary-400 hover:shadow-lg transition-all duration-300"
          >
            <div class="flex items-start gap-4">
              <div class="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <i class="pi pi-file text-primary-600 text-xl" />
              </div>
              <div>
                <h2 class="text-xl font-bold text-secondary-900 mb-2">Conditions Générales d'Utilisation</h2>
                <p class="text-gray-600">
                  Règles d'utilisation du service StoFlow, droits et obligations des utilisateurs.
                </p>
              </div>
            </div>
          </NuxtLink>

          <!-- CGV -->
          <NuxtLink
            to="/legal/cgv"
            class="block bg-white rounded-xl p-6 border-2 border-gray-200 hover:border-primary-400 hover:shadow-lg transition-all duration-300"
          >
            <div class="flex items-start gap-4">
              <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <i class="pi pi-shopping-cart text-green-600 text-xl" />
              </div>
              <div>
                <h2 class="text-xl font-bold text-secondary-900 mb-2">Conditions Générales de Vente</h2>
                <p class="text-gray-600">
                  Modalités d'abonnement, paiement, résiliation et droit de rétractation.
                </p>
              </div>
            </div>
          </NuxtLink>

          <!-- Privacy -->
          <NuxtLink
            to="/legal/privacy"
            class="block bg-white rounded-xl p-6 border-2 border-gray-200 hover:border-primary-400 hover:shadow-lg transition-all duration-300"
          >
            <div class="flex items-start gap-4">
              <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <i class="pi pi-shield text-purple-600 text-xl" />
              </div>
              <div>
                <h2 class="text-xl font-bold text-secondary-900 mb-2">Politique de Confidentialité</h2>
                <p class="text-gray-600">
                  Protection de vos données personnelles, cookies et vos droits RGPD.
                </p>
              </div>
            </div>
          </NuxtLink>
        </div>

        <!-- Contact -->
        <div class="mt-12 text-center">
          <p class="text-gray-600">
            Une question ? Contactez-nous à
            <a href="mailto:contact@stoflow.io" class="text-primary-600 hover:underline font-medium">
              contact@stoflow.io
            </a>
          </p>
        </div>
      </div>
    </main>

    <LayoutFooterFull />
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

useSeoMeta({
  title: 'Informations Légales - StoFlow',
  description: 'Mentions légales, CGU, CGV et politique de confidentialité de StoFlow.'
})
</script>

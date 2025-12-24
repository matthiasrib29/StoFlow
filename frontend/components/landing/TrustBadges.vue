<template>
  <section class="py-8 bg-gray-50 border-y border-gray-100">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex flex-wrap justify-center items-center gap-6 md:gap-12">
        <!-- RGPD Compliant -->
        <div class="flex items-center gap-2 text-secondary-600">
          <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm border border-gray-200">
            <i class="pi pi-shield text-green-600 text-xl" />
          </div>
          <div class="text-sm">
            <div class="font-semibold text-secondary-900">Conforme RGPD</div>
            <div class="text-secondary-500 text-xs">Protection des données</div>
          </div>
        </div>

        <!-- Hosted in France -->
        <div class="flex items-center gap-2 text-secondary-600">
          <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm border border-gray-200">
            <span class="text-xl">🇫🇷</span>
          </div>
          <div class="text-sm">
            <div class="font-semibold text-secondary-900">Hébergé en France</div>
            <div class="text-secondary-500 text-xs">Serveurs OVH</div>
          </div>
        </div>

        <!-- Encryption -->
        <div class="flex items-center gap-2 text-secondary-600">
          <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm border border-gray-200">
            <i class="pi pi-lock text-green-600 text-xl" />
          </div>
          <div class="text-sm">
            <div class="font-semibold text-secondary-900">Chiffrement AES-256</div>
            <div class="text-secondary-500 text-xs">Sécurité bancaire</div>
          </div>
        </div>

        <!-- Stripe Partner (optional) -->
        <div class="flex items-center gap-2 text-secondary-600">
          <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm border border-gray-200">
            <i class="pi pi-credit-card text-indigo-500 text-xl" />
          </div>
          <div class="text-sm">
            <div class="font-semibold text-secondary-900">Paiement Stripe</div>
            <div class="text-secondary-500 text-xs">100% sécurisé</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
// Static component, no logic needed
</script>

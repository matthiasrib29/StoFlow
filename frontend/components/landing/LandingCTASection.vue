<template>
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
          @click="$emit('showDemo')"
        />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineEmits<{
  showDemo: []
}>()
</script>

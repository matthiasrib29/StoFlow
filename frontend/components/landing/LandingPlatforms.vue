<template>
  <section class="py-16 bg-white border-y border-gray-100">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <p class="text-center text-secondary-700 mb-10 text-lg">Connectez-vous à vos marketplaces préférées</p>
      <div class="flex flex-wrap justify-center items-center gap-10 md:gap-20">
        <div
          v-for="platform in platforms"
          :key="platform.name"
          class="flex items-center gap-4 opacity-70 hover:opacity-100 transition-all hover:scale-105 cursor-pointer"
        >
          <img :src="platform.logo" :alt="platform.name" class="h-10 w-auto" />
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
</template>

<script setup lang="ts">
const { showEtsyPlatform } = useFeatureFlags()

const allPlatforms = [
  { name: 'Vinted', logo: '/images/platforms/vinted-logo.png' },
  { name: 'eBay', logo: '/images/platforms/ebay-logo.png' },
  { name: 'Etsy', logo: '/images/platforms/etsy-logo.png' }
]

// PMV2: Filter out Etsy if not enabled
const platforms = computed(() => {
  if (showEtsyPlatform) return allPlatforms
  return allPlatforms.filter(p => p.name !== 'Etsy')
})
</script>

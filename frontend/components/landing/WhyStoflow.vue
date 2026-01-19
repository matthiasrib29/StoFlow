<template>
  <section class="py-20 lg:py-32 bg-white">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Section header -->
      <div class="text-center mb-16 animate-on-scroll">
        <span class="inline-block text-sm font-semibold text-secondary-700 uppercase tracking-wider mb-3">Comparatif</span>
        <h2 class="text-3xl sm:text-4xl font-bold text-secondary-900 mb-4">
          Pourquoi choisir Stoflow ?
        </h2>
        <p class="text-xl text-secondary-700 max-w-2xl mx-auto">
          La seule solution qui supporte vraiment Vinted
        </p>
      </div>

      <!-- USP Vinted callout -->
      <div class="bg-gradient-to-r from-secondary-900 to-secondary-800 rounded-2xl p-6 md:p-8 mb-12 animate-on-scroll">
        <div class="flex flex-col md:flex-row items-center gap-6">
          <div class="flex-shrink-0">
            <div class="w-16 h-16 bg-primary-400 rounded-2xl flex items-center justify-center">
              <i class="pi pi-star-fill text-secondary-900 text-2xl" />
            </div>
          </div>
          <div class="text-center md:text-left">
            <h3 class="text-xl font-bold text-white mb-2">
              Stoflow est l'une des seules solutions à supporter Vinted
            </h3>
            <p class="text-gray-400">
              Vinted n'a pas d'API publique. Grâce à notre extension navigateur sécurisée,
              vous pouvez synchroniser vos produits Vinted avec vos autres marketplaces.
            </p>
          </div>
          <div class="flex-shrink-0">
            <div class="w-12 h-12 bg-platform-vinted rounded-full flex items-center justify-center">
              <i class="pi pi-check text-white text-xl" />
            </div>
          </div>
        </div>
      </div>

      <!-- Comparison table -->
      <div class="overflow-x-auto animate-on-scroll">
        <table class="w-full">
          <thead>
            <tr class="border-b-2 border-gray-200">
              <th class="text-left py-4 px-4 text-secondary-700 font-medium">Fonctionnalité</th>
              <th class="text-center py-4 px-4">
                <div class="inline-flex items-center gap-2">
                  <div class="w-8 h-8 bg-secondary-900 rounded-lg flex items-center justify-center">
                    <span class="text-primary-400 font-bold text-sm">S</span>
                  </div>
                  <span class="font-bold text-secondary-900">Stoflow</span>
                </div>
              </th>
              <th class="text-center py-4 px-4 text-secondary-600">CrossList</th>
              <th class="text-center py-4 px-4 text-secondary-600">Autres</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, index) in comparisonData"
              :key="index"
              class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
            >
              <td class="py-4 px-4 text-secondary-900 font-medium">
                {{ row.feature }}
              </td>
              <td class="py-4 px-4 text-center">
                <span
                  v-if="row.stoflow === true"
                  class="inline-flex items-center justify-center w-8 h-8 bg-green-100 rounded-full"
                >
                  <i class="pi pi-check text-green-600" />
                </span>
                <span v-else class="text-secondary-900 font-semibold">{{ row.stoflow }}</span>
              </td>
              <td class="py-4 px-4 text-center">
                <span
                  v-if="row.crosslist === true"
                  class="inline-flex items-center justify-center w-8 h-8 bg-green-100 rounded-full"
                >
                  <i class="pi pi-check text-green-600" />
                </span>
                <span
                  v-else-if="row.crosslist === false"
                  class="inline-flex items-center justify-center w-8 h-8 bg-gray-100 rounded-full"
                >
                  <i class="pi pi-times text-gray-400" />
                </span>
                <span v-else class="text-secondary-600">{{ row.crosslist }}</span>
              </td>
              <td class="py-4 px-4 text-center">
                <span
                  v-if="row.others === true"
                  class="inline-flex items-center justify-center w-8 h-8 bg-green-100 rounded-full"
                >
                  <i class="pi pi-check text-green-600" />
                </span>
                <span
                  v-else-if="row.others === false"
                  class="inline-flex items-center justify-center w-8 h-8 bg-gray-100 rounded-full"
                >
                  <i class="pi pi-times text-gray-400" />
                </span>
                <span v-else class="text-secondary-600">{{ row.others }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- CTA -->
      <div class="text-center mt-12 animate-on-scroll">
        <Button
          label="Essayer Stoflow gratuitement"
          icon="pi pi-arrow-right"
          icon-pos="right"
          class="bg-secondary-900 hover:bg-secondary-800 text-white border-0 font-bold text-lg px-8 py-3"
          @click="navigateTo('/register')"
        />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const { showEtsyPlatform } = useFeatureFlags()

interface ComparisonRow {
  feature: string
  stoflow: boolean | string
  crosslist: boolean | string
  others: boolean | string
}

const allComparisonData: ComparisonRow[] = [
  {
    feature: 'Support Vinted',
    stoflow: true,
    crosslist: false,
    others: false
  },
  {
    feature: 'Génération IA des descriptions',
    stoflow: true,
    crosslist: false,
    others: false
  },
  {
    feature: 'Support eBay',
    stoflow: true,
    crosslist: true,
    others: true
  },
  {
    feature: 'Support Etsy',
    stoflow: true,
    crosslist: true,
    others: true
  },
  {
    feature: 'Prix à partir de',
    stoflow: '0€',
    crosslist: '29€',
    others: '39€'
  },
  {
    feature: 'Hébergement EU / RGPD',
    stoflow: true,
    crosslist: false,
    others: false
  },
  {
    feature: 'Messagerie unifiée',
    stoflow: true,
    crosslist: false,
    others: false
  }
]

// PMV2: Filter out Etsy row if not enabled
const comparisonData = computed(() => {
  if (showEtsyPlatform) return allComparisonData
  return allComparisonData.filter(row => row.feature !== 'Support Etsy')
})
</script>

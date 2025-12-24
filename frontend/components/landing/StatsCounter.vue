<template>
  <section ref="sectionRef" class="py-12 bg-secondary-900">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-4">
        <!-- Stat 1: Vendeurs actifs -->
        <div class="text-center">
          <div class="flex items-center justify-center gap-1">
            <span class="text-4xl md:text-5xl font-bold text-white">+</span>
            <span class="text-4xl md:text-5xl font-bold text-primary-400">
              {{ sellersCount }}
            </span>
          </div>
          <p class="text-gray-400 mt-2 text-lg">vendeurs actifs</p>
        </div>

        <!-- Stat 2: Produits synchronisés -->
        <div class="text-center">
          <div class="flex items-center justify-center gap-1">
            <span class="text-4xl md:text-5xl font-bold text-primary-400">
              {{ productsCount.toLocaleString('fr-FR') }}
            </span>
            <span class="text-4xl md:text-5xl font-bold text-white">+</span>
          </div>
          <p class="text-gray-400 mt-2 text-lg">produits synchronisés</p>
        </div>

        <!-- Stat 3: Satisfaction -->
        <div class="text-center">
          <div class="flex items-center justify-center gap-1">
            <span class="text-4xl md:text-5xl font-bold text-primary-400">
              {{ satisfactionCount }}
            </span>
            <span class="text-4xl md:text-5xl font-bold text-white">%</span>
          </div>
          <p class="text-gray-400 mt-2 text-lg">de satisfaction</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useCountUp } from '~/composables/useCountUp'

const sectionRef = ref<HTMLElement | null>(null)
const hasAnimated = ref(false)

// Target values
const SELLERS_TARGET = 500
const PRODUCTS_TARGET = 15000
const SATISFACTION_TARGET = 98

// Count up states (start at 0, don't auto-start)
const { displayValue: sellersCount, animate: animateSellers } = useCountUp(SELLERS_TARGET, {
  autoStart: false,
  duration: 2000
})

const { displayValue: productsCount, animate: animateProducts } = useCountUp(PRODUCTS_TARGET, {
  autoStart: false,
  duration: 2500
})

const { displayValue: satisfactionCount, animate: animateSatisfaction } = useCountUp(SATISFACTION_TARGET, {
  autoStart: false,
  duration: 1800
})

onMounted(() => {
  if (!sectionRef.value) return

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !hasAnimated.value) {
          hasAnimated.value = true
          // Start all animations with slight delays
          animateSellers(SELLERS_TARGET)
          setTimeout(() => animateProducts(PRODUCTS_TARGET), 200)
          setTimeout(() => animateSatisfaction(SATISFACTION_TARGET), 400)
          observer.disconnect()
        }
      })
    },
    { threshold: 0.3 }
  )

  observer.observe(sectionRef.value)
})
</script>

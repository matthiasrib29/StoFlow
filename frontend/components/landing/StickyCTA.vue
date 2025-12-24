<template>
  <Transition name="slide-up">
    <div
      v-if="isVisible"
      class="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-white border-t-2 border-gray-100 shadow-lg p-4 safe-area-bottom"
    >
      <Button
        label="Essai gratuit 14 jours"
        icon="pi pi-arrow-right"
        icon-pos="right"
        class="w-full bg-secondary-900 hover:bg-secondary-800 text-white border-0 font-bold py-3"
        @click="navigateTo('/register')"
      />
    </div>
  </Transition>
</template>

<script setup lang="ts">
const isVisible = ref(false)
const heroHeight = ref(0)

onMounted(() => {
  // Get hero section height
  const heroSection = document.querySelector('section')
  if (heroSection) {
    heroHeight.value = heroSection.offsetHeight
  }

  // Show sticky CTA after scrolling past hero
  const handleScroll = () => {
    const scrollY = window.scrollY
    isVisible.value = scrollY > heroHeight.value * 0.5
  }

  window.addEventListener('scroll', handleScroll, { passive: true })

  onUnmounted(() => {
    window.removeEventListener('scroll', handleScroll)
  })
})
</script>

<style scoped>
.safe-area-bottom {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease-out, opacity 0.3s ease-out;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>

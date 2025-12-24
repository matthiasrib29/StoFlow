<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="isVisible"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm"
          @click="closePopup"
        />

        <!-- Modal -->
        <div class="relative bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 animate-bounce-in">
          <!-- Close button -->
          <button
            class="absolute top-4 right-4 w-8 h-8 flex items-center justify-center text-secondary-400 hover:text-secondary-900 transition-colors"
            @click="closePopup"
          >
            <i class="pi pi-times text-xl" />
          </button>

          <!-- Content -->
          <div class="text-center">
            <!-- Gift icon -->
            <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <span class="text-3xl">🎁</span>
            </div>

            <h3 class="text-2xl font-bold text-secondary-900 mb-3">
              Attendez !
            </h3>

            <p class="text-secondary-600 mb-6">
              Obtenez <strong class="text-secondary-900">20% de réduction</strong> sur votre premier mois Pro
            </p>

            <!-- Promo code -->
            <div class="bg-gray-100 rounded-xl p-4 mb-6 flex items-center justify-center gap-3">
              <span class="text-sm text-secondary-600">Code promo :</span>
              <span class="font-mono font-bold text-lg text-secondary-900 bg-white px-3 py-1 rounded-lg border-2 border-dashed border-primary-400">
                STOFLOW20
              </span>
            </div>

            <Button
              label="Récupérer mon offre"
              icon="pi pi-arrow-right"
              icon-pos="right"
              class="w-full bg-secondary-900 hover:bg-secondary-800 text-white border-0 font-bold py-3"
              @click="handleClaim"
            />

            <p class="text-xs text-secondary-400 mt-4">
              Offre valable 24h. Applicable sur le premier mois.
            </p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const isVisible = ref(false)
const hasShown = ref(false)

const STORAGE_KEY = 'stoflow_exit_popup_shown'

onMounted(() => {
  // Check if already shown in this session
  if (sessionStorage.getItem(STORAGE_KEY)) {
    hasShown.value = true
    return
  }

  // Desktop: detect mouse leave
  const handleMouseLeave = (e: MouseEvent) => {
    if (e.clientY <= 0 && !hasShown.value) {
      showPopup()
    }
  }

  // Add listener with delay to prevent immediate trigger
  setTimeout(() => {
    document.addEventListener('mouseleave', handleMouseLeave)
  }, 5000) // Wait 5 seconds before enabling

  onUnmounted(() => {
    document.removeEventListener('mouseleave', handleMouseLeave)
  })
})

const showPopup = () => {
  if (hasShown.value) return
  hasShown.value = true
  isVisible.value = true
  sessionStorage.setItem(STORAGE_KEY, 'true')
}

const closePopup = () => {
  isVisible.value = false
}

const handleClaim = () => {
  closePopup()
  navigateTo('/register?promo=STOFLOW20')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.animate-bounce-in {
  animation: bounceIn 0.5s ease-out;
}

@keyframes bounceIn {
  0% {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  60% {
    transform: scale(1.02) translateY(0);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>

<template>
  <div class="empty-state text-center py-12 px-6">
    <!-- Lottie Animation -->
    <div
      v-if="animationType !== 'none'"
      ref="animationContainer"
      class="animation-container mx-auto mb-6"
      :style="{ width: animationSize, height: animationSize }"
    />

    <!-- Fallback Icon si pas d'animation -->
    <div v-else class="fallback-icon mb-6">
      <i :class="[icon, 'text-6xl', iconColorClass]"/>
    </div>

    <!-- Title -->
    <h3 class="text-xl font-bold text-secondary-900 mb-3">
      {{ title }}
    </h3>

    <!-- Description -->
    <p class="text-gray-600 mb-6 max-w-md mx-auto">
      {{ description }}
    </p>

    <!-- Action Button -->
    <slot name="action">
      <Button
        v-if="actionLabel"
        :label="actionLabel"
        :icon="actionIcon"
        class="btn-primary"
        @click="$emit('action')"
      />
    </slot>
  </div>
</template>

<script setup lang="ts">
import lottie, { type AnimationItem } from 'lottie-web'

interface Props {
  /** Type d'animation Lottie à afficher */
  animationType?: 'empty-box' | 'no-data' | 'search' | 'folder' | 'rocket' | 'none'
  /** Taille de l'animation (défaut: 200px) */
  animationSize?: string
  /** Titre du message */
  title: string
  /** Description du message */
  description: string
  /** Label du bouton d'action */
  actionLabel?: string
  /** Icon du bouton d'action */
  actionIcon?: string
  /** Icon de fallback si pas d'animation (ex: "pi pi-inbox") */
  icon?: string
  /** Couleur de l'icon de fallback */
  iconColor?: 'primary' | 'secondary' | 'gray'
}

const props = withDefaults(defineProps<Props>(), {
  animationType: 'empty-box',
  animationSize: '200px',
  actionIcon: 'pi pi-plus',
  icon: 'pi pi-inbox',
  iconColor: 'gray'
})

defineEmits<{
  action: []
}>()

const animationContainer = ref<HTMLElement | null>(null)
let animationInstance: AnimationItem | null = null

// Mapping des types d'animation vers des URLs Lottie
const animationUrls: Record<string, string> = {
  'empty-box': 'https://lottie.host/8f5c0e5a-4b5a-4d5a-8b5a-4d5a8b5a4d5a/1234567890.json',
  'no-data': 'https://lottie.host/embed/4e5c0e5a-4b5a-4d5a-8b5a-4d5a8b5a4d5a/1234567890.json',
  'search': 'https://lottie.host/embed/2e5c0e5a-4b5a-4d5a-8b5a-4d5a8b5a4d5a/1234567890.json',
  'folder': 'https://lottie.host/embed/3e5c0e5a-4b5a-4d5a-8b5a-4d5a8b5a4d5a/1234567890.json',
  'rocket': 'https://lottie.host/embed/5e5c0e5a-4b5a-4d5a-8b5a-4d5a8b5a4d5a/1234567890.json'
}

// Animations Lottie simples en JSON inline (pour éviter les dépendances externes)
const inlineAnimations: Record<string, any> = {
  'empty-box': {
    v: '5.7.4',
    fr: 60,
    ip: 0,
    op: 120,
    w: 400,
    h: 400,
    nm: 'Empty Box',
    ddd: 0,
    assets: [],
    layers: [
      {
        ddd: 0,
        ind: 1,
        ty: 4,
        nm: 'Box',
        sr: 1,
        ks: {
          o: { a: 0, k: 100 },
          r: {
            a: 1,
            k: [
              { t: 0, s: [0], e: [10] },
              { t: 60, s: [10], e: [0] },
              { t: 120, s: [0] }
            ]
          },
          p: { a: 0, k: [200, 200, 0] },
          a: { a: 0, k: [0, 0, 0] },
          s: {
            a: 1,
            k: [
              { t: 0, s: [100, 100, 100], e: [110, 110, 100] },
              { t: 60, s: [110, 110, 100], e: [100, 100, 100] },
              { t: 120, s: [100, 100, 100] }
            ]
          }
        },
        ao: 0,
        shapes: [
          {
            ty: 'rc',
            d: 1,
            s: { a: 0, k: [120, 120] },
            p: { a: 0, k: [0, 0] },
            r: { a: 0, k: 10 },
            nm: 'Rectangle'
          },
          {
            ty: 'st',
            c: { a: 0, k: [0.929, 0.765, 0.298, 1] },
            o: { a: 0, k: 100 },
            w: { a: 0, k: 8 },
            lc: 2,
            lj: 2,
            nm: 'Stroke'
          }
        ],
        ip: 0,
        op: 120,
        st: 0,
        bm: 0
      }
    ]
  }
}

const iconColorClass = computed(() => {
  switch (props.iconColor) {
    case 'primary':
      return 'text-primary-400'
    case 'secondary':
      return 'text-secondary-400'
    case 'gray':
    default:
      return 'text-gray-400'
  }
})

onMounted(() => {
  if (props.animationType !== 'none' && animationContainer.value) {
    // Utiliser l'animation inline si disponible, sinon fallback
    const animationData = inlineAnimations[props.animationType]

    if (animationData) {
      animationInstance = lottie.loadAnimation({
        container: animationContainer.value,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        animationData: animationData
      })
    }
  }
})

onUnmounted(() => {
  if (animationInstance) {
    animationInstance.destroy()
  }
})
</script>

<style scoped>
.empty-state {
  @apply transition-all duration-300;
}

.animation-container {
  @apply opacity-60;
  filter: grayscale(20%);
}

.fallback-icon {
  @apply transition-transform duration-300;
}

.empty-state:hover .fallback-icon {
  @apply scale-110;
}
</style>

<template>
  <Transition name="success-fade">
    <div v-if="visible" class="success-animation-wrapper">
      <div :class="['success-animation', sizeClass, variantClass]">
        <!-- SVG Checkmark animé -->
        <svg
          class="checkmark"
          xmlns="http://www.w3.org/2000/svg"
          :viewBox="`0 0 ${svgSize} ${svgSize}`"
        >
          <circle
            class="checkmark-circle"
            :cx="svgSize / 2"
            :cy="svgSize / 2"
            :r="svgSize / 2 - 4"
            fill="none"
            :stroke-width="strokeWidth"
          />
          <path
            class="checkmark-check"
            fill="none"
            :stroke-width="strokeWidth"
            :d="checkPath"
            stroke-linecap="round"
          />
        </svg>

        <!-- Message -->
        <div v-if="message" class="success-message">
          {{ message }}
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
interface Props {
  /** Afficher ou masquer l'animation */
  visible?: boolean
  /** Message à afficher */
  message?: string
  /** Taille de l'animation */
  size?: 'small' | 'medium' | 'large'
  /** Variante de couleur */
  variant?: 'success' | 'primary' | 'info'
  /** Durée d'affichage automatique en ms (0 = infini) */
  duration?: number
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  size: 'medium',
  variant: 'success',
  duration: 3000
})

const emit = defineEmits<{
  hide: []
}>()

// Taille du SVG selon le prop size
const svgSize = computed(() => {
  switch (props.size) {
    case 'small': return 32
    case 'large': return 80
    case 'medium':
    default: return 52
  }
})

const strokeWidth = computed(() => {
  switch (props.size) {
    case 'small': return 2
    case 'large': return 4
    case 'medium':
    default: return 3
  }
})

// Path du checkmark adapté à la taille
const checkPath = computed(() => {
  const size = svgSize.value
  const padding = size * 0.25
  const start = { x: padding, y: size / 2 }
  const middle = { x: size * 0.4, y: size - padding }
  const end = { x: size - padding, y: padding }
  return `M ${start.x} ${start.y} L ${middle.x} ${middle.y} L ${end.x} ${end.y}`
})

const sizeClass = computed(() => `success-animation--${props.size}`)
const variantClass = computed(() => `success-animation--${props.variant}`)

// Auto-hide après duration
let hideTimeout: ReturnType<typeof setTimeout> | null = null

watch(() => props.visible, (newVal) => {
  if (newVal && props.duration > 0) {
    // Nettoyer le timeout précédent
    if (hideTimeout) clearTimeout(hideTimeout)

    // Nouveau timeout
    hideTimeout = setTimeout(() => {
      emit('hide')
    }, props.duration)
  }
})

onUnmounted(() => {
  if (hideTimeout) clearTimeout(hideTimeout)
})
</script>

<style scoped>
.success-animation-wrapper {
  @apply inline-flex items-center justify-center;
}

.success-animation {
  @apply flex flex-col items-center gap-2 p-4 rounded-lg;
  animation: bounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

/* Sizes */
.success-animation--small {
  @apply p-2 gap-1;
}

.success-animation--medium {
  @apply p-4 gap-2;
}

.success-animation--large {
  @apply p-6 gap-3;
}

/* Variants */
.success-animation--success .checkmark-circle {
  stroke: #22c55e;
}

.success-animation--success .checkmark-check {
  stroke: #22c55e;
}

.success-animation--primary .checkmark-circle {
  stroke: var(--primary-400);
}

.success-animation--primary .checkmark-check {
  stroke: var(--primary-400);
}

.success-animation--info .checkmark-circle {
  stroke: #3b82f6;
}

.success-animation--info .checkmark-check {
  stroke: #3b82f6;
}

/* SVG Animations */
.checkmark {
  @apply block;
}

.checkmark-circle {
  stroke-dasharray: 166;
  stroke-dashoffset: 166;
  animation: stroke-circle 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}

.checkmark-check {
  stroke-dasharray: 48;
  stroke-dashoffset: 48;
  animation: stroke-check 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.4s forwards;
}

@keyframes stroke-circle {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes stroke-check {
  to {
    stroke-dashoffset: 0;
  }
}

/* Message */
.success-message {
  @apply text-sm font-medium text-secondary-900 text-center;
}

.success-animation--small .success-message {
  @apply text-xs;
}

.success-animation--large .success-message {
  @apply text-base;
}

/* Transition */
.success-fade-enter-active,
.success-fade-leave-active {
  transition: all 0.3s ease;
}

.success-fade-enter-from {
  opacity: 0;
  transform: scale(0.8);
}

.success-fade-leave-to {
  opacity: 0;
  transform: scale(0.8);
}
</style>

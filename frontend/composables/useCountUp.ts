import { ref, watch, onMounted, type Ref } from 'vue'

/**
 * Composable pour animer un compteur de 0 à une valeur cible
 *
 * @example
 * ```typescript
 * const { displayValue, animate } = useCountUp(127, { duration: 1500 })
 * // displayValue va compter: 0 → 127 en 1.5 secondes
 * ```
 */
export interface CountUpOptions {
  /** Durée de l'animation en ms (défaut: 1500) */
  duration?: number
  /** Délai avant de démarrer l'animation en ms (défaut: 0) */
  delay?: number
  /** Fonction d'easing (défaut: easeOutExpo) */
  easing?: (t: number) => number
  /** Démarrer automatiquement au montage (défaut: true) */
  autoStart?: boolean
  /** Nombre de décimales pour l'affichage (défaut: 0) */
  decimals?: number
}

/**
 * Fonction d'easing par défaut - Exponentielle décroissante
 */
const easeOutExpo = (t: number): number => {
  return t === 1 ? 1 : 1 - Math.pow(2, -10 * t)
}

export function useCountUp(
  target: Ref<number> | number,
  options: CountUpOptions = {}
) {
  const {
    duration = 1500,
    delay = 0,
    easing = easeOutExpo,
    autoStart = true,
    decimals = 0
  } = options

  const displayValue = ref(0)
  const isAnimating = ref(false)

  let animationFrameId: number | null = null

  /**
   * Lance l'animation du compteur
   */
  const animate = (targetValue: number) => {
    // Annuler l'animation précédente si elle existe
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId)
    }

    const startValue = displayValue.value
    const startTime = performance.now()
    const delta = targetValue - startValue

    isAnimating.value = true

    const step = (currentTime: number) => {
      const elapsed = currentTime - startTime - delay

      if (elapsed < 0) {
        // En attente du délai
        animationFrameId = requestAnimationFrame(step)
        return
      }

      const progress = Math.min(elapsed / duration, 1)
      const easedProgress = easing(progress)

      displayValue.value = Number((startValue + delta * easedProgress).toFixed(decimals))

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(step)
      } else {
        // Animation terminée
        displayValue.value = Number(targetValue.toFixed(decimals))
        isAnimating.value = false
        animationFrameId = null
      }
    }

    animationFrameId = requestAnimationFrame(step)
  }

  /**
   * Réinitialise le compteur à 0
   */
  const reset = () => {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId)
      animationFrameId = null
    }
    displayValue.value = 0
    isAnimating.value = false
  }

  // Observer les changements de la valeur cible si c'est une ref
  if (typeof target !== 'number') {
    watch(target, (newValue) => {
      animate(newValue)
    })
  }

  // Démarrer automatiquement au montage si demandé
  onMounted(() => {
    if (autoStart) {
      const targetValue = typeof target === 'number' ? target : target.value
      setTimeout(() => animate(targetValue), 0)
    }
  })

  // Nettoyer à la destruction
  onUnmounted(() => {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId)
    }
  })

  return {
    displayValue,
    isAnimating,
    animate,
    reset
  }
}

/**
 * Fonctions d'easing alternatives disponibles
 */
export const easingFunctions = {
  // Linéaire
  linear: (t: number) => t,

  // Quadratique
  easeInQuad: (t: number) => t * t,
  easeOutQuad: (t: number) => t * (2 - t),
  easeInOutQuad: (t: number) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),

  // Cubique
  easeInCubic: (t: number) => t * t * t,
  easeOutCubic: (t: number) => (--t) * t * t + 1,
  easeInOutCubic: (t: number) =>
    t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,

  // Exponentielle
  easeInExpo: (t: number) => (t === 0 ? 0 : Math.pow(2, 10 * (t - 1))),
  easeOutExpo: (t: number) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  easeInOutExpo: (t: number) => {
    if (t === 0 || t === 1) return t
    if (t < 0.5) return Math.pow(2, 20 * t - 10) / 2
    return (2 - Math.pow(2, -20 * t + 10)) / 2
  }
}

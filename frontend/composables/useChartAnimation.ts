import { ref, type Ref } from 'vue'

/**
 * Composable pour animer les valeurs de graphiques/charts
 * Anime progressivement les données pour un effet visuel fluide
 *
 * @example
 * ```typescript
 * const { animatedData, animateChart } = useChartAnimation()
 *
 * // Animer les données
 * animateChart([10, 20, 30, 40], { duration: 1000 })
 *
 * // Utiliser dans chart: animatedData.value
 * ```
 */

export interface ChartAnimationOptions {
  /** Durée de l'animation en ms (défaut: 1000) */
  duration?: number
  /** Délai avant de démarrer en ms (défaut: 0) */
  delay?: number
  /** Fonction d'easing */
  easing?: (t: number) => number
  /** Animer séquentiellement (true) ou en parallèle (false) */
  stagger?: boolean
  /** Délai entre chaque élément si stagger=true (ms) */
  staggerDelay?: number
}

const easeOutQuart = (t: number): number => {
  return 1 - Math.pow(1 - t, 4)
}

export function useChartAnimation<T extends number | number[]>(initialData?: T) {
  const animatedData = ref<T>(initialData ?? ([] as any)) as Ref<T>
  const isAnimating = ref(false)

  let animationFrameId: number | null = null

  /**
   * Anime un tableau de nombres de 0 vers les valeurs cibles
   */
  const animateChart = (
    targetData: number[],
    options: ChartAnimationOptions = {}
  ): Promise<void> => {
    return new Promise((resolve) => {
      const {
        duration = 1000,
        delay = 0,
        easing = easeOutQuart,
        stagger = false,
        staggerDelay = 50
      } = options

      // Annuler l'animation précédente
      if (animationFrameId !== null) {
        cancelAnimationFrame(animationFrameId)
      }

      // Initialiser à 0 si pas déjà défini
      const startData = (animatedData.value as number[]).length === targetData.length
        ? (animatedData.value as number[]).slice()
        : Array(targetData.length).fill(0)

      const deltas = targetData.map((target, i) => target - startData[i])
      const startTime = performance.now()
      isAnimating.value = true

      const step = (currentTime: number) => {
        const elapsed = currentTime - startTime - delay

        if (elapsed < 0) {
          // En attente du délai
          animationFrameId = requestAnimationFrame(step)
          return
        }

        if (stagger) {
          // Animation séquentielle (stagger)
          const updatedData = startData.map((start, index) => {
            const itemDelay = index * staggerDelay
            const itemElapsed = Math.max(0, elapsed - itemDelay)
            const progress = Math.min(itemElapsed / duration, 1)
            const easedProgress = easing(progress)
            return start + deltas[index] * easedProgress
          })

          animatedData.value = updatedData as T

          // Vérifier si tous les éléments sont terminés
          const allComplete = targetData.every(
            (target, i) => Math.abs((animatedData.value as number[])[i] - target) < 0.01
          )

          if (allComplete || elapsed >= duration + targetData.length * staggerDelay) {
            animatedData.value = targetData as T
            isAnimating.value = false
            resolve()
          } else {
            animationFrameId = requestAnimationFrame(step)
          }
        } else {
          // Animation parallèle (tous en même temps)
          const progress = Math.min(elapsed / duration, 1)
          const easedProgress = easing(progress)

          const updatedData = startData.map((start, index) => {
            return start + deltas[index] * easedProgress
          })

          animatedData.value = updatedData as T

          if (progress < 1) {
            animationFrameId = requestAnimationFrame(step)
          } else {
            animatedData.value = targetData as T
            isAnimating.value = false
            resolve()
          }
        }
      }

      animationFrameId = requestAnimationFrame(step)
    })
  }

  /**
   * Anime une seule valeur
   */
  const animateValue = (
    targetValue: number,
    options: ChartAnimationOptions = {}
  ): Promise<void> => {
    return animateChart([targetValue], options).then(() => {
      // Extraire la valeur unique
      animatedData.value = (animatedData.value as number[])[0] as T
    })
  }

  /**
   * Réinitialise l'animation
   */
  const reset = (value?: T) => {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId)
      animationFrameId = null
    }
    animatedData.value = value ?? ([] as any)
    isAnimating.value = false
  }

  // Nettoyer à la destruction
  onUnmounted(() => {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId)
    }
  })

  return {
    animatedData,
    isAnimating,
    animateChart,
    animateValue,
    reset
  }
}

/**
 * Utilitaires pour animer des barres/colonnes de charts
 */
export function useBarChartAnimation() {
  const { animatedData, animateChart, isAnimating } = useChartAnimation<number[]>([])

  /**
   * Anime les hauteurs des barres
   */
  const animateBars = async (heights: number[], duration = 800) => {
    await animateChart(heights, {
      duration,
      stagger: true,
      staggerDelay: 60,
      easing: easeOutQuart
    })
  }

  return {
    barHeights: animatedData,
    isAnimating,
    animateBars
  }
}

/**
 * Utilitaires pour animer des lignes de charts
 */
export function useLineChartAnimation() {
  const { animatedData, animateChart, isAnimating } = useChartAnimation<number[]>([])

  /**
   * Anime une ligne (path drawing effect)
   */
  const animateLine = async (points: number[], duration = 1200) => {
    await animateChart(points, {
      duration,
      stagger: false, // Parallèle pour effet smooth
      easing: easeOutQuart
    })
  }

  return {
    linePoints: animatedData,
    isAnimating,
    animateLine
  }
}

import { ref, onMounted, onUnmounted, type Ref } from 'vue'

/**
 * Composable pour animer les éléments quand ils deviennent visibles au scroll
 *
 * @example
 * ```typescript
 * // Dans le composant
 * const { elementRef, isRevealed } = useScrollReveal({ threshold: 0.2 })
 *
 * // Dans le template
 * <div ref="elementRef" :class="{ 'revealed': isRevealed }">
 *   Content animé au scroll
 * </div>
 * ```
 */

export interface ScrollRevealOptions {
  /** Seuil de visibilité (0-1) pour déclencher l'animation (défaut: 0.1) */
  threshold?: number
  /** Marge autour de l'élément (px) (défaut: '0px') */
  rootMargin?: string
  /** Animation une seule fois ou à chaque fois (défaut: true) */
  once?: boolean
  /** Délai avant l'animation en ms (défaut: 0) */
  delay?: number
}

export function useScrollReveal(options: ScrollRevealOptions = {}) {
  const {
    threshold = 0.1,
    rootMargin = '0px',
    once = true,
    delay = 0
  } = options

  const elementRef = ref<HTMLElement | null>(null)
  const isRevealed = ref(false)

  let observer: IntersectionObserver | null = null

  const reveal = () => {
    if (delay > 0) {
      setTimeout(() => {
        isRevealed.value = true
      }, delay)
    } else {
      isRevealed.value = true
    }
  }

  const unreveal = () => {
    if (!once) {
      isRevealed.value = false
    }
  }

  onMounted(() => {
    if (!elementRef.value) return

    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            reveal()
            if (once && observer) {
              observer.unobserve(entry.target)
            }
          } else {
            unreveal()
          }
        })
      },
      {
        threshold,
        rootMargin
      }
    )

    observer.observe(elementRef.value)
  })

  onUnmounted(() => {
    if (observer) {
      observer.disconnect()
    }
  })

  return {
    elementRef,
    isRevealed
  }
}

/**
 * Directive pour scroll reveal (alternative au composable)
 * Usage: v-scroll-reveal ou v-scroll-reveal="{ threshold: 0.2, delay: 100 }"
 */
export const vScrollReveal = {
  mounted(el: HTMLElement, binding: any) {
    const options = binding.value || {}
    const {
      threshold = 0.1,
      rootMargin = '0px',
      once = true,
      delay = 0
    } = options

    // Ajouter la classe de base
    el.classList.add('scroll-reveal')

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            if (delay > 0) {
              setTimeout(() => {
                el.classList.add('revealed')
              }, delay)
            } else {
              el.classList.add('revealed')
            }

            if (once) {
              observer.unobserve(entry.target)
            }
          } else if (!once) {
            el.classList.remove('revealed')
          }
        })
      },
      {
        threshold,
        rootMargin
      }
    )

    observer.observe(el)

    // Stocker l'observer pour cleanup
    ;(el as any)._scrollRevealObserver = observer
  },

  unmounted(el: HTMLElement) {
    const observer = (el as any)._scrollRevealObserver
    if (observer) {
      observer.disconnect()
    }
  }
}

/**
 * Hook pour observer plusieurs éléments
 * Utile pour les listes/grids avec stagger
 */
export function useScrollRevealGroup(options: ScrollRevealOptions & { staggerDelay?: number } = {}) {
  const { staggerDelay = 100, ...scrollOptions } = options

  const containerRef = ref<HTMLElement | null>(null)
  const revealedItems = ref<Set<number>>(new Set())

  let observer: IntersectionObserver | null = null

  onMounted(() => {
    if (!containerRef.value) return

    const children = containerRef.value.children

    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const index = Array.from(children).indexOf(entry.target)
            if (index >= 0) {
              setTimeout(() => {
                entry.target.classList.add('revealed')
                revealedItems.value.add(index)
              }, index * staggerDelay)

              if (scrollOptions.once !== false) {
                observer?.unobserve(entry.target)
              }
            }
          }
        })
      },
      {
        threshold: scrollOptions.threshold || 0.1,
        rootMargin: scrollOptions.rootMargin || '0px'
      }
    )

    Array.from(children).forEach((child) => {
      child.classList.add('scroll-reveal')
      observer?.observe(child)
    })
  })

  onUnmounted(() => {
    if (observer) {
      observer.disconnect()
    }
  })

  return {
    containerRef,
    revealedItems
  }
}

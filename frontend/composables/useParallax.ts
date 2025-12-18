import { ref, onMounted, onUnmounted, type Ref } from 'vue'

/**
 * Composable pour créer des effets parallax au scroll
 *
 * @example
 * ```typescript
 * const { parallaxRef, offset, progress } = useParallax({ speed: 0.5 })
 *
 * // Dans le template avec style binding
 * <div ref="parallaxRef" :style="{ transform: `translateY(${offset}px)` }">
 *   Contenu avec effet parallax
 * </div>
 * ```
 */

export interface ParallaxOptions {
  /** Vitesse du parallax (0-1, où 0.5 = moitié de la vitesse du scroll) */
  speed?: number
  /** Direction du parallax */
  direction?: 'vertical' | 'horizontal' | 'both'
  /** Inverser l'effet */
  reverse?: boolean
  /** Limiter l'effet quand l'élément est visible */
  limitToViewport?: boolean
}

export function useParallax(options: ParallaxOptions = {}) {
  const {
    speed = 0.5,
    direction = 'vertical',
    reverse = false,
    limitToViewport = true
  } = options

  const parallaxRef = ref<HTMLElement | null>(null)
  const offset = ref(0)
  const horizontalOffset = ref(0)
  const progress = ref(0) // 0-1, progression dans le viewport

  let ticking = false

  const calculateParallax = () => {
    if (!parallaxRef.value) return

    const rect = parallaxRef.value.getBoundingClientRect()
    const windowHeight = window.innerHeight

    // Calculer la progression (0 quand en bas du viewport, 1 quand en haut)
    const elementProgress = 1 - (rect.top + rect.height) / (windowHeight + rect.height)
    progress.value = Math.max(0, Math.min(1, elementProgress))

    // Si limitToViewport, ne pas appliquer l'effet si l'élément n'est pas visible
    if (limitToViewport) {
      const isVisible = rect.top < windowHeight && rect.bottom > 0
      if (!isVisible) return
    }

    // Calculer l'offset basé sur la position de scroll
    const scrollY = window.scrollY
    const elementTop = rect.top + scrollY
    const relativeScroll = scrollY - elementTop + windowHeight / 2

    const effectSpeed = reverse ? -speed : speed
    const calculatedOffset = relativeScroll * effectSpeed

    if (direction === 'vertical' || direction === 'both') {
      offset.value = calculatedOffset
    }
    if (direction === 'horizontal' || direction === 'both') {
      horizontalOffset.value = calculatedOffset
    }

    ticking = false
  }

  const handleScroll = () => {
    if (!ticking) {
      requestAnimationFrame(calculateParallax)
      ticking = true
    }
  }

  onMounted(() => {
    window.addEventListener('scroll', handleScroll, { passive: true })
    calculateParallax() // Calcul initial
  })

  onUnmounted(() => {
    window.removeEventListener('scroll', handleScroll)
  })

  return {
    parallaxRef,
    offset,
    horizontalOffset,
    progress
  }
}

/**
 * Parallax avec effet de perspective 3D
 */
export function useParallax3D(options: { intensity?: number } = {}) {
  const { intensity = 10 } = options

  const containerRef = ref<HTMLElement | null>(null)
  const rotateX = ref(0)
  const rotateY = ref(0)
  const scale = ref(1)

  const handleMouseMove = (event: MouseEvent) => {
    if (!containerRef.value) return

    const rect = containerRef.value.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2

    const mouseX = event.clientX - centerX
    const mouseY = event.clientY - centerY

    rotateY.value = (mouseX / rect.width) * intensity
    rotateX.value = -(mouseY / rect.height) * intensity
  }

  const handleMouseEnter = () => {
    scale.value = 1.02
  }

  const handleMouseLeave = () => {
    rotateX.value = 0
    rotateY.value = 0
    scale.value = 1
  }

  onMounted(() => {
    if (containerRef.value) {
      containerRef.value.addEventListener('mousemove', handleMouseMove)
      containerRef.value.addEventListener('mouseenter', handleMouseEnter)
      containerRef.value.addEventListener('mouseleave', handleMouseLeave)
    }
  })

  onUnmounted(() => {
    if (containerRef.value) {
      containerRef.value.removeEventListener('mousemove', handleMouseMove)
      containerRef.value.removeEventListener('mouseenter', handleMouseEnter)
      containerRef.value.removeEventListener('mouseleave', handleMouseLeave)
    }
  })

  const transform = computed(() =>
    `perspective(1000px) rotateX(${rotateX.value}deg) rotateY(${rotateY.value}deg) scale(${scale.value})`
  )

  return {
    containerRef,
    rotateX,
    rotateY,
    scale,
    transform
  }
}

/**
 * Effet de parallax sur le curseur (fond qui suit le curseur)
 */
export function useMouseParallax(options: { sensitivity?: number } = {}) {
  const { sensitivity = 20 } = options

  const mouseX = ref(0)
  const mouseY = ref(0)

  const handleMouseMove = (event: MouseEvent) => {
    const centerX = window.innerWidth / 2
    const centerY = window.innerHeight / 2

    mouseX.value = (event.clientX - centerX) / sensitivity
    mouseY.value = (event.clientY - centerY) / sensitivity
  }

  onMounted(() => {
    window.addEventListener('mousemove', handleMouseMove, { passive: true })
  })

  onUnmounted(() => {
    window.removeEventListener('mousemove', handleMouseMove)
  })

  const backgroundTransform = computed(() =>
    `translate(${mouseX.value}px, ${mouseY.value}px)`
  )

  return {
    mouseX,
    mouseY,
    backgroundTransform
  }
}

/**
 * Composable pour gérer les meta tags SEO de manière centralisée
 *
 * Usage:
 * ```ts
 * useSeoHead({
 *   title: 'Ma Page',
 *   description: 'Description de ma page',
 *   ogImage: '/images/og-custom.jpg',
 *   noindex: true // Pour les pages privées
 * })
 * ```
 */

interface SeoHeadOptions {
  /** Titre de la page (sera suffixé par " - Stoflow") */
  title: string
  /** Meta description (150-160 caractères recommandés) */
  description: string
  /** URL de l'image Open Graph (optionnel, utilise l'image par défaut si omis) */
  ogImage?: string
  /** Type Open Graph (website, article, etc.) */
  ogType?: string
  /** Empêcher l'indexation (pour pages privées) */
  noindex?: boolean
}

export const useSeoHead = (options: SeoHeadOptions) => {
  const {
    title,
    description,
    ogImage = '/images/og-stoflow.jpg',
    ogType = 'website',
    noindex = false
  } = options

  const fullTitle = `${title} - Stoflow`

  useHead({
    title: fullTitle,
    meta: [
      // Meta description
      { name: 'description', content: description },

      // Open Graph
      { property: 'og:title', content: fullTitle },
      { property: 'og:description', content: description },
      { property: 'og:type', content: ogType },
      { property: 'og:image', content: ogImage },

      // Twitter Card
      { name: 'twitter:title', content: fullTitle },
      { name: 'twitter:description', content: description },
      { name: 'twitter:image', content: ogImage },

      // Robots (noindex pour pages privées)
      ...(noindex ? [{ name: 'robots', content: 'noindex, nofollow' }] : []),
    ]
  })
}

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
  /** Override canonical URL path (defaults to current route) */
  canonicalPath?: string
}

export const useSeoHead = (options: SeoHeadOptions) => {
  const {
    title,
    description,
    ogImage = '/images/og-stoflow.jpg',
    ogType = 'website',
    noindex = false,
    canonicalPath
  } = options

  const route = useRoute()
  const fullTitle = `${title} - Stoflow`
  const canonicalUrl = `https://www.stoflow.io${canonicalPath || route.path}`

  useHead({
    title: fullTitle,
    link: [
      { rel: 'canonical', href: canonicalUrl }
    ],
    meta: [
      // Meta description
      { name: 'description', content: description },

      // Open Graph
      { property: 'og:title', content: fullTitle },
      { property: 'og:description', content: description },
      { property: 'og:type', content: ogType },
      { property: 'og:image', content: ogImage },
      { property: 'og:url', content: canonicalUrl },

      // Twitter Card
      { name: 'twitter:title', content: fullTitle },
      { name: 'twitter:description', content: description },
      { name: 'twitter:image', content: ogImage },

      // Robots (noindex pour pages privées)
      ...(noindex ? [{ name: 'robots', content: 'noindex, nofollow' }] : []),
    ]
  })
}

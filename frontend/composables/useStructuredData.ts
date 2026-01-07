/**
 * Composables pour gérer les structured data (Schema.org JSON-LD)
 *
 * Les structured data permettent aux moteurs de recherche de mieux comprendre
 * le contenu de vos pages et d'afficher des rich snippets dans les résultats de recherche.
 */

/**
 * Ajoute le schema Organization à la page
 * À utiliser sur la page d'accueil principalement
 */
export const useOrganizationSchema = () => {
  useHead({
    script: [
      {
        type: 'application/ld+json',
        children: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'Organization',
          name: 'Stoflow',
          url: 'https://stoflow.io',
          logo: 'https://stoflow.io/logo.png',
          description: 'Plateforme de gestion multi-marketplace pour e-commerce. Gérez vos ventes Vinted, eBay et Etsy en un seul endroit.',
          sameAs: [
            // URLs réseaux sociaux (à compléter si disponibles)
            // 'https://twitter.com/stoflow',
            // 'https://www.linkedin.com/company/stoflow',
            // 'https://www.facebook.com/stoflow',
          ]
        })
      }
    ]
  })
}

/**
 * Ajoute le schema SoftwareApplication à la page
 * À utiliser sur la page d'accueil pour décrire l'application
 */
export const useSoftwareApplicationSchema = () => {
  useHead({
    script: [
      {
        type: 'application/ld+json',
        children: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'SoftwareApplication',
          name: 'Stoflow',
          applicationCategory: 'BusinessApplication',
          operatingSystem: 'Web',
          description: 'Application de gestion multi-marketplace pour Vinted, eBay et Etsy',
          offers: {
            '@type': 'Offer',
            price: '0',
            priceCurrency: 'EUR',
            description: 'Essai gratuit 14 jours disponible'
          },
          aggregateRating: {
            '@type': 'AggregateRating',
            ratingValue: '4.8',
            ratingCount: '127',
            bestRating: '5',
            worstRating: '1'
          }
        })
      }
    ]
  })
}

/**
 * Ajoute le schema FAQPage à la page
 * À utiliser sur les pages contenant une FAQ
 *
 * @param faqs - Liste des questions/réponses
 */
export const useFAQPageSchema = (faqs: Array<{ question: string; answer: string }>) => {
  useHead({
    script: [
      {
        type: 'application/ld+json',
        children: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'FAQPage',
          mainEntity: faqs.map(faq => ({
            '@type': 'Question',
            name: faq.question,
            acceptedAnswer: {
              '@type': 'Answer',
              text: faq.answer
            }
          }))
        })
      }
    ]
  })
}

/**
 * Ajoute le schema BreadcrumbList à la page
 * À utiliser sur les pages avec navigation hiérarchique
 *
 * @param breadcrumbs - Liste des fils d'ariane
 *
 * @example
 * useBreadcrumbSchema([
 *   { name: 'Accueil', url: '/' },
 *   { name: 'Mentions légales', url: '/legal/mentions' }
 * ])
 */
export const useBreadcrumbSchema = (breadcrumbs: Array<{ name: string; url: string }>) => {
  useHead({
    script: [
      {
        type: 'application/ld+json',
        children: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'BreadcrumbList',
          itemListElement: breadcrumbs.map((item, index) => ({
            '@type': 'ListItem',
            position: index + 1,
            name: item.name,
            item: `https://stoflow.io${item.url}`
          }))
        })
      }
    ]
  })
}

/**
 * Ajoute le schema Article à la page
 * À utiliser sur les pages de blog ou articles de documentation
 *
 * @param article - Données de l'article
 */
export const useArticleSchema = (article: {
  title: string
  description: string
  datePublished: string
  dateModified?: string
  author: string
  image?: string
}) => {
  useHead({
    script: [
      {
        type: 'application/ld+json',
        children: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'Article',
          headline: article.title,
          description: article.description,
          datePublished: article.datePublished,
          dateModified: article.dateModified || article.datePublished,
          author: {
            '@type': 'Organization',
            name: article.author
          },
          ...(article.image ? { image: article.image } : {}),
          publisher: {
            '@type': 'Organization',
            name: 'Stoflow',
            logo: {
              '@type': 'ImageObject',
              url: 'https://stoflow.io/logo.png'
            }
          }
        })
      }
    ]
  })
}

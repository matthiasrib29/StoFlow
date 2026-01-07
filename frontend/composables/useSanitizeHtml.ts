import DOMPurify from 'dompurify'

/**
 * Composable pour sanitizer du contenu HTML
 * Prévient les attaques XSS en supprimant les scripts et event handlers
 *
 * @param html - Contenu HTML à nettoyer
 * @param allowedTags - Tags HTML autorisés (défaut: tags de contenu sûr)
 * @returns HTML nettoyé et sûr
 *
 * @example
 * const { sanitizeHtml } = useSanitizeHtml()
 * const clean = sanitizeHtml('<p>Safe <img onerror="alert(1)"></p>')
 * // Output: '<p>Safe <img></p>'
 */
export const useSanitizeHtml = () => {
  // Configuration par défaut: tags de contenu sûr
  const defaultAllowedTags = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'strong', 'b', 'em', 'i', 'u',
    'a', 'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    'blockquote', 'code', 'pre',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'img', 'figure', 'figcaption',
    'div', 'span'
  ]

  const defaultAllowedAttrs = [
    'href',
    'title',
    'class',
    'id',
    'src',
    'alt',
    'width',
    'height'
  ]

  /**
   * Nettoie le HTML en supprimant les scripts et event handlers
   */
  const sanitizeHtml = (
    html: string,
    allowedTags: string[] = defaultAllowedTags,
    allowedAttrs: string[] = defaultAllowedAttrs
  ): string => {
    if (!html) return ''

    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS: allowedTags,
      ALLOWED_ATTR: allowedAttrs,
      KEEP_CONTENT: true,
      FORCE_BODY: false,
      RETURN_DOM: false,
      RETURN_DOM_FRAGMENT: false,
      RETURN_DOM_IMPORT: false
    })
  }

  /**
   * Version stricte: seulement du texte avec formatage basique
   */
  const sanitizeStrict = (html: string): string => {
    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS: ['strong', 'em', 'br', 'p'],
      ALLOWED_ATTR: [],
      KEEP_CONTENT: true
    })
  }

  /**
   * Version pour testimonials: pas de HTML du tout, juste du texte
   */
  const sanitizeText = (html: string): string => {
    if (!html) return ''
    // Supprimer tous les tags HTML et entités
    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS: [],
      ALLOWED_ATTR: [],
      KEEP_CONTENT: true
    })
  }

  return {
    sanitizeHtml,
    sanitizeStrict,
    sanitizeText
  }
}

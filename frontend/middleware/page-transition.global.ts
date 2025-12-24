/**
 * Middleware global pour transitions de pages contextuelles
 *
 * Transitions désactivées pour les navigations internes au dashboard
 * pour éviter le délai de 250ms causé par le mode 'out-in'.
 * Les transitions sont uniquement appliquées pour les navigations
 * depuis/vers les pages d'authentification.
 */

export default defineNuxtRouteMiddleware((to, from) => {
  // Navigation interne au dashboard → pas de transition (navigation instantanée)
  const isDashboardInternal = to.path.startsWith('/dashboard') && from.path.startsWith('/dashboard')
  if (isDashboardInternal) {
    to.meta.pageTransition = false
    return
  }

  // Navigation vers/depuis auth → fade simple
  const isAuthTransition =
    to.path.includes('/login') || to.path.includes('/register') ||
    from.path.includes('/login') || from.path.includes('/register')

  if (isAuthTransition) {
    to.meta.pageTransition = {
      name: 'fade',
      mode: 'out-in'
    }
    return
  }

  // Navigation vers dashboard depuis landing ou vice versa → fade
  to.meta.pageTransition = {
    name: 'fade',
    mode: 'out-in'
  }
})

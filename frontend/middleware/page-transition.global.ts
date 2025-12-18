/**
 * Middleware global pour transitions de pages contextuelles
 * Applique des transitions différentes selon le type de navigation
 */

export default defineNuxtRouteMiddleware((to, from) => {
  // Déterminer le type de transition selon la route
  const getTransitionName = (toRoute: any, fromRoute: any): string => {
    // Navigation vers/depuis auth → fade simple
    if (toRoute.path.includes('/login') || toRoute.path.includes('/register') ||
        fromRoute.path.includes('/login') || fromRoute.path.includes('/register')) {
      return 'fade'
    }

    // Navigation vers création/édition → slide-up (modal-like)
    if (toRoute.path.includes('/create') || toRoute.path.includes('/edit') ||
        toRoute.path.match(/\/\[id\]/)) {
      return 'slide-up'
    }

    // Toutes les autres navigations → fade simple et rapide
    return 'fade'
  }

  const transitionName = getTransitionName(to, from)

  // Appliquer la transition via pageTransition
  to.meta.pageTransition = {
    name: transitionName,
    mode: 'out-in'
  }
})

/**
 * Middleware global pour transitions de pages
 *
 * Toutes les transitions sont désactivées pour éviter les pages blanches
 * causées par le mode 'out-in' sans styles CSS correspondants.
 *
 * Les transitions globales sont déjà désactivées dans nuxt.config.ts,
 * ce middleware s'assure qu'aucune transition n'est activée dynamiquement.
 */

export default defineNuxtRouteMiddleware((to) => {
  // Désactiver toutes les transitions pour une navigation instantanée
  to.meta.pageTransition = false
  to.meta.layoutTransition = false
})

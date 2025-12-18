/**
 * Plugin d'authentification (client-side only)
 * Charge la session depuis localStorage au démarrage de l'app
 *
 * Ce plugin s'exécute uniquement côté client (.client.ts suffix)
 * car localStorage n'est pas disponible côté serveur (SSR)
 */
export default defineNuxtPlugin(async () => {
  const authStore = useAuthStore()

  // Charger la session depuis localStorage
  authStore.loadFromStorage()

  // Si un token est présent, on pourrait optionnellement vérifier sa validité
  // en appelant un endpoint /me du backend, mais pour l'instant on fait confiance au localStorage
  // Une validation se fera automatiquement au premier appel API protégé via l'intercepteur

  // Log pour debug (à retirer en production)
  if (import.meta.dev) {
    if (authStore.isAuthenticated) {
      console.log('[Auth Plugin] Session restaurée:', {
        userId: authStore.user?.id,
        email: authStore.user?.email,
        role: authStore.user?.role
      })
    } else {
      console.log('[Auth Plugin] Aucune session active')
    }
  }
})

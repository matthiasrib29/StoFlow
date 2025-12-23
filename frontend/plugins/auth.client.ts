/**
 * Plugin d'authentification (client-side only)
 * Charge la session depuis localStorage au démarrage de l'app
 *
 * Ce plugin s'exécute uniquement côté client (.client.ts suffix)
 * car localStorage n'est pas disponible côté serveur (SSR)
 */
import { authLogger } from '~/utils/logger'

export default defineNuxtPlugin(async () => {
  const authStore = useAuthStore()

  // Charger la session depuis localStorage
  authStore.loadFromStorage()

  // Si un token est présent, on pourrait optionnellement vérifier sa validité
  // en appelant un endpoint /me du backend, mais pour l'instant on fait confiance au localStorage
  // Une validation se fera automatiquement au premier appel API protégé via l'intercepteur

  // Log sécurisé (automatiquement désactivé en production, données sensibles masquées)
  if (authStore.isAuthenticated) {
    authLogger.debug('Session restored', {
      userId: authStore.user?.id,
      role: authStore.user?.role
      // Note: email intentionally omitted for security
    })
  } else {
    authLogger.debug('No active session')
  }
})

/**
 * Configuration centralisée du plugin StoFlow
 *
 * Les variables sont injectées au moment du build via Vite.
 * - Développement: utilise .env.development
 * - Production: utilise .env.production
 *
 * Toutes les variables doivent avoir le préfixe VITE_ pour être accessibles.
 *
 * @see https://vitejs.dev/guide/env-and-mode.html
 */

/**
 * Configuration de l'environnement d'exécution
 */
export const ENV = {
  /**
   * URL de l'API backend Stoflow (kept for future use with eBay/Etsy)
   * @default https://api.stoflow.io
   */
  BACKEND_URL: import.meta.env.VITE_BACKEND_URL || 'https://api.stoflow.io',

  /**
   * Timeout pour les requêtes vers l'API Vinted (en ms)
   * @default 30000 (30 secondes)
   */
  VINTED_REQUEST_TIMEOUT: Number(import.meta.env.VITE_VINTED_REQUEST_TIMEOUT) || 30000,

  /**
   * Délai minimum entre chaque requête Vinted (en ms)
   * Protection anti-ban : évite les requêtes trop rapprochées
   * @default 1000 (1 seconde)
   */
  VINTED_MIN_REQUEST_DELAY: Number(import.meta.env.VITE_VINTED_MIN_REQUEST_DELAY) || 1000,

  /**
   * Activer les logs de debug
   * @default true en dev, false en prod
   */
  ENABLE_DEBUG_LOGS: import.meta.env.VITE_ENABLE_DEBUG_LOGS === 'true',

  /**
   * Version de l'application
   */
  APP_VERSION: import.meta.env.VITE_APP_VERSION || '2.0.0',

  /**
   * Mode d'exécution (development, production)
   */
  MODE: import.meta.env.MODE,

  /**
   * Indicateur de mode développement
   */
  IS_DEV: import.meta.env.DEV,

  /**
   * Indicateur de mode production
   */
  IS_PROD: import.meta.env.PROD,
} as const;

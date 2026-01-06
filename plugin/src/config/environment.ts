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

/**
 * URL backend production
 */
export const BACKEND_URL = 'https://api.stoflow.io';

/**
 * Constantes applicatives (non configurables via .env)
 */
export const CONSTANTS = {
  /**
   * Domaines autorisés pour les requêtes HTTP
   */
  ALLOWED_DOMAINS: [
    'www.vinted.fr',
    'vinted.fr',
    'api.vinted.fr',
  ] as const,

  /**
   * Méthodes HTTP autorisées
   */
  ALLOWED_HTTP_METHODS: [
    'GET',
    'POST',
    'PUT',
    'DELETE',
    'PATCH',
  ] as const,

  /**
   * Clés du storage Chrome
   */
  STORAGE_KEYS: {
    CONFIG_OVERRIDES: 'config_overrides',
  } as const,

  /**
   * Tailles limites
   */
  LIMITS: {
    MAX_REQUEST_BODY_SIZE: 1024 * 1024, // 1MB
    MAX_RETRIES: 3,
    CSRF_CACHE_DURATION: 5 * 60 * 1000, // 5 minutes
  } as const,
} as const;

/**
 * Valide la configuration au démarrage
 * Lève une erreur si la config est invalide
 */
export function validateConfig(): void {
  if (!ENV.BACKEND_URL) {
    throw new Error('VITE_BACKEND_URL is not defined');
  }

  try {
    new URL(ENV.BACKEND_URL);
  } catch (error) {
    throw new Error(`Invalid VITE_BACKEND_URL: ${ENV.BACKEND_URL}`);
  }
}

/**
 * Affiche la configuration au démarrage (mode debug uniquement)
 */
export function logConfig(): void {
  if (!ENV.ENABLE_DEBUG_LOGS) return;

  console.debug('🔧 [Config] StoFlow Plugin Configuration:');
  console.debug('  - Mode:', ENV.MODE);
  console.debug('  - Version:', ENV.APP_VERSION);
  console.debug('  - Backend URL:', ENV.BACKEND_URL);
  console.debug('  - Debug Logs:', ENV.ENABLE_DEBUG_LOGS);
}

/**
 * Récupère l'URL backend (production uniquement)
 * @returns L'URL backend production
 */
export function getActiveBackendUrl(): string {
  return BACKEND_URL;
}

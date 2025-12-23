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
   * URL de l'API backend Stoflow
   * Configurable via VITE_BACKEND_URL
   * @default http://localhost:8000 (dev)
   */
  BACKEND_URL: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',

  /**
   * Intervalle de polling initial (en ms)
   * @default 5000 (5 secondes)
   */
  POLL_INTERVAL: Number(import.meta.env.VITE_POLL_INTERVAL) || 5000,

  /**
   * Intervalle de polling maximum avec backoff (en ms)
   * @default 60000 (60 secondes)
   */
  POLL_MAX_INTERVAL: Number(import.meta.env.VITE_POLL_MAX_INTERVAL) || 60000,

  /**
   * Timeout global pour les requêtes API (en ms)
   * @default 30000 (30 secondes)
   */
  API_TIMEOUT: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,

  /**
   * Timeout pour les requêtes HTTP individuelles (en ms)
   * @default 10000 (10 secondes)
   */
  REQUEST_TIMEOUT: Number(import.meta.env.VITE_REQUEST_TIMEOUT) || 10000,

  /**
   * Timeout pour le long polling (en secondes)
   * Doit correspondre au timeout côté backend
   * @default 30 (30 secondes)
   */
  LONG_POLL_TIMEOUT: Number(import.meta.env.VITE_LONG_POLL_TIMEOUT) || 30,

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
 * URLs backend disponibles
 */
export const BACKEND_URLS = {
  LOCALHOST: 'http://localhost:8000',
  PRODUCTION: 'https://api.stoflow.com',
} as const;

export type EnvironmentMode = 'localhost' | 'production';

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
    ACCESS_TOKEN: 'stoflow_access_token',
    REFRESH_TOKEN: 'stoflow_refresh_token',
    USER_DATA: 'stoflow_user_data',
    CONFIG_OVERRIDES: 'config_overrides',
    ENVIRONMENT_MODE: 'stoflow_environment_mode',
  } as const,

  /**
   * Tailles limites
   */
  LIMITS: {
    MAX_REQUEST_BODY_SIZE: 1024 * 1024, // 1MB
    MAX_RETRIES: 3,
    MIN_POLL_INTERVAL: 5000, // 5s
    MAX_POLL_INTERVAL: 60000, // 60s
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

  if (ENV.POLL_INTERVAL < CONSTANTS.LIMITS.MIN_POLL_INTERVAL) {
    console.warn(
      `[Config] POLL_INTERVAL (${ENV.POLL_INTERVAL}ms) is below minimum (${CONSTANTS.LIMITS.MIN_POLL_INTERVAL}ms)`
    );
  }

  if (ENV.POLL_MAX_INTERVAL > CONSTANTS.LIMITS.MAX_POLL_INTERVAL) {
    console.warn(
      `[Config] POLL_MAX_INTERVAL (${ENV.POLL_MAX_INTERVAL}ms) exceeds maximum (${CONSTANTS.LIMITS.MAX_POLL_INTERVAL}ms)`
    );
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
  console.debug('  - Poll Interval:', ENV.POLL_INTERVAL, 'ms');
  console.debug('  - Debug Logs:', ENV.ENABLE_DEBUG_LOGS);
}

/**
 * Récupère l'URL backend active depuis le storage
 * @returns L'URL backend selon le mode choisi (localhost ou production)
 */
export async function getActiveBackendUrl(): Promise<string> {
  try {
    const result = await chrome.storage.local.get(CONSTANTS.STORAGE_KEYS.ENVIRONMENT_MODE);
    const mode: EnvironmentMode = result[CONSTANTS.STORAGE_KEYS.ENVIRONMENT_MODE] || 'localhost';
    return mode === 'production' ? BACKEND_URLS.PRODUCTION : BACKEND_URLS.LOCALHOST;
  } catch {
    // Fallback si erreur (ex: contexte non-extension)
    return BACKEND_URLS.LOCALHOST;
  }
}

/**
 * Récupère le mode d'environnement actuel
 */
export async function getEnvironmentMode(): Promise<EnvironmentMode> {
  try {
    const result = await chrome.storage.local.get(CONSTANTS.STORAGE_KEYS.ENVIRONMENT_MODE);
    return result[CONSTANTS.STORAGE_KEYS.ENVIRONMENT_MODE] || 'localhost';
  } catch {
    return 'localhost';
  }
}

/**
 * Définit le mode d'environnement
 */
export async function setEnvironmentMode(mode: EnvironmentMode): Promise<void> {
  await chrome.storage.local.set({ [CONSTANTS.STORAGE_KEYS.ENVIRONMENT_MODE]: mode });
}

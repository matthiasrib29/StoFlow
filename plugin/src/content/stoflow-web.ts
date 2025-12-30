/**
 * Content Script pour le site web Stoflow
 *
 * Ce script s'injecte sur le site web Stoflow et gère la synchronisation SSO
 * avec le frontend Nuxt.
 *
 * SÉCURITÉ: Communication bidirectionnelle sécurisée
 * 1. Le plugin s'annonce au frontend avec son origine (STOFLOW_PLUGIN_READY)
 * 2. Le frontend mémorise l'origine et répond avec STOFLOW_FRONTEND_ACK
 * 3. Les tokens sont échangés uniquement avec validation d'origine stricte
 *
 * Flow:
 * 1. Plugin se charge → envoie STOFLOW_PLUGIN_READY
 * 2. Frontend reçoit → mémorise l'origine du plugin
 * 3. User se connecte → Frontend envoie STOFLOW_SYNC_TOKEN vers l'origine du plugin
 * 4. Plugin reçoit (avec validation d'origine) → stocke dans chrome.storage
 */

import { CONSTANTS } from '../config/environment';

// ==================== CONFIGURATION SÉCURITÉ ====================

// Origines autorisées pour recevoir des messages (frontend Stoflow)
const ALLOWED_ORIGINS = [
  'https://stoflow.io',
  'https://www.stoflow.io',
  'https://app.stoflow.io'
];

// Flag pour les logs (désactivés en production)
const DEBUG_ENABLED = false;

/**
 * Mini-logger for content script context
 * Consistent format with other plugin loggers
 */
const PREFIX = '[Stoflow Web]';
const log = {
  debug: (...args: any[]) => DEBUG_ENABLED && console.log(PREFIX, ...args),
  info: (...args: any[]) => console.log(PREFIX, '✓', ...args),
  warn: (...args: any[]) => console.warn(PREFIX, '⚠', ...args),
  error: (...args: any[]) => console.error(PREFIX, '✗', ...args),
  success: (...args: any[]) => console.log(PREFIX, '✓', ...args)
};

// ==================== VALIDATION SÉCURITÉ ====================

/**
 * Vérifie si une origine est autorisée
 */
function isAllowedOrigin(origin: string): boolean {
  return ALLOWED_ORIGINS.some(allowed => origin === allowed || origin.startsWith(allowed));
}

/**
 * Valide la structure d'un message de token
 */
function isValidTokenMessage(data: any): data is { type: string; access_token: string; refresh_token?: string } {
  return (
    typeof data === 'object' &&
    data !== null &&
    typeof data.type === 'string' &&
    typeof data.access_token === 'string' &&
    data.access_token.length > 0
  );
}

// ==================== ANNONCE AU FRONTEND ====================

/**
 * Annonce la présence du plugin au frontend
 * Le frontend mémorisera notre origine pour les communications futures
 */
function announceToFrontend() {
  log.debug('Annonce au frontend...');

  // Envoyer vers toutes les origines autorisées (le frontend écoutera)
  // Note: On envoie vers '*' car on ne connaît pas encore l'origine exacte du frontend
  // Mais le MESSAGE lui-même ne contient PAS de données sensibles
  window.postMessage({
    type: 'STOFLOW_PLUGIN_READY',
    version: '1.0.0'
  }, '*');

  log.info('Plugin annoncé au frontend');
}

// ==================== GESTION DES TOKENS ====================

/**
 * Récupère le token depuis localStorage du site web
 */
function getTokenFromLocalStorage(): string | null {
  try {
    const possibleKeys = [
      'stoflow_access_token',
      'stoflow_token',
      'access_token',
      'auth_token',
      'token'
    ];

    for (const key of possibleKeys) {
      const token = localStorage.getItem(key);
      if (token) {
        log.debug(`Token trouvé dans localStorage.${key}`);
        return token;
      }
    }

    // Essayer de récupérer depuis un objet auth complet
    const authData = localStorage.getItem('auth');
    if (authData) {
      try {
        const parsed = JSON.parse(authData);
        if (parsed.access_token || parsed.token) {
          log.debug('Token trouvé dans localStorage.auth');
          return parsed.access_token || parsed.token;
        }
      } catch {
        // Ignore parsing errors
      }
    }

    return null;
  } catch (error) {
    log.error('Erreur lecture localStorage:', error);
    return null;
  }
}

/**
 * Récupère le refresh token depuis localStorage
 */
function getRefreshTokenFromLocalStorage(): string | null {
  try {
    const possibleKeys = ['stoflow_refresh_token', 'refresh_token'];

    for (const key of possibleKeys) {
      const token = localStorage.getItem(key);
      if (token) {
        return token;
      }
    }

    // Essayer depuis objet auth
    const authData = localStorage.getItem('auth');
    if (authData) {
      try {
        const parsed = JSON.parse(authData);
        if (parsed.refresh_token) {
          return parsed.refresh_token;
        }
      } catch {
        // Ignore
      }
    }

    return null;
  } catch (error) {
    log.error('Erreur lecture refresh token:', error);
    return null;
  }
}

/**
 * Envoie le token au background script pour stockage
 */
async function syncTokenToBackground(accessToken: string, refreshToken: string | null) {
  log.debug('Envoi du token au background...');

  try {
    const response = await chrome.runtime.sendMessage({
      action: 'SYNC_TOKEN_FROM_WEBSITE',
      access_token: accessToken,
      refresh_token: refreshToken
    });

    if (response?.success) {
      log.info('Token synchronisé avec succès');
      showSyncNotification();
      return true;
    } else {
      log.error('Échec synchronisation:', response?.error);
      return false;
    }
  } catch (error) {
    log.error('Erreur envoi au background:', error);
    return false;
  }
}

/**
 * Synchronise le token initial depuis localStorage
 */
async function syncTokenFromLocalStorage() {
  const accessToken = getTokenFromLocalStorage();
  const refreshToken = getRefreshTokenFromLocalStorage();

  if (!accessToken) {
    log.debug('Aucun token à synchroniser depuis localStorage');
    return;
  }

  await syncTokenToBackground(accessToken, refreshToken);
}

// ==================== NOTIFICATION ====================

/**
 * Affiche une notification discrète de synchronisation
 */
function showSyncNotification() {
  // Éviter les doublons
  if (document.getElementById('stoflow-sso-toast')) {
    return;
  }

  const toast = document.createElement('div');
  toast.id = 'stoflow-sso-toast';
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #10b981;
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    font-family: system-ui, -apple-system, sans-serif;
    font-size: 14px;
    z-index: 999999;
    display: flex;
    align-items: center;
    gap: 8px;
    animation: stoflow-slideIn 0.3s ease-out;
  `;
  toast.innerHTML = `
    <span>✓</span>
    <span>Plugin Stoflow connecté</span>
  `;

  // Ajouter l'animation (une seule fois)
  if (!document.getElementById('stoflow-toast-style')) {
    const style = document.createElement('style');
    style.id = 'stoflow-toast-style';
    style.textContent = `
      @keyframes stoflow-slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
    `;
    document.head.appendChild(style);
  }

  document.body.appendChild(toast);

  // Retirer après 3 secondes
  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ==================== LISTENERS ====================

/**
 * Configure le listener pour les messages postMessage du frontend
 */
function setupMessageListener() {
  log.debug('Installation du listener postMessage...');

  window.addEventListener('message', async (event) => {
    // SÉCURITÉ CRITIQUE: Valider l'origine du message
    if (!isAllowedOrigin(event.origin)) {
      // Ignorer silencieusement les messages d'origines non autorisées
      return;
    }

    const data = event.data;
    if (!data || typeof data.type !== 'string') {
      return;
    }

    // Traiter les différents types de messages
    switch (data.type) {
      case 'STOFLOW_FRONTEND_ACK':
        // Le frontend a reçu notre annonce
        log.info('Frontend a confirmé la réception (ACK)');
        break;

      case 'STOFLOW_SYNC_TOKEN':
        // Le frontend envoie un token après login
        log.debug('Token reçu du frontend');

        if (!isValidTokenMessage(data)) {
          log.warn('Message de token invalide, ignoré');
          return;
        }

        await syncTokenToBackground(data.access_token, data.refresh_token || null);
        break;

      case 'STOFLOW_LOGOUT':
        // Le frontend signale une déconnexion
        log.info('Logout reçu du frontend');

        try {
          await chrome.runtime.sendMessage({
            action: 'LOGOUT_FROM_WEBSITE'
          });
          log.info('Logout synchronisé');
        } catch (error) {
          log.error('Erreur logout:', error);
        }
        break;

      default:
        // Ignorer les autres types de messages
        break;
    }
  });

  log.debug('Listener postMessage installé');
}

/**
 * Observe les changements de localStorage (login/logout dans le même onglet)
 */
function setupLocalStorageObserver() {
  // Observer les changements via storage event (autres onglets)
  window.addEventListener('storage', (event) => {
    if (event.key?.includes('token') || event.key === 'auth') {
      log.debug('Token modifié (storage event), re-synchronisation...');
      setTimeout(() => syncTokenFromLocalStorage(), 100);
    }
  });

  // Observer les changements directs (même onglet) via proxy
  const originalSetItem = localStorage.setItem.bind(localStorage);
  localStorage.setItem = function(key: string, value: string) {
    originalSetItem(key, value);
    if (key.includes('token') || key === 'auth') {
      log.debug('Token modifié (setItem), re-synchronisation...');
      setTimeout(() => syncTokenFromLocalStorage(), 100);
    }
  };

  log.debug('Observer localStorage installé');
}

// ==================== INITIALISATION ====================

function init() {
  log.info('Content script chargé sur', window.location.href);

  // 1. S'annoncer au frontend
  announceToFrontend();

  // 2. Configurer le listener pour les messages du frontend
  setupMessageListener();

  // 3. Observer les changements de localStorage
  setupLocalStorageObserver();

  // 4. Synchroniser le token initial (si déjà connecté)
  setTimeout(() => {
    syncTokenFromLocalStorage();
  }, 500);

  // 5. Re-synchroniser périodiquement (backup)
  setInterval(() => {
    const token = getTokenFromLocalStorage();
    if (token) {
      syncTokenFromLocalStorage();
    }
  }, 30000);

  log.info('Initialisation terminée');
}

// Démarrer
init();

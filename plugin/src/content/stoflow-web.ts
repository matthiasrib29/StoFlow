/**
 * Content Script for StoFlow Website
 *
 * This script injects on stoflow.io and handles:
 * 1. Firefox fallback for Vinted actions (since Firefox doesn't support externally_connectable)
 *
 * Architecture:
 * - Chrome: Frontend uses chrome.runtime.sendMessage directly (externally_connectable)
 * - Firefox: Frontend uses postMessage → this content script → background script
 *
 * Security:
 * - Validates message origins against whitelist
 *
 * Author: Claude
 * Date: 2026-01-06
 */

// ==================== CONFIGURATION SÉCURITÉ ====================

// Origines autorisées pour recevoir des messages (frontend Stoflow)
const ALLOWED_ORIGINS = [
  'https://stoflow.io',
  'https://www.stoflow.io',
  'https://app.stoflow.io',
  'http://localhost:3000',
  'http://localhost:5173'
];

// Flag pour les logs (activés pour debug)
const DEBUG_ENABLED = true;

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

// ==================== ANNONCE AU FRONTEND ====================

/**
 * Annonce la présence du plugin au frontend
 * Le frontend mémorisera notre origine pour les communications futures
 */
function announceToFrontend() {
  log.debug('Annonce au frontend...');

  // Send to current origin (the frontend will listen)
  // Note: Using window.location.origin instead of '*' for better security
  window.postMessage({
    type: 'STOFLOW_PLUGIN_READY',
    version: '1.0.0'
  }, window.location.origin);

  log.info('Plugin annoncé au frontend');
}


// ==================== FIREFOX FALLBACK: VINTED ACTIONS ====================

/**
 * Handles Vinted actions from the frontend (Firefox fallback)
 *
 * Since Firefox doesn't support externally_connectable, the frontend sends
 * Vinted actions via postMessage, and we relay them to the background script.
 */
async function handleVintedAction(data: any, origin: string) {
  const { action, requestId, payload } = data;

  log.debug('Vinted action received:', action, requestId);

  try {
    // Forward to background script
    const response = await chrome.runtime.sendMessage({
      action,
      requestId,
      payload
    });

    // Send response back to frontend via postMessage
    window.postMessage({
      type: 'VINTED_ACTION_RESPONSE',
      requestId,
      ...response
    }, origin);

    if (response?.success) {
      log.debug('Vinted action completed:', action);
    } else {
      log.warn('Vinted action failed:', action, response?.error);
    }
  } catch (error: any) {
    log.error('Error forwarding Vinted action:', error);

    // Send error response back to frontend
    window.postMessage({
      type: 'VINTED_ACTION_RESPONSE',
      requestId,
      success: false,
      error: error.message || 'Content script error',
      errorCode: 'CONTENT_SCRIPT_ERROR'
    }, origin);
  }
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

      // ============ FIREFOX FALLBACK: Vinted Actions ============
      // Firefox doesn't support externally_connectable, so the frontend
      // sends Vinted actions via postMessage instead of chrome.runtime.sendMessage
      case 'VINTED_ACTION':
        await handleVintedAction(data, event.origin);
        break;

      default:
        // Ignorer les autres types de messages
        break;
    }
  });

  log.debug('Listener postMessage installé');
}


// ==================== INITIALISATION ====================

function init() {
  log.info('Content script chargé sur', window.location.href);

  // 1. S'annoncer au frontend
  announceToFrontend();

  // 2. Configurer le listener pour les messages du frontend (Firefox fallback)
  setupMessageListener();

  log.info('Initialisation terminée');
}

// Démarrer
init();

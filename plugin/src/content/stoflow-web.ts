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
 * - Validates message origins against centralized whitelist (origins.ts)
 *
 * Author: Claude
 * Date: 2026-01-06
 */

// ==================== IMPORTS ====================

import { getAllowedOrigins, isAllowedOrigin as validateOrigin } from '../config/origins';

// ==================== CONFIGURATION ====================

// Flag for logs (enabled only in development)
const DEBUG_ENABLED = import.meta.env.DEV;

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

// ==================== SECURITY VALIDATION ====================

/**
 * Check if an origin is allowed.
 * Uses the centralized origin validator with strict equality check.
 * SECURITY: Does NOT use startsWith to prevent bypass attacks (e.g., stoflow.io.evil.com)
 */
function isAllowedOrigin(origin: string): boolean {
  return validateOrigin(origin);
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

  log.info('═══════════════════════════════════════════════');
  log.info('🎯 VINTED_ACTION received from frontend');
  log.info(`   Action: ${action}`);
  log.info(`   Request ID: ${requestId}`);
  if (payload) {
    log.debug(`   Payload: ${JSON.stringify(payload).substring(0, 200)}`);
  }

  const startTime = Date.now();

  try {
    log.info('📤 Forwarding to background script...');

    // Forward to background script
    const response = await chrome.runtime.sendMessage({
      action,
      requestId,
      payload
    });

    const duration = Date.now() - startTime;

    // Send response back to frontend via postMessage
    window.postMessage({
      type: 'VINTED_ACTION_RESPONSE',
      requestId,
      ...response
    }, origin);

    if (response?.success) {
      log.info(`✅ Action ${action} completed in ${duration}ms`);
    } else {
      log.warn(`❌ Action ${action} failed in ${duration}ms: ${response?.error}`);
    }
    log.info('═══════════════════════════════════════════════');
  } catch (error: any) {
    const duration = Date.now() - startTime;
    log.error(`💥 Error forwarding ${action} after ${duration}ms:`, error);
    log.info('═══════════════════════════════════════════════');

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
    // Log ALL messages received (for debugging)
    log.debug('📥 Message reçu:', {
      origin: event.origin,
      type: event.data?.type,
      data: event.data
    });

    // SÉCURITÉ CRITIQUE: Valider l'origine du message
    if (!isAllowedOrigin(event.origin)) {
      log.warn('❌ Origine refusée:', event.origin, 'Autorisées:', getAllowedOrigins());
      return;
    }

    const data = event.data;
    if (!data || typeof data.type !== 'string') {
      log.debug('⚠️  Message ignoré (pas de type):', data);
      return;
    }

    // IMPORTANT: Ignore our own STOFLOW_PLUGIN_READY messages to avoid infinite loop
    if (data.type === 'STOFLOW_PLUGIN_READY') {
      log.debug('⚠️  Message ignoré (notre propre annonce)');
      return;
    }

    log.info('✅ Message accepté:', data.type);

    // Traiter les différents types de messages
    switch (data.type) {
      case 'STOFLOW_FRONTEND_ACK':
        // Le frontend a reçu notre annonce
        log.info('Frontend a confirmé la réception (ACK)');
        break;

      case 'STOFLOW_PING':
        // Frontend is asking if we're here - respond with PLUGIN_READY
        log.info('🏓 Ping reçu du frontend - réponse PONG');
        window.postMessage({
          type: 'STOFLOW_PLUGIN_READY',
          version: '1.0.0',
          isPong: true  // Flag to indicate this is a response to ping
        }, event.origin);
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

// Guard against multiple injections (can happen with registerContentScripts + manifest content_scripts)
const INIT_FLAG = '__STOFLOW_CONTENT_SCRIPT_INITIALIZED__';

function init() {
  // Check if already initialized
  if ((window as any)[INIT_FLAG]) {
    log.warn('Content script déjà initialisé - skip');
    return;
  }
  (window as any)[INIT_FLAG] = true;

  log.info('Content script chargé sur', window.location.href);

  // 1. S'annoncer au frontend
  announceToFrontend();

  // 2. Configurer le listener pour les messages du frontend (Firefox fallback)
  setupMessageListener();

  log.info('Initialisation terminée');
}

// Démarrer
init();

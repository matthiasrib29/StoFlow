/**
 * Stoflow Content Script for Vinted
 *
 * Extracts user data and provides API for communication with Vinted
 */

import { VintedLogger } from '../utils/logger';
import { ENV } from '../config/environment';

// Import the API injector - this injects stoflow-vinted-api.js into MAIN world
import './inject-api';
// ===== SYNC CREDENTIALS TO BACKEND =====

/**
 * Vérifie si l'utilisateur est connecté à Stoflow (token présent)
 * Avec timeout pour éviter de bloquer si le background ne répond pas
 */
async function isAuthenticatedToStoflow(): Promise<boolean> {
  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      VintedLogger.debug('[Stoflow] ⚠️ Timeout vérification auth (background ne répond pas);');
      resolve(false);
    }, 3000); // 3 secondes timeout

    try {
      chrome.runtime.sendMessage({ action: 'CHECK_AUTH_STATUS' }, (response) => {
        clearTimeout(timeout);
        if (chrome.runtime.lastError) {
          VintedLogger.debug('[Stoflow] ⚠️ Erreur communication background:', chrome.runtime.lastError.message);
          resolve(false);
          return;
        }
        VintedLogger.debug('[Stoflow] Auth status:', response);
        resolve(response?.authenticated === true);
      });
    } catch (error) {
      clearTimeout(timeout);
      VintedLogger.error('[Stoflow] Erreur check auth:', error);
      resolve(false);
    }
  });
}

// ===== INITIALIZATION =====

VintedLogger.debug('');
VintedLogger.debug('🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️');
VintedLogger.debug('🛍️ [STOFLOW VINTED] Content script chargé !');
VintedLogger.debug('🛍️ URL:', window.location.href);
VintedLogger.debug('🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️🛍️');
VintedLogger.debug('');

// ===== VINTED API BRIDGE ACCESS =====

/**
 * Import the vintedAPI bridge for making API calls via Vinted's Axios instance
 */
import { vintedAPI } from './vinted-api-bridge';

/**
 * Import the simplified Vinted user info extraction
 */
import { getVintedUserInfo } from './vinted-detector';

// ===== MESSAGE HANDLERS =====

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const action = message.action;

  /**
   * GET_VINTED_USER_INFO - Extract userId + login from Vinted page (DOM parsing)
   * Used by check_vinted_connection task (legacy)
   */
  if (action === 'GET_VINTED_USER_INFO') {
    VintedLogger.debug('');
    VintedLogger.debug('📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨');
    VintedLogger.debug('📨 [VINTED] Message reçu: GET_VINTED_USER_INFO');
    VintedLogger.debug('📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨');

    try {
      VintedLogger.debug('📨 Appel de getVintedUserInfo()...');
      const userInfo = getVintedUserInfo();

      VintedLogger.debug('📨 Infos extraites:', {
        userId: userInfo.userId,
        login: userInfo.login
      });

      const response = {
        success: true,
        data: {
          userId: userInfo.userId,
          login: userInfo.login
        }
      };

      VintedLogger.debug('📨 ✅ Envoi de la réponse au popup:', response);
      VintedLogger.debug('📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨');
      VintedLogger.debug('');

      sendResponse(response);
    } catch (error: any) {
      VintedLogger.error('📨 ❌ ERREUR lors de l\'extraction:', error);
      VintedLogger.error('📨 Stack:', error.stack);
      VintedLogger.debug('📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨📨');
      VintedLogger.debug('');

      sendResponse({ success: false, error: error.message });
    }
    return true;
  }

  /**
   * GET_VINTED_USER_PROFILE - Fetch full user profile from Vinted API
   * Uses /api/v2/users/current endpoint with fallback to DOM parsing
   * Returns user info + seller stats (item_count, feedback_count, etc.)
   */
  if (action === 'GET_VINTED_USER_PROFILE') {
    VintedLogger.debug('');
    VintedLogger.debug('👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤');
    VintedLogger.debug('👤 [VINTED] Message reçu: GET_VINTED_USER_PROFILE');
    VintedLogger.debug('👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤');

    (async () => {
      try {
        // Try API call first
        VintedLogger.debug('👤 Tentative appel API /api/v2/users/current...');

        const requestId = `profile_${Date.now()}_${Math.random().toString(36).substring(7)}`;
        let responseSent = false;

        // Promise wrapper for API call
        const apiResult = await new Promise<any>((resolve, reject) => {
          const responseListener = (event: MessageEvent) => {
            if (event.source !== window) return;
            if (responseSent) return;

            const msg = event.data;
            if (msg.type === 'STOFLOW_API_RESPONSE' && msg.requestId === requestId) {
              responseSent = true;
              window.removeEventListener('message', responseListener);
              clearTimeout(timeoutId);

              if (msg.success && msg.data?.user) {
                resolve(msg.data);
              } else {
                reject(new Error(msg.error || 'API call failed'));
              }
            }
          };

          window.addEventListener('message', responseListener);

          const timeoutId = setTimeout(() => {
            if (responseSent) return;
            responseSent = true;
            window.removeEventListener('message', responseListener);
            reject(new Error('API timeout'));
          }, 10000); // 10s timeout for API call

          // Send message to injected script
          window.postMessage({
            type: 'STOFLOW_API_CALL',
            requestId,
            method: 'GET',
            endpoint: '/users/current',
            params: {},
            data: null,
            config: {}
          }, '*');
        });

        // API call succeeded - extract full profile
        const user = apiResult.user;
        VintedLogger.debug('👤 ✅ API success! User:', user.login);

        const response = {
          success: true,
          source: 'api',
          data: {
            userId: user.id,
            login: user.login,
            // Seller stats
            stats: {
              item_count: user.item_count,
              total_items_count: user.total_items_count,
              given_item_count: user.given_item_count,
              taken_item_count: user.taken_item_count,
              followers_count: user.followers_count,
              feedback_count: user.feedback_count,
              feedback_reputation: user.feedback_reputation,
              positive_feedback_count: user.positive_feedback_count,
              negative_feedback_count: user.negative_feedback_count,
              is_business: user.business,
              is_on_holiday: user.is_on_holiday
            }
          }
        };

        VintedLogger.debug('👤 ✅ Réponse avec stats:', response);
        VintedLogger.debug('👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤');
        sendResponse(response);

      } catch (apiError: any) {
        // API failed - fallback to DOM parsing
        VintedLogger.warn('👤 ⚠️ API failed, fallback to DOM parsing:', apiError.message);

        try {
          const userInfo = getVintedUserInfo();

          const response = {
            success: true,
            source: 'dom',
            data: {
              userId: userInfo.userId,
              login: userInfo.login,
              stats: null // No stats from DOM parsing
            }
          };

          VintedLogger.debug('👤 ✅ Fallback DOM success:', response);
          VintedLogger.debug('👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤');
          sendResponse(response);

        } catch (domError: any) {
          VintedLogger.error('👤 ❌ Both API and DOM failed:', domError.message);
          VintedLogger.debug('👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤');
          sendResponse({
            success: false,
            error: `API: ${apiError.message}, DOM: ${domError.message}`
          });
        }
      }
    })();

    return true; // Async response
  }

  /**
   * FETCH_HTML_PAGE - Fetch HTML pages via the injected script hook
   * Uses STOFLOW_FETCH_HTML message to communicate with stoflow-vinted-api.js
   * Used for fetching product pages to extract meta description
   */
  if (action === 'FETCH_HTML_PAGE') {
    const { url } = message;

    if (!url) {
      sendResponse({ success: false, error: 'URL manquante' });
      return true;
    }

    VintedLogger.debug('');
    VintedLogger.debug('📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄');
    VintedLogger.debug(`📄 [VINTED] FETCH_HTML_PAGE: ${url}`);
    VintedLogger.debug('📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄📄');

    // Generate unique request ID
    const requestId = `html_${Date.now()}_${Math.random().toString(36).substring(7)}`;

    // Flag to prevent double sendResponse
    let responseSent = false;

    // Create listener for the response from injected script
    const responseListener = (event: MessageEvent) => {
      if (event.source !== window) return;
      if (responseSent) return; // Already responded

      const messageData = event.data;

      if (messageData.type === 'STOFLOW_FETCH_HTML_RESPONSE' && messageData.requestId === requestId) {
        responseSent = true;
        window.removeEventListener('message', responseListener);
        clearTimeout(timeoutId);

        VintedLogger.debug('📄 [VINTED] Réponse HTML reçue du script injecté');
        VintedLogger.debug('📄 Success:', messageData.success);
        VintedLogger.debug('📄 Data length:', messageData.data?.length || 0);

        if (messageData.success) {
          sendResponse({
            success: true,
            status: messageData.status || 200,
            data: messageData.data
          });
        } else {
          VintedLogger.error('📄 [VINTED] Erreur:', messageData.error, 'Status:', messageData.status);
          sendResponse({
            success: false,
            status: messageData.status || 500,
            statusText: messageData.statusText || 'Error',
            error: messageData.error || 'Erreur fetch HTML'
          });
        }
      }
    };

    // Add listener
    window.addEventListener('message', responseListener);

    // Timeout (configurable via ENV.VINTED_REQUEST_TIMEOUT)
    const timeoutId = setTimeout(() => {
      if (responseSent) return; // Already responded
      responseSent = true;
      window.removeEventListener('message', responseListener);
      sendResponse({ success: false, status: 408, error: `Request timeout (${ENV.VINTED_REQUEST_TIMEOUT / 1000}s)` });
    }, ENV.VINTED_REQUEST_TIMEOUT);

    // Send message to injected script
    window.postMessage({
      type: 'STOFLOW_FETCH_HTML',
      requestId,
      url
    }, '*');

    VintedLogger.debug('📄 [VINTED] Message STOFLOW_FETCH_HTML envoyé au script injecté');

    return true; // Async response
  }

  /**
   * VINTED_API_CALL - Generic Vinted API call using Webpack hook
   * Uses the vintedAPI bridge to make calls via Vinted's Axios instance
   */
  if (action === 'VINTED_API_CALL') {
    const { method, endpoint, data, config } = message;

    if (!method || !endpoint) {
      sendResponse({ success: false, error: 'Invalid VINTED_API_CALL: missing method or endpoint' });
      return true;
    }

    (async () => {
      try {
        VintedLogger.debug(`[Stoflow] 🔄 VINTED_API_CALL: ${method} ${endpoint}`);

        let response;
        switch (method.toUpperCase()) {
          case 'GET':
            response = await vintedAPI.get(endpoint, data);
            break;
          case 'POST':
            response = await vintedAPI.post(endpoint, data, config);
            break;
          case 'PUT':
            response = await vintedAPI.put(endpoint, data);
            break;
          case 'DELETE':
            response = await vintedAPI.delete(endpoint);
            break;
          default:
            throw new Error(`Unsupported method: ${method}`);
        }

        VintedLogger.debug(`[Stoflow] ✅ VINTED_API_CALL success:`, response);

        sendResponse({
          success: true,
          status: 200,
          data: response
        });
      } catch (error: any) {
        VintedLogger.error(`[Stoflow] ❌ VINTED_API_CALL error:`, error);

        sendResponse({
          success: false,
          status: error.status || 500,
          error: error.message || 'Unknown error'
        });
      }
    })();
    return true;
  }

  /**
   * DATADOME_PING - Ping DataDome to maintain session
   * Used by DataDome scheduler to keep the Vinted session alive
   */
  if (action === 'DATADOME_PING') {
    VintedLogger.debug('');
    VintedLogger.debug('🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️');
    VintedLogger.debug('🛡️ [VINTED] DATADOME_PING received');
    VintedLogger.debug('🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️');

    // Generate unique request ID
    const requestId = `datadome_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    let responseSent = false;

    // Create listener for response from injected script
    const responseListener = (event: MessageEvent) => {
      if (event.source !== window) return;
      const msg = event.data;

      if (msg.type === 'STOFLOW_DATADOME_PING_RESPONSE' && msg.requestId === requestId) {
        if (responseSent) return;
        responseSent = true;

        window.removeEventListener('message', responseListener);
        clearTimeout(timeout);

        VintedLogger.debug('🛡️ [VINTED] DataDome ping response:', msg);

        sendResponse({
          success: msg.success,
          data: msg.data,
          error: msg.error
        });
      }
    };

    window.addEventListener('message', responseListener);

    // Timeout (10 seconds for DataDome ping)
    const timeout = setTimeout(() => {
      if (responseSent) return;
      responseSent = true;
      window.removeEventListener('message', responseListener);
      VintedLogger.warn('🛡️ [VINTED] DataDome ping timeout');
      sendResponse({
        success: false,
        error: 'DataDome ping timeout (10s)',
        data: { success: false, ping_count: 0 }
      });
    }, 10000);

    // Send message to injected script
    window.postMessage({
      type: 'STOFLOW_DATADOME_PING',
      requestId
    }, '*');

    VintedLogger.debug('🛡️ [VINTED] Message STOFLOW_DATADOME_PING sent to injected script');

    return true; // Async response
  }

  /**
   * EXECUTE_VINTED_API - New architecture (2025-12-11)
   * Utilise window.postMessage pour communiquer avec le script injecté stoflow-vinted-api.js
   * Le script injecté gère les headers automatiquement via le hook Axios de Vinted
   */
  if (action === 'EXECUTE_VINTED_API') {
    const { url, method, params, body } = message;

    if (!url || !method) {
      sendResponse({ success: false, error: 'Invalid EXECUTE_VINTED_API: missing url or method' });
      return true;
    }

    VintedLogger.debug('');
    VintedLogger.debug('🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐');
    VintedLogger.debug(`🌐 [VINTED] EXECUTE_VINTED_API: ${method} ${url}`);
    VintedLogger.debug('🌐 Params:', params);
    VintedLogger.debug('🌐 Body:', body);
    VintedLogger.debug('🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐');

    // Extraire l'endpoint depuis l'URL (complète ou relative)
    // Le baseURL de l'API Vinted est déjà "/api/v2", donc on doit retirer ce préfixe
    let endpoint: string;
    try {
      // URL complète (https://www.vinted.fr/api/v2/items?page=1)
      const urlObj = new URL(url);
      endpoint = urlObj.pathname + urlObj.search; // Inclure les query params!
    } catch {
      // URL relative (/api/v2/items ou /items) - utiliser directement
      endpoint = url;
    }

    // Retirer le préfixe /api/v2 si présent (évite la duplication)
    if (endpoint.startsWith('/api/v2')) {
      endpoint = endpoint.replace('/api/v2', '');
    }

    // Générer un ID unique pour cette requête
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substring(7)}`;

    // Flag to prevent double sendResponse
    let responseSent = false;

    // Créer un listener pour la réponse
    const responseListener = (event: MessageEvent) => {
      // Vérifier que le message vient de la même fenêtre
      if (event.source !== window) return;
      if (responseSent) return; // Already responded

      const messageData = event.data;

      // Vérifier que c'est une réponse à notre requête
      if (messageData.type === 'STOFLOW_API_RESPONSE' && messageData.requestId === requestId) {
        responseSent = true;
        window.removeEventListener('message', responseListener);
        clearTimeout(timeoutId);

        VintedLogger.debug('🌐 [VINTED] Réponse reçue du script injecté');
        VintedLogger.debug('🌐 Success:', messageData.success);
        VintedLogger.debug('🌐 Data:', messageData.data);

        if (messageData.success) {
          sendResponse({
            success: true,
            status: messageData.status || 200,
            data: messageData.data
          });
        } else {
          VintedLogger.error('🌐 [VINTED] Erreur:', messageData.error);
          sendResponse({
            success: false,
            status: messageData.status || 500,
            error: messageData.error || 'Unknown error'
          });
        }
      }
    };

    // Ajouter le listener
    window.addEventListener('message', responseListener);

    // Timeout (configurable via ENV.VINTED_REQUEST_TIMEOUT)
    const timeoutId = setTimeout(() => {
      if (responseSent) return; // Already responded
      responseSent = true;
      window.removeEventListener('message', responseListener);
      sendResponse({ success: false, error: `Request timeout (${ENV.VINTED_REQUEST_TIMEOUT / 1000}s)` });
    }, ENV.VINTED_REQUEST_TIMEOUT);

    // Envoyer le message au script injecté
    window.postMessage({
      type: 'STOFLOW_API_CALL',
      requestId,
      method: method.toUpperCase(),
      endpoint,
      params,
      data: body,
      config: {}
    }, '*');

    VintedLogger.debug('🌐 [VINTED] Message postMessage envoyé au script injecté');

    return true; // Async response
  }

  /**
   * REFRESH_VINTED_SESSION - Refresh Vinted session cookies
   * Called by backend when a task returns 401
   * Uses /web/api/auth/refresh endpoint to regenerate session
   */
  if (action === 'REFRESH_VINTED_SESSION') {
    VintedLogger.debug('');
    VintedLogger.debug('🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄');
    VintedLogger.debug('🔄 [VINTED] REFRESH_VINTED_SESSION received');
    VintedLogger.debug('🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄🔄');

    const requestId = `refresh_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    let responseSent = false;

    const responseListener = (event: MessageEvent) => {
      if (event.source !== window) return;
      if (responseSent) return;

      const msg = event.data;

      if (msg.type === 'STOFLOW_REFRESH_SESSION_RESPONSE' && msg.requestId === requestId) {
        responseSent = true;
        window.removeEventListener('message', responseListener);
        clearTimeout(timeoutId);

        VintedLogger.debug('🔄 [VINTED] Refresh session response:', msg);

        sendResponse({
          success: msg.success,
          error: msg.error || null
        });
      }
    };

    window.addEventListener('message', responseListener);

    const timeoutId = setTimeout(() => {
      if (responseSent) return;
      responseSent = true;
      window.removeEventListener('message', responseListener);
      VintedLogger.warn('🔄 [VINTED] Refresh session timeout');
      sendResponse({
        success: false,
        error: 'Refresh session timeout (10s)'
      });
    }, 10000);

    window.postMessage({
      type: 'STOFLOW_REFRESH_SESSION',
      requestId
    }, '*');

    VintedLogger.debug('🔄 [VINTED] Message STOFLOW_REFRESH_SESSION sent to injected script');

    return true; // Async response
  }
});

VintedLogger.debug('[Stoflow] Content script loaded');

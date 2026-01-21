/**
 * Stoflow Content Script for Vinted
 *
 * Extracts user data and provides API for communication with Vinted
 */

import { VintedLogger } from '../utils/logger';
import { sendPostMessageRequest } from './message-utils';

// Import the API injector - this injects stoflow-vinted-api.js into MAIN world
import './inject-api';

// ===== INITIALIZATION =====

VintedLogger.debug('🛍️ [STOFLOW VINTED] Content script loaded - URL:', window.location.href);

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
    VintedLogger.debug('📨 [VINTED] GET_VINTED_USER_INFO received');

    try {
      const userInfo = getVintedUserInfo();
      VintedLogger.debug('📨 ✅ User info extracted:', userInfo.login);
      sendResponse({
        success: true,
        data: {
          userId: userInfo.userId,
          login: userInfo.login
        }
      });
    } catch (error: any) {
      VintedLogger.error('📨 ❌ Extraction error:', error.message);
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
    VintedLogger.debug('👤 [VINTED] GET_VINTED_USER_PROFILE received');

    (async () => {
      // Try API call first
      const apiResponse = await sendPostMessageRequest({
        messageType: 'STOFLOW_API_CALL',
        responseType: 'STOFLOW_API_RESPONSE',
        payload: {
          method: 'GET',
          endpoint: '/users/current',
          params: {},
          data: null,
          config: {}
        },
        timeout: 10000,
        logContext: '👤 [PROFILE]'
      });

      if (apiResponse.success && apiResponse.data?.user) {
        const user = apiResponse.data.user;
        VintedLogger.debug('👤 ✅ API success! User:', user.login);

        sendResponse({
          success: true,
          source: 'api',
          data: {
            userId: user.id,
            login: user.login,
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
        });
        return;
      }

      // API failed - fallback to DOM parsing
      VintedLogger.warn('👤 ⚠️ API failed, fallback to DOM parsing:', apiResponse.error);

      try {
        const userInfo = getVintedUserInfo();
        sendResponse({
          success: true,
          source: 'dom',
          data: {
            userId: userInfo.userId,
            login: userInfo.login,
            stats: null
          }
        });
      } catch (domError: any) {
        VintedLogger.error('👤 ❌ Both API and DOM failed:', domError.message);
        sendResponse({
          success: false,
          error: `API: ${apiResponse.error}, DOM: ${domError.message}`
        });
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

    VintedLogger.debug(`📄 [VINTED] FETCH_HTML_PAGE: ${url}`);

    (async () => {
      const response = await sendPostMessageRequest({
        messageType: 'STOFLOW_FETCH_HTML',
        responseType: 'STOFLOW_FETCH_HTML_RESPONSE',
        payload: { url },
        logContext: '📄 [HTML]'
      });

      if (response.success) {
        sendResponse({
          success: true,
          status: response.status || 200,
          data: response.data
        });
      } else {
        sendResponse({
          success: false,
          status: response.status || 500,
          statusText: response.statusText || 'Error',
          error: response.error || 'Erreur fetch HTML'
        });
      }
    })();

    return true; // Async response
  }

  /**
   * VINTED_API_CALL - Generic Vinted API call using Webpack hook
   * Uses the vintedAPI bridge to make calls via Vinted's Axios instance
   */
  if (action === 'VINTED_API_CALL') {
    const { method, endpoint: rawEndpoint, data, config } = message;

    if (!method || !rawEndpoint) {
      sendResponse({ success: false, error: 'Invalid VINTED_API_CALL: missing method or endpoint' });
      return true;
    }

    // Remove /api/v2 prefix if present (avoid duplication - Axios baseURL already has it)
    let endpoint = rawEndpoint;
    if (endpoint.startsWith('/api/v2')) {
      endpoint = endpoint.replace('/api/v2', '');
    }

    (async () => {
      try {
        VintedLogger.debug(`[Stoflow] 🔄 VINTED_API_CALL: ${method} ${endpoint} (original: ${rawEndpoint})`);

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

        // CRITICAL: Clean response to ensure it's JSON-safe (no functions, no circular refs)
        // This prevents "Function object could not be cloned" error in sendResponse
        let cleanResponse;
        try {
          cleanResponse = JSON.parse(JSON.stringify(response));
        } catch (jsonError: any) {
          VintedLogger.warn(`JSON cleanup failed, manual extraction:`, jsonError.message);

          // CRITICAL FIX (2026-01-14): Extract only primitive fields manually
          // vintedAPI.get() returns data directly (not wrapped in {data: ...})
          if (response && typeof response === 'object') {
            cleanResponse = {};
            const skippedFields: string[] = [];

            for (const key in response) {
              if (!response.hasOwnProperty(key)) continue;

              const value = response[key];
              const valueType = typeof value;

              // Copy only primitive values and plain objects/arrays
              if (valueType === 'string' || valueType === 'number' || valueType === 'boolean' || value === null) {
                cleanResponse[key] = value;
              } else if (Array.isArray(value)) {
                try {
                  cleanResponse[key] = JSON.parse(JSON.stringify(value));
                } catch {
                  skippedFields.push(`${key}(array)`);
                }
              } else if (valueType === 'object') {
                try {
                  cleanResponse[key] = JSON.parse(JSON.stringify(value));
                } catch {
                  skippedFields.push(`${key}(object)`);
                }
              } else if (valueType === 'function') {
                skippedFields.push(`${key}(function)`);
              } else {
                skippedFields.push(`${key}(${valueType})`);
              }
            }

            if (skippedFields.length > 0) {
              VintedLogger.debug(`Manual cleanup: skipped fields: ${skippedFields.join(', ')}`);
            }
          } else {
            // Response is not an object - this should never happen
            cleanResponse = {
              _error: 'Response is not an object',
              _type: typeof response,
              _value: String(response)
            };
          }
        }

        sendResponse({
          success: true,
          status: 200,
          data: cleanResponse
        });
      } catch (error: any) {
        const httpStatus = error.status || 500;
        VintedLogger.error(`[Stoflow] ❌ VINTED_API_CALL error: HTTP ${httpStatus} - ${error.message}`);

        sendResponse({
          success: false,
          status: httpStatus,
          statusText: error.statusText || null,
          error: error.message || 'Unknown error',
          errorData: error.errorData || null  // Include error response data from Vinted API
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
    VintedLogger.debug('🛡️ [VINTED] DATADOME_PING received');

    (async () => {
      const response = await sendPostMessageRequest({
        messageType: 'STOFLOW_DATADOME_PING',
        responseType: 'STOFLOW_DATADOME_PING_RESPONSE',
        timeout: 10000,
        logContext: '🛡️ [DATADOME]'
      });

      sendResponse({
        success: response.success,
        data: response.data || { success: false, ping_count: 0 },
        error: response.error
      });
    })();

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

    VintedLogger.debug(`🌐 [VINTED] EXECUTE_VINTED_API: ${method} ${url}`);

    // Extract endpoint from URL (complete or relative)
    let endpoint: string;
    try {
      const urlObj = new URL(url);
      endpoint = urlObj.pathname + urlObj.search;
    } catch {
      endpoint = url;
    }

    // Remove /api/v2 prefix if present (avoid duplication)
    if (endpoint.startsWith('/api/v2')) {
      endpoint = endpoint.replace('/api/v2', '');
    }

    (async () => {
      const response = await sendPostMessageRequest({
        messageType: 'STOFLOW_API_CALL',
        responseType: 'STOFLOW_API_RESPONSE',
        payload: {
          method: method.toUpperCase(),
          endpoint,
          params,
          data: body,
          config: {}
        },
        logContext: '🌐 [API]'
      });

      if (response.success) {
        sendResponse({
          success: true,
          status: response.status || 200,
          data: response.data
        });
      } else {
        sendResponse({
          success: false,
          status: response.status || 500,
          error: response.error || 'Unknown error'
        });
      }
    })();

    return true; // Async response
  }

  /**
   * REFRESH_VINTED_SESSION - Refresh Vinted session cookies
   * Called by backend when a task returns 401
   * Uses /web/api/auth/refresh endpoint to regenerate session
   */
  if (action === 'REFRESH_VINTED_SESSION') {
    VintedLogger.debug('🔄 [VINTED] REFRESH_VINTED_SESSION received');

    (async () => {
      const response = await sendPostMessageRequest({
        messageType: 'STOFLOW_REFRESH_SESSION',
        responseType: 'STOFLOW_REFRESH_SESSION_RESPONSE',
        timeout: 10000,
        logContext: '🔄 [REFRESH]'
      });

      sendResponse({
        success: response.success,
        error: response.error || null
      });
    })();

    return true; // Async response
  }

  /**
   * VINTED_FETCH_USERS - Search for Vinted users via the users API
   * Used by admin prospect feature to find power sellers
   * Calls: GET /api/v2/users?search_text=X&per_page=100&page=Y
   */
  if (action === 'VINTED_FETCH_USERS') {
    const { search_text, page, per_page } = message;

    VintedLogger.debug(`👥 [VINTED] VINTED_FETCH_USERS: search="${search_text}", page=${page}, per_page=${per_page}`);

    (async () => {
      const response = await sendPostMessageRequest({
        messageType: 'STOFLOW_API_CALL',
        responseType: 'STOFLOW_API_RESPONSE',
        payload: {
          method: 'GET',
          endpoint: '/users',
          params: {
            search_text: search_text || '',
            page: page || 1,
            per_page: per_page || 100
          },
          data: null,
          config: {}
        },
        timeout: 30000,
        logContext: '👥 [USERS]'
      });

      if (response.success) {
        VintedLogger.debug(`👥 ✅ Users found: ${response.data?.users?.length || 0}`);
        sendResponse({
          success: true,
          status: response.status || 200,
          data: response.data
        });
      } else {
        VintedLogger.error(`👥 ❌ VINTED_FETCH_USERS error:`, response.error);
        sendResponse({
          success: false,
          status: response.status || 500,
          error: response.error || 'Unknown error'
        });
      }
    })();

    return true; // Async response
  }
});

VintedLogger.debug('[Stoflow] Content script loaded');

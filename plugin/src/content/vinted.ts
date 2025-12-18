/**
 * Stoflow Content Script for Vinted
 *
 * Extracts user data and provides API for communication with Vinted
 */

import { VintedLogger } from '../utils/logger';
import { ENV } from '../config/environment';

// Import the API injector - this injects stoflow-vinted-api.js into MAIN world
import './inject-api';

// ===== TYPES =====

interface VintedHeadersCache {
  csrfToken: string;
  anonId: string;
  lastUpdated: number;
  isReady: boolean;
}

interface VintedUserData {
  id: number | null;
  login: string;
  email: string;
  real_name: string;
  birthday: string;
  gender: string;
  city: string;
  city_id: number | null;
  country_id: number | null;
  country_code: string;
  country_title: string;
  currency: string;
  locale: string;
  profile_url: string;
  photo_url: string;
  about: string;
  created_at: string;
  feedback_count: number;
  feedback_reputation: number;
  positive_feedback_count: number;
  negative_feedback_count: number;
  neutral_feedback_count: number;
  item_count: number;
  total_items_count: number;
  followers_count: number;
  following_count: number;
  given_item_count: number;
  taken_item_count: number;
  business: boolean;
  business_account: {
    id: number | null;
    name: string;
    legal_name: string;
    legal_code: string;
    vat: string;
    email: string;
    phone_number: string;
    entity_type: string;
    status: string;
    address: {
      name: string;
      line1: string;
      line2: string;
      city: string;
      postal_code: string;
      country_code: string;
    } | null;
  } | null;
  default_address: {
    id: number | null;
    name: string;
    line1: string;
    line2: string;
    city: string;
    postal_code: string;
    country_code: string;
    phone_number: string;
  } | null;
  verification: {
    email: boolean;
    phone: boolean;
    google: boolean;
    facebook: boolean;
  };
  is_online: boolean;
  is_on_holiday: boolean;
  accepts_payments: boolean;
  has_confirmed_payments_account: boolean;
}

// ===== CONSTANTS =====

const CACHE_DURATION_MS = 5 * 60 * 1000; // 5 minutes

// ===== STATE =====

const headersCache: VintedHeadersCache = {
  csrfToken: '',
  anonId: '',
  lastUpdated: 0,
  isReady: false
};

// ===== EXTRACTION HELPERS =====

function createEmptyUserData(): VintedUserData {
  return {
    id: null,
    login: '',
    email: '',
    real_name: '',
    birthday: '',
    gender: '',
    city: '',
    city_id: null,
    country_id: null,
    country_code: '',
    country_title: '',
    currency: 'EUR',
    locale: 'fr',
    profile_url: '',
    photo_url: '',
    about: '',
    created_at: '',
    feedback_count: 0,
    feedback_reputation: 0,
    positive_feedback_count: 0,
    negative_feedback_count: 0,
    neutral_feedback_count: 0,
    item_count: 0,
    total_items_count: 0,
    followers_count: 0,
    following_count: 0,
    given_item_count: 0,
    taken_item_count: 0,
    business: false,
    business_account: null,
    default_address: null,
    verification: { email: false, phone: false, google: false, facebook: false },
    is_online: false,
    is_on_holiday: false,
    accepts_payments: false,
    has_confirmed_payments_account: false
  };
}

/**
 * Extracts data from Vinted's Next.js RSC scripts
 */
function extractVintedData(): {
  userId: number | null;
  anonId: string;
  csrfToken: string;
  user: VintedUserData | null;
} {
  let userId: number | null = null;
  let anonId = '';
  let csrfToken = '';
  let user: VintedUserData | null = null;

  const scripts = document.querySelectorAll('script:not([src])');

  for (const script of scripts) {
    const content = script.textContent || '';
    if (!content || content.length < 10) continue;

    // Extract CSRF Token
    if (!csrfToken) {
      const csrfMatch = content.match(/\\?"CSRF_TOKEN\\?"\s*:\s*\\?"([a-f0-9-]{36})\\?"/i) ||
                        content.match(/["']?CSRF_TOKEN["']?\s*[":]\s*["']([a-f0-9-]{36})["']/i);
      if (csrfMatch) csrfToken = csrfMatch[1];
    }

    // Extract Anon ID
    if (!anonId) {
      const anonMatch = content.match(/\\?"anon_id\\?"\s*:\s*\\?"([a-f0-9-]{36})\\?"/i) ||
                        content.match(/["']?anon_id["']?\s*[":]\s*["']([a-f0-9-]{36})["']/i);
      if (anonMatch) anonId = anonMatch[1];
    }

    // Extract currentUser data
    if (!user && content.includes('currentUser')) {
      const currentUserIdx = content.indexOf('currentUser');
      if (currentUserIdx === -1) continue;

      // Extract context around currentUser (30KB should be enough for all user data)
      const userContext = content.substring(currentUserIdx, currentUserIdx + 30000);

      // Helper functions for extraction within userContext
      const extractString = (field: string): string => {
        const escapedMatch = userContext.match(new RegExp(`\\\\"${field}\\\\":\\s*\\\\"([^\\\\"]*)\\\\"`));
        if (escapedMatch) return escapedMatch[1];
        const normalMatch = userContext.match(new RegExp(`"${field}":\\s*"([^"]*)"`));
        return normalMatch ? normalMatch[1] : '';
      };

      const extractNumber = (field: string): number | null => {
        const escapedMatch = userContext.match(new RegExp(`\\\\"${field}\\\\":\\s*(\\d+)`));
        if (escapedMatch) return parseInt(escapedMatch[1]);
        const normalMatch = userContext.match(new RegExp(`"${field}":\\s*(\\d+)`));
        return normalMatch ? parseInt(normalMatch[1]) : null;
      };

      const extractBoolean = (field: string): boolean => {
        const escapedMatch = userContext.match(new RegExp(`\\\\"${field}\\\\":\\s*(true|false)`));
        if (escapedMatch) return escapedMatch[1] === 'true';
        const normalMatch = userContext.match(new RegExp(`"${field}":\\s*(true|false)`));
        return normalMatch ? normalMatch[1] === 'true' : false;
      };

      const extractFloat = (field: string): number => {
        const escapedMatch = userContext.match(new RegExp(`\\\\"${field}\\\\":\\s*([\\d.]+)`));
        if (escapedMatch) return parseFloat(escapedMatch[1]);
        const normalMatch = userContext.match(new RegExp(`"${field}":\\s*([\\d.]+)`));
        return normalMatch ? parseFloat(normalMatch[1]) : 0;
      };

      // Create user object
      user = createEmptyUserData();

      // Identity
      user.id = extractNumber('id');
      user.login = extractString('login');
      user.email = extractString('email');
      user.real_name = extractString('real_name');
      user.birthday = extractString('birthday');
      user.gender = extractString('gender');

      // Location
      user.city = extractString('city');
      user.city_id = extractNumber('city_id');
      user.country_id = extractNumber('country_id');
      user.country_code = extractString('country_code');
      user.country_title = extractString('country_title');
      user.currency = extractString('currency') || 'EUR';
      user.locale = extractString('locale') || extractString('iso_locale_code') || 'fr';

      // Profile
      user.profile_url = extractString('profile_url');
      user.created_at = extractString('created_at');
      const photoUrlMatch = userContext.match(/\\"photo\\":\s*\{[^}]*\\"url\\":\s*\\"([^"\\]+)\\"/);
      if (photoUrlMatch) user.photo_url = photoUrlMatch[1];

      // Statistics
      user.feedback_count = extractNumber('feedback_count') || 0;
      user.feedback_reputation = extractFloat('feedback_reputation');
      user.positive_feedback_count = extractNumber('positive_feedback_count') || 0;
      user.negative_feedback_count = extractNumber('negative_feedback_count') || 0;
      user.neutral_feedback_count = extractNumber('neutral_feedback_count') || 0;
      user.item_count = extractNumber('item_count') || 0;
      user.total_items_count = extractNumber('total_items_count') || 0;
      user.followers_count = extractNumber('followers_count') || 0;
      user.following_count = extractNumber('following_count') || 0;
      user.given_item_count = extractNumber('given_item_count') || 0;
      user.taken_item_count = extractNumber('taken_item_count') || 0;

      // Business
      user.business = extractBoolean('business');
      if (user.business) {
        const legalName = extractString('legal_name');
        const legalCode = extractString('legal_code');
        if (legalName || legalCode) {
          user.business_account = {
            id: extractNumber('business_account_id'),
            name: extractString('name'),
            legal_name: legalName,
            legal_code: legalCode,
            vat: extractString('vat'),
            email: '',
            phone_number: extractString('phone_number'),
            entity_type: extractString('entity_type'),
            status: extractString('status'),
            address: null
          };

          const addressMatch = userContext.match(/\\"address\\":\s*\{[^}]*\\"line1\\":\s*\\"([^"\\]*)\\"/);
          if (addressMatch) {
            user.business_account.address = {
              name: extractString('name'),
              line1: addressMatch[1],
              line2: '',
              city: user.city,
              postal_code: extractString('postal_code'),
              country_code: extractString('country_code')
            };
          }
        }
      }

      // Verification status
      const emailValid = userContext.match(/\\"email\\":\s*\{\s*\\"valid\\":\s*(true|false)/);
      const phoneValid = userContext.match(/\\"phone\\":\s*\{\s*\\"valid\\":\s*(true|false)/);
      const googleValid = userContext.match(/\\"google\\":\s*\{\s*\\"valid\\":\s*(true|false)/);
      const facebookValid = userContext.match(/\\"facebook\\":\s*\{\s*\\"valid\\":\s*(true|false)/);
      user.verification = {
        email: emailValid ? emailValid[1] === 'true' : false,
        phone: phoneValid ? phoneValid[1] === 'true' : false,
        google: googleValid ? googleValid[1] === 'true' : false,
        facebook: facebookValid ? facebookValid[1] === 'true' : false
      };

      // Other flags
      user.is_on_holiday = extractBoolean('is_on_holiday');
      user.accepts_payments = extractBoolean('accepts_payments');
      user.has_confirmed_payments_account = extractBoolean('has_confirmed_payments_account');

      if (user.id) userId = user.id;
    }

    // Extract userId if not found yet
    if (!userId) {
      const userIdMatch = content.match(/\\?"userId\\?"\s*:\s*\\?"?(\d+)/) ||
                          content.match(/["']?userId["']?\s*[":]\s*["']?(\d+)["']?/i);
      if (userIdMatch) userId = parseInt(userIdMatch[1]);
    }

    // Stop if we have everything
    if (csrfToken && anonId && user && user.email) break;
  }

  // Fallback: extract login if user not found
  if (!user) {
    for (const script of scripts) {
      const content = script.textContent || '';
      if (content.includes('currentUser') || content.includes('login')) {
        const loginMatch = content.match(/\\?"login\\?"\s*:\s*\\?"([^"\\]+)\\?"/);
        if (loginMatch && loginMatch[1] && !loginMatch[1].startsWith('$') && loginMatch[1].length > 1) {
          user = createEmptyUserData();
          user.id = userId;
          user.login = loginMatch[1];
          break;
        }
      }
    }
  }

  if (user && !user.id && userId) user.id = userId;

  return { userId, anonId, csrfToken, user };
}

// ===== HEADERS CACHE =====

function refreshHeadersCache(): boolean {
  const data = extractVintedData();

  headersCache.csrfToken = data.csrfToken;
  headersCache.anonId = data.anonId;
  headersCache.lastUpdated = Date.now();
  headersCache.isReady = !!(data.csrfToken && data.anonId);

  return headersCache.isReady;
}

function ensureHeadersReady(): boolean {
  const cacheExpired = (Date.now() - headersCache.lastUpdated) > CACHE_DURATION_MS;
  if (!headersCache.isReady || cacheExpired) {
    return refreshHeadersCache();
  }
  return headersCache.isReady;
}

async function waitForHeaders(maxAttempts = 10, delayMs = 500): Promise<boolean> {
  for (let i = 0; i < maxAttempts; i++) {
    if (ensureHeadersReady()) return true;
    await new Promise(resolve => setTimeout(resolve, delayMs));
  }
  return false;
}

function getVintedHeaders(): Record<string, string> {
  ensureHeadersReady();
  return {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'fr',
    'X-Money-Object': 'true',
    'X-CSRF-Token': headersCache.csrfToken,
    'X-Anon-Id': headersCache.anonId,
    'Referer': window.location.href,
  };
}

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

if (document.readyState === 'complete') {
  VintedLogger.debug('[Stoflow] Document ready, initialisation...');
  refreshHeadersCache();
} else {
  VintedLogger.debug('[Stoflow] En attente du chargement de la page...');
  window.addEventListener('load', () => {
    VintedLogger.debug('[Stoflow] Page chargée, initialisation...');
    refreshHeadersCache();
  });
}

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    refreshHeadersCache();
  }
});

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
   * GET_VINTED_USER_INFO - Extract userId + login from Vinted page
   * Used by check_vinted_connection task
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
   * EXECUTE_HTTP_REQUEST - Execute HTTP request with Vinted cookies/headers
   * Used by useHttpProxy composable
   */
  if (action === 'EXECUTE_HTTP_REQUEST') {
    const req = message.request;
    if (!req?.url || !req?.method) {
      sendResponse({ success: false, error: 'Invalid request' });
      return true;
    }

    (async () => {
      try {
        if (!(await waitForHeaders())) {
          sendResponse({ success: false, error: 'Headers not available' });
          return;
        }

        const mergedHeaders = { ...getVintedHeaders(), ...(req.headers || {}) };
        const fetchOptions: RequestInit = {
          method: req.method,
          headers: mergedHeaders,
          credentials: req.credentials || 'include'
        };

        if (req.body && !['GET', 'HEAD'].includes(req.method.toUpperCase())) {
          fetchOptions.body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body);
        }

        const response = await fetch(req.url, fetchOptions);
        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json')
          ? await response.json()
          : await response.text();

        const responseHeaders: Record<string, string> = {};
        response.headers.forEach((value, key) => { responseHeaders[key] = value; });

        sendResponse({
          success: response.ok,
          status: response.status,
          headers: responseHeaders,
          data
        });
      } catch (error: any) {
        sendResponse({ success: false, error: error.message || 'Unknown error' });
      }
    })();
    return true;
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
});

VintedLogger.debug('[Stoflow] Content script loaded');

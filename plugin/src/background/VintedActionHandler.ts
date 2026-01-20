/**
 * VintedActionHandler - Handles Vinted actions from stoflow.io via externally_connectable
 *
 * This module replaces the polling-based task system with direct request/response communication.
 * All Vinted operations are initiated by the frontend and executed synchronously.
 *
 * Author: Claude
 * Date: 2026-01-06
 */

import { BackgroundLogger } from '../utils/logger';
import { validateRequest } from '../utils/domain-validator';
import { isAllowedOrigin } from '../config/origins';

// Note: Rate limiting is handled at the backend level (VintedRateLimiter)
// The plugin only executes requests as instructed by the backend

// ============================================================
// TYPES
// ============================================================

export interface ExternalMessage {
  action: string;
  requestId?: string;
  payload?: any;
}

export interface ExternalResponse {
  success: boolean;
  requestId?: string;
  data?: any;
  error?: string;
  errorCode?: string;
}

interface VintedTab {
  id: number;
  url: string;
}

// Re-export isAllowedOrigin for backward compatibility
export { isAllowedOrigin } from '../config/origins';

// ============================================================
// VINTED TAB MANAGEMENT
// ============================================================

/**
 * Find an open Vinted tab
 */
async function findVintedTab(): Promise<VintedTab | null> {
  BackgroundLogger.debug('[VintedHandler] 🔍 Searching for Vinted tab...');
  try {
    const tabs = await chrome.tabs.query({
      url: ['*://www.vinted.fr/*', '*://www.vinted.com/*']
    });

    if (tabs.length > 0 && tabs[0].id) {
      BackgroundLogger.info(`[VintedHandler] ✅ Found Vinted tab: id=${tabs[0].id}, url=${tabs[0].url}`);
      return { id: tabs[0].id, url: tabs[0].url || '' };
    }

    BackgroundLogger.warn('[VintedHandler] ❌ No Vinted tab found');
    return null;
  } catch (error) {
    BackgroundLogger.error('[VintedHandler] Error finding Vinted tab:', error);
    return null;
  }
}

/**
 * Open a new Vinted tab
 */
async function openVintedTab(url?: string): Promise<VintedTab | null> {
  try {
    const targetUrl = url || 'https://www.vinted.fr';
    const tab = await chrome.tabs.create({ url: targetUrl, active: false });

    if (!tab.id) return null;

    // Wait for the tab to load
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        chrome.tabs.onUpdated.removeListener(listener);
        reject(new Error('Tab load timeout'));
      }, 30000);

      const listener = (tabId: number, info: chrome.tabs.TabChangeInfo) => {
        if (tabId === tab.id && info.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          clearTimeout(timeout);
          resolve();
        }
      };

      chrome.tabs.onUpdated.addListener(listener);
    });

    return { id: tab.id, url: tab.url || targetUrl };
  } catch (error) {
    BackgroundLogger.error('[VintedHandler] Error opening Vinted tab:', error);
    return null;
  }
}

/**
 * Ensure a Vinted tab is available, return error response if not
 */
async function ensureVintedTab(): Promise<{ tab: VintedTab | null; error?: ExternalResponse }> {
  const tab = await findVintedTab();

  if (!tab) {
    return {
      tab: null,
      error: {
        success: false,
        errorCode: 'NO_VINTED_TAB',
        error: 'No Vinted tab found. Please open www.vinted.fr in a browser tab.'
      }
    };
  }

  return { tab };
}

// ============================================================
// CONTENT SCRIPT COMMUNICATION
// ============================================================

/**
 * Send a message to the Vinted content script and wait for response
 *
 * Note: Rate limiting is handled at the backend level (VintedRateLimiter)
 *
 * @param tabId - Target tab ID
 * @param action - Action to perform
 * @param payload - Optional payload (may contain 'method' for HTTP method)
 * @param timeout - Request timeout in ms
 */
async function sendToContentScript(
  tabId: number,
  action: string,
  payload?: any,
  timeout: number = 30000
): Promise<any> {
  const httpMethod = payload?.method?.toUpperCase() || 'GET';

  BackgroundLogger.info(`[VintedHandler] 📤 Sending to content script: tabId=${tabId}, action=${action}, method=${httpMethod}`);
  if (payload) {
    BackgroundLogger.debug('[VintedHandler] 📤 Payload:', JSON.stringify(payload).substring(0, 500));
  }

  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      BackgroundLogger.error(`[VintedHandler] ⏱️ Content script timeout after ${timeout}ms`);
      reject(new Error('Content script timeout'));
    }, timeout);

    chrome.tabs.sendMessage(tabId, { action, ...payload }, (response) => {
      clearTimeout(timeoutId);

      if (chrome.runtime.lastError) {
        BackgroundLogger.error('[VintedHandler] ❌ chrome.runtime.lastError:', chrome.runtime.lastError.message);
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }

      BackgroundLogger.info(`[VintedHandler] 📥 Response from content script: success=${response?.success}`);
      if (response?.error) {
        BackgroundLogger.warn('[VintedHandler] 📥 Response error:', response.error);
      }
      if (response?.data) {
        BackgroundLogger.debug('[VintedHandler] 📥 Response data:', JSON.stringify(response.data).substring(0, 500));
      }

      resolve(response);
    });
  });
}

// ============================================================
// VINTED ACTION HANDLERS
// ============================================================

/**
 * Check if a Vinted tab is open
 */
async function handleCheckVintedTab(requestId?: string): Promise<ExternalResponse> {
  const tab = await findVintedTab();

  return {
    success: true,
    requestId,
    data: {
      hasVintedTab: !!tab,
      tabId: tab?.id,
      tabUrl: tab?.url
    }
  };
}

/**
 * Open a Vinted tab
 */
async function handleOpenVintedTab(requestId?: string, url?: string): Promise<ExternalResponse> {
  const tab = await openVintedTab(url);

  if (!tab) {
    return {
      success: false,
      requestId,
      errorCode: 'TAB_OPEN_FAILED',
      error: 'Failed to open Vinted tab'
    };
  }

  return {
    success: true,
    requestId,
    data: { tabId: tab.id, tabUrl: tab.url }
  };
}

/**
 * Get Vinted user info
 */
async function handleGetUserInfo(requestId?: string): Promise<ExternalResponse> {
  const { tab, error } = await ensureVintedTab();
  if (error) return { ...error, requestId };

  try {
    const response = await sendToContentScript(tab!.id, 'GET_VINTED_USER_INFO');

    if (!response?.success) {
      return {
        success: false,
        requestId,
        errorCode: 'USER_INFO_FAILED',
        error: response?.error || 'Failed to get user info'
      };
    }

    return {
      success: true,
      requestId,
      data: response.data
    };
  } catch (error: any) {
    return {
      success: false,
      requestId,
      errorCode: 'CONTENT_SCRIPT_ERROR',
      error: error.message
    };
  }
}

/**
 * Get Vinted user profile (more detailed)
 */
async function handleGetUserProfile(requestId?: string): Promise<ExternalResponse> {
  const { tab, error } = await ensureVintedTab();
  if (error) return { ...error, requestId };

  try {
    const response = await sendToContentScript(tab!.id, 'GET_VINTED_USER_PROFILE');

    return {
      success: response?.success ?? false,
      requestId,
      data: response?.data,
      error: response?.error,
      errorCode: response?.success ? undefined : 'PROFILE_FAILED'
    };
  } catch (error: any) {
    return {
      success: false,
      requestId,
      errorCode: 'CONTENT_SCRIPT_ERROR',
      error: error.message
    };
  }
}

/**
 * Execute a generic Vinted API call
 */
async function handleVintedApiCall(
  requestId?: string,
  payload?: { method: string; endpoint: string; data?: any; params?: any }
): Promise<ExternalResponse> {
  const { tab, error } = await ensureVintedTab();
  if (error) return { ...error, requestId };

  if (!payload?.method || !payload?.endpoint) {
    return {
      success: false,
      requestId,
      errorCode: 'INVALID_PAYLOAD',
      error: 'method and endpoint are required'
    };
  }

  // Security: Validate endpoint and method against whitelist
  const validation = validateRequest(payload.endpoint, payload.method);
  if (!validation.valid) {
    BackgroundLogger.warn(`[VintedHandler] Blocked request: ${payload.method} ${payload.endpoint} - ${validation.error}`);
    return {
      success: false,
      requestId,
      errorCode: validation.errorCode || 'FORBIDDEN_ENDPOINT',
      error: validation.error || 'Request blocked by security policy'
    };
  }

  try {
    const response = await sendToContentScript(tab!.id, 'VINTED_API_CALL', {
      method: payload.method,
      endpoint: payload.endpoint,
      data: payload.data,
      params: payload.params
    });

    return {
      success: response?.success ?? false,
      requestId,
      data: response?.data,
      error: response?.error,
      errorCode: response?.success ? undefined : 'API_CALL_FAILED'
    };
  } catch (error: any) {
    return {
      success: false,
      requestId,
      errorCode: 'CONTENT_SCRIPT_ERROR',
      error: error.message
    };
  }
}

/**
 * Get user's wardrobe items
 */
async function handleGetWardrobe(
  requestId?: string,
  payload?: { userId: string; page?: number; perPage?: number }
): Promise<ExternalResponse> {
  const { tab, error } = await ensureVintedTab();
  if (error) return { ...error, requestId };

  if (!payload?.userId) {
    return {
      success: false,
      requestId,
      errorCode: 'INVALID_PAYLOAD',
      error: 'userId is required'
    };
  }

  try {
    const response = await sendToContentScript(tab!.id, 'VINTED_API_CALL', {
      method: 'GET',
      endpoint: `/users/${payload.userId}/items`,
      params: {
        page: payload.page || 1,
        per_page: payload.perPage || 96
      }
    });

    return {
      success: response?.success ?? false,
      requestId,
      data: response?.data,
      error: response?.error,
      errorCode: response?.success ? undefined : 'WARDROBE_FAILED'
    };
  } catch (error: any) {
    return {
      success: false,
      requestId,
      errorCode: 'CONTENT_SCRIPT_ERROR',
      error: error.message
    };
  }
}

/**
 * Publish a product to Vinted
 */
async function handlePublishProduct(
  requestId?: string,
  payload?: any
): Promise<ExternalResponse> {
  const { tab, error } = await ensureVintedTab();
  if (error) return { ...error, requestId };

  if (!payload) {
    return {
      success: false,
      requestId,
      errorCode: 'INVALID_PAYLOAD',
      error: 'Product data is required'
    };
  }

  try {
    const response = await sendToContentScript(tab!.id, 'VINTED_API_CALL', {
      method: 'POST',
      endpoint: '/items',
      data: payload
    });

    return {
      success: response?.success ?? false,
      requestId,
      data: response?.data,
      error: response?.error,
      errorCode: response?.success ? undefined : 'PUBLISH_FAILED'
    };
  } catch (error: any) {
    return {
      success: false,
      requestId,
      errorCode: 'CONTENT_SCRIPT_ERROR',
      error: error.message
    };
  }
}

/**
 * Update a product on Vinted
 */
async function handleUpdateProduct(
  requestId?: string,
  payload?: { vintedId: string; updates: any }
): Promise<ExternalResponse> {
  const { tab, error } = await ensureVintedTab();
  if (error) return { ...error, requestId };

  if (!payload?.vintedId || !payload?.updates) {
    return {
      success: false,
      requestId,
      errorCode: 'INVALID_PAYLOAD',
      error: 'vintedId and updates are required'
    };
  }

  try {
    const response = await sendToContentScript(tab!.id, 'VINTED_API_CALL', {
      method: 'PUT',
      endpoint: `/items/${payload.vintedId}`,
      data: payload.updates
    });

    return {
      success: response?.success ?? false,
      requestId,
      data: response?.data,
      error: response?.error,
      errorCode: response?.success ? undefined : 'UPDATE_FAILED'
    };
  } catch (error: any) {
    return {
      success: false,
      requestId,
      errorCode: 'CONTENT_SCRIPT_ERROR',
      error: error.message
    };
  }
}

/**
 * Delete a product from Vinted
 */
async function handleDeleteProduct(
  requestId?: string,
  payload?: { vintedId: string }
): Promise<ExternalResponse> {
  const { tab, error } = await ensureVintedTab();
  if (error) return { ...error, requestId };

  if (!payload?.vintedId) {
    return {
      success: false,
      requestId,
      errorCode: 'INVALID_PAYLOAD',
      error: 'vintedId is required'
    };
  }

  try {
    const response = await sendToContentScript(tab!.id, 'VINTED_API_CALL', {
      method: 'DELETE',
      endpoint: `/items/${payload.vintedId}`
    });

    return {
      success: response?.success ?? false,
      requestId,
      data: response?.data,
      error: response?.error,
      errorCode: response?.success ? undefined : 'DELETE_FAILED'
    };
  } catch (error: any) {
    return {
      success: false,
      requestId,
      errorCode: 'CONTENT_SCRIPT_ERROR',
      error: error.message
    };
  }
}

/**
 * Ping - Check if extension is alive and get version
 */
async function handlePing(requestId?: string): Promise<ExternalResponse> {
  return {
    success: true,
    requestId,
    data: {
      status: 'ready',
      version: chrome.runtime.getManifest().version,
      timestamp: Date.now()
    }
  };
}

// ============================================================
// MAIN MESSAGE HANDLER
// ============================================================

/**
 * Main handler for external messages from stoflow.io
 */
export async function handleExternalMessage(message: ExternalMessage): Promise<ExternalResponse> {
  const { action, requestId, payload } = message;

  BackgroundLogger.info(`[VintedHandler] ═══════════════════════════════════════════════`);
  BackgroundLogger.info(`[VintedHandler] 🎯 Processing action: ${action}`);
  BackgroundLogger.info(`[VintedHandler] 📋 Request ID: ${requestId || 'none'}`);
  if (payload) {
    BackgroundLogger.debug(`[VintedHandler] 📦 Payload:`, JSON.stringify(payload).substring(0, 300));
  }

  const startTime = Date.now();

  try {
    let result: ExternalResponse;

    switch (action) {
      // ============ STATUS & DETECTION ============
      case 'PING':
        result = await handlePing(requestId);
        break;

      case 'CHECK_VINTED_TAB':
        result = await handleCheckVintedTab(requestId);
        break;

      case 'OPEN_VINTED_TAB':
        result = await handleOpenVintedTab(requestId, payload?.url);
        break;

      // ============ USER INFO ============
      case 'VINTED_GET_USER_INFO':
        result = await handleGetUserInfo(requestId);
        break;

      case 'VINTED_GET_USER_PROFILE':
        result = await handleGetUserProfile(requestId);
        break;

      // ============ VINTED API ============
      case 'VINTED_API_CALL':
        result = await handleVintedApiCall(requestId, payload);
        break;

      case 'VINTED_GET_WARDROBE':
        result = await handleGetWardrobe(requestId, payload);
        break;

      // ============ PRODUCT OPERATIONS ============
      case 'VINTED_PUBLISH':
        result = await handlePublishProduct(requestId, payload);
        break;

      case 'VINTED_UPDATE':
        result = await handleUpdateProduct(requestId, payload);
        break;

      case 'VINTED_DELETE':
        result = await handleDeleteProduct(requestId, payload);
        break;

      // ============ UNKNOWN ============
      default:
        result = {
          success: false,
          requestId,
          errorCode: 'UNKNOWN_ACTION',
          error: `Unknown action: ${action}`
        };
    }

    const duration = Date.now() - startTime;
    if (result.success) {
      BackgroundLogger.info(`[VintedHandler] ✅ Action ${action} completed in ${duration}ms`);
    } else {
      BackgroundLogger.error(`[VintedHandler] ❌ Action ${action} failed in ${duration}ms: ${result.error}`);
    }
    BackgroundLogger.info(`[VintedHandler] ═══════════════════════════════════════════════`);

    return result;
  } catch (error: any) {
    const duration = Date.now() - startTime;
    BackgroundLogger.error(`[VintedHandler] 💥 Exception in ${action} after ${duration}ms:`, error);
    BackgroundLogger.info(`[VintedHandler] ═══════════════════════════════════════════════`);

    return {
      success: false,
      requestId,
      errorCode: 'HANDLER_ERROR',
      error: error.message
    };
  }
}

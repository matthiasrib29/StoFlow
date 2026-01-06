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

// ============================================================
// ALLOWED ORIGINS
// ============================================================

const ALLOWED_ORIGINS = [
  'https://stoflow.io',
  'https://www.stoflow.io',
  'https://app.stoflow.io',
  'http://localhost:3000',
  'http://localhost:5173'
];

/**
 * Verify if the sender origin is allowed
 */
export function isAllowedOrigin(senderUrl: string | undefined): boolean {
  if (!senderUrl) return false;

  try {
    const origin = new URL(senderUrl).origin;
    return ALLOWED_ORIGINS.some(allowed =>
      origin === allowed || origin.startsWith(allowed.replace('/*', ''))
    );
  } catch {
    return false;
  }
}

// ============================================================
// VINTED TAB MANAGEMENT
// ============================================================

/**
 * Find an open Vinted tab
 */
async function findVintedTab(): Promise<VintedTab | null> {
  try {
    const tabs = await chrome.tabs.query({
      url: ['*://www.vinted.fr/*', '*://www.vinted.com/*']
    });

    if (tabs.length > 0 && tabs[0].id) {
      return { id: tabs[0].id, url: tabs[0].url || '' };
    }

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
 */
async function sendToContentScript(
  tabId: number,
  action: string,
  payload?: any,
  timeout: number = 30000
): Promise<any> {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(new Error('Content script timeout'));
    }, timeout);

    chrome.tabs.sendMessage(tabId, { action, ...payload }, (response) => {
      clearTimeout(timeoutId);

      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
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
 * Execute a batch of Vinted operations
 */
async function handleBatchExecute(
  requestId?: string,
  payload?: { operations: Array<{ action: string; payload?: any }> }
): Promise<ExternalResponse> {
  if (!payload?.operations || !Array.isArray(payload.operations)) {
    return {
      success: false,
      requestId,
      errorCode: 'INVALID_PAYLOAD',
      error: 'operations array is required'
    };
  }

  const results: Array<{ index: number; success: boolean; data?: any; error?: string }> = [];

  for (let i = 0; i < payload.operations.length; i++) {
    const op = payload.operations[i];

    try {
      const result = await handleExternalMessage({
        action: op.action,
        payload: op.payload
      });

      results.push({
        index: i,
        success: result.success,
        data: result.data,
        error: result.error
      });

      // Small delay between operations to avoid rate limiting
      if (i < payload.operations.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    } catch (error: any) {
      results.push({
        index: i,
        success: false,
        error: error.message
      });
    }
  }

  const successCount = results.filter(r => r.success).length;

  return {
    success: successCount === results.length,
    requestId,
    data: {
      results,
      total: results.length,
      succeeded: successCount,
      failed: results.length - successCount
    }
  };
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

  BackgroundLogger.debug(`[VintedHandler] Processing action: ${action}`, { requestId });

  try {
    switch (action) {
      // ============ STATUS & DETECTION ============
      case 'PING':
        return handlePing(requestId);

      case 'CHECK_VINTED_TAB':
        return handleCheckVintedTab(requestId);

      case 'OPEN_VINTED_TAB':
        return handleOpenVintedTab(requestId, payload?.url);

      // ============ USER INFO ============
      case 'VINTED_GET_USER_INFO':
        return handleGetUserInfo(requestId);

      case 'VINTED_GET_USER_PROFILE':
        return handleGetUserProfile(requestId);

      // ============ VINTED API ============
      case 'VINTED_API_CALL':
        return handleVintedApiCall(requestId, payload);

      case 'VINTED_GET_WARDROBE':
        return handleGetWardrobe(requestId, payload);

      // ============ PRODUCT OPERATIONS ============
      case 'VINTED_PUBLISH':
        return handlePublishProduct(requestId, payload);

      case 'VINTED_UPDATE':
        return handleUpdateProduct(requestId, payload);

      case 'VINTED_DELETE':
        return handleDeleteProduct(requestId, payload);

      // ============ BATCH ============
      case 'VINTED_BATCH':
        return handleBatchExecute(requestId, payload);

      // ============ UNKNOWN ============
      default:
        // Return null to indicate this action should be handled elsewhere
        return {
          success: false,
          requestId,
          errorCode: 'UNKNOWN_ACTION',
          error: `Unknown action: ${action}`
        };
    }
  } catch (error: any) {
    BackgroundLogger.error(`[VintedHandler] Error handling ${action}:`, error);

    return {
      success: false,
      requestId,
      errorCode: 'HANDLER_ERROR',
      error: error.message
    };
  }
}

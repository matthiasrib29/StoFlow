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
import { registerVintedOperation, unregisterVintedOperation } from './index';
import { TIMEOUTS, RATE_LIMIT } from '../config/constants';

// ============================================================
// SECURITY: LOCAL RATE LIMITING - Prevent request flooding
// ============================================================

/**
 * Request queue with concurrency control and rate limiting.
 * Prevents flooding even if the backend rate limiter is bypassed.
 */
class RequestQueue {
  private queue: Array<{
    executor: () => Promise<any>;
    resolve: (value: any) => void;
    reject: (error: any) => void;
  }> = [];
  private activeRequests = 0;
  private readonly maxConcurrent = RATE_LIMIT.MAX_CONCURRENT;
  private readonly maxQueueSize = RATE_LIMIT.MAX_QUEUE_SIZE;

  /**
   * Add a request to the queue
   * @throws Error if queue is full
   */
  async enqueue<T>(executor: () => Promise<T>): Promise<T> {
    if (this.queue.length >= this.maxQueueSize) {
      BackgroundLogger.warn('[RateLimit] Queue full, rejecting request');
      throw new Error('Request queue full - too many pending requests');
    }

    return new Promise((resolve, reject) => {
      this.queue.push({ executor, resolve, reject });
      this.processNext();
    });
  }

  /**
   * Process the next request in the queue
   */
  private async processNext(): Promise<void> {
    if (this.activeRequests >= this.maxConcurrent || this.queue.length === 0) {
      return;
    }

    this.activeRequests++;
    const { executor, resolve, reject } = this.queue.shift()!;

    try {
      const result = await executor();
      resolve(result);
    } catch (error) {
      reject(error);
    } finally {
      this.activeRequests--;
      this.processNext();
    }
  }

  /**
   * Get current queue stats
   */
  getStats() {
    return {
      active: this.activeRequests,
      pending: this.queue.length,
      maxConcurrent: this.maxConcurrent,
      maxQueueSize: this.maxQueueSize
    };
  }
}

const requestQueue = new RequestQueue();

// ============================================================
// CANCEL TOKEN - Prevent processing of late responses after timeout
// ============================================================

/**
 * CancelToken allows cancelling a request after timeout or tab closure.
 * When cancelled, late responses are ignored to prevent race conditions.
 */
class CancelToken {
  private cancelled = false;
  private callbacks: Array<() => void> = [];

  /**
   * Cancel the operation. Any late responses will be ignored.
   */
  cancel(): void {
    if (!this.cancelled) {
      this.cancelled = true;
      this.callbacks.forEach(cb => cb());
      this.callbacks = [];
    }
  }

  /**
   * Check if the operation has been cancelled.
   */
  isCancelled(): boolean {
    return this.cancelled;
  }

  /**
   * Register a callback to be called when the token is cancelled.
   */
  onCancel(callback: () => void): void {
    if (this.cancelled) {
      callback();
    } else {
      this.callbacks.push(callback);
    }
  }
}

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
// SESSION VERIFICATION
// ============================================================

interface SessionStatus {
  hasSession: boolean;
  isExpired: boolean;
  error?: string;
}

/**
 * Verify that Vinted tab has a valid session before operations.
 * Checks cookies via chrome.cookies API (not storage).
 *
 * SECURITY: This function reads cookies directly without storing them.
 */
async function verifyVintedSession(): Promise<SessionStatus> {
  try {
    const cookies = await chrome.cookies.getAll({ domain: '.vinted.fr' });

    // Check for session cookies (v_sid is the main session, _vinted_fr_session is backup)
    const sessionCookie = cookies.find(c =>
      c.name === 'v_sid' || c.name === '_vinted_fr_session'
    );

    if (!sessionCookie) {
      BackgroundLogger.warn('[VintedHandler] No Vinted session cookie found');
      return { hasSession: false, isExpired: false, error: 'No session cookie found' };
    }

    // Check expiration (if expirationDate is set)
    if (sessionCookie.expirationDate) {
      const now = Date.now() / 1000; // Convert to seconds
      if (sessionCookie.expirationDate < now) {
        BackgroundLogger.warn('[VintedHandler] Vinted session cookie expired');
        return { hasSession: true, isExpired: true, error: 'Session cookie expired' };
      }
    }

    BackgroundLogger.debug('[VintedHandler] Vinted session verified');
    return { hasSession: true, isExpired: false };
  } catch (error: any) {
    BackgroundLogger.error('[VintedHandler] Session verification error:', error);
    return { hasSession: false, isExpired: false, error: error.message };
  }
}

// ============================================================
// VINTED TAB MANAGEMENT
// ============================================================

/**
 * Find the best Vinted tab to use.
 * Priority: 1) Active tab, 2) Most recently accessed, 3) First found
 *
 * This prevents issues when multiple Vinted tabs are open.
 */
async function findVintedTab(): Promise<VintedTab | null> {
  BackgroundLogger.debug('[VintedHandler] 🔍 Searching for Vinted tab...');

  try {
    const tabs = await chrome.tabs.query({
      url: ['*://www.vinted.fr/*', '*://www.vinted.com/*']
    });

    if (tabs.length === 0) {
      BackgroundLogger.warn('[VintedHandler] ❌ No Vinted tab found');
      return null;
    }

    // If only one tab, return it
    if (tabs.length === 1 && tabs[0].id) {
      BackgroundLogger.info(`[VintedHandler] ✅ Found single Vinted tab: id=${tabs[0].id}`);
      return { id: tabs[0].id, url: tabs[0].url || '' };
    }

    // Multiple tabs: prioritize active tab
    const activeTab = tabs.find(t => t.active);
    if (activeTab?.id) {
      BackgroundLogger.info(`[VintedHandler] ✅ Using active Vinted tab: id=${activeTab.id}`);
      return { id: activeTab.id, url: activeTab.url || '' };
    }

    // No active tab: use most recently accessed (highest lastAccessed timestamp)
    const sortedTabs = tabs
      .filter(t => t.id !== undefined)
      .sort((a, b) => (b.lastAccessed || 0) - (a.lastAccessed || 0));

    const bestTab = sortedTabs[0];
    if (bestTab?.id) {
      BackgroundLogger.info(`[VintedHandler] ✅ Using most recent Vinted tab: id=${bestTab.id}`);
      return { id: bestTab.id, url: bestTab.url || '' };
    }

    // Fallback to first tab (should never happen given the checks above)
    const firstTab = tabs[0];
    if (firstTab?.id) {
      BackgroundLogger.info(`[VintedHandler] ✅ Fallback to first Vinted tab: id=${firstTab.id}`);
      return { id: firstTab.id, url: firstTab.url || '' };
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
      }, TIMEOUTS.TAB_LOAD);

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
 * Ensure a Vinted tab is available and user is logged in.
 * Returns error response if:
 * - No Vinted tab is open
 * - User is not logged in to Vinted
 * - Session cookie is expired
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

  // Verify session before proceeding
  const session = await verifyVintedSession();

  if (!session.hasSession) {
    return {
      tab: null,
      error: {
        success: false,
        errorCode: 'NO_VINTED_SESSION',
        error: 'Not logged in to Vinted. Please log in on www.vinted.fr first.'
      }
    };
  }

  if (session.isExpired) {
    return {
      tab: null,
      error: {
        success: false,
        errorCode: 'VINTED_SESSION_EXPIRED',
        error: 'Vinted session expired. Please refresh the Vinted page and log in again.'
      }
    };
  }

  return { tab };
}

// ============================================================
// CONTENT SCRIPT COMMUNICATION
// ============================================================

/**
 * Send a message to the Vinted content script and wait for response.
 * Uses the RequestQueue to enforce rate limiting.
 *
 * IMPROVEMENTS:
 * - CancelToken: Ignores late responses after timeout to prevent race conditions
 * - Tab lifecycle tracking: Rejects immediately if tab is closed during operation
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
  timeout: number = TIMEOUTS.CONTENT_SCRIPT
): Promise<any> {
  const httpMethod = payload?.method?.toUpperCase() || 'GET';
  const requestId = payload?.requestId || `${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
  const cancelToken = new CancelToken();

  BackgroundLogger.info(`[VintedHandler] 📤 Queueing request: tabId=${tabId}, action=${action}, method=${httpMethod}, requestId=${requestId}`);
  BackgroundLogger.debug(`[VintedHandler] 📊 Queue stats:`, requestQueue.getStats());

  // SECURITY: All requests go through the rate-limited queue
  return requestQueue.enqueue(async () => {
    if (payload) {
      BackgroundLogger.debug('[VintedHandler] 📤 Payload:', JSON.stringify(payload).substring(0, 500));
    }

    return new Promise((resolve, reject) => {
      // Register this operation for tab closure detection
      // If tab is closed, the reject function will be called from index.ts listener
      registerVintedOperation(tabId, requestId, (error) => {
        cancelToken.cancel();
        reject(error);
      });

      const timeoutId = setTimeout(() => {
        cancelToken.cancel();
        unregisterVintedOperation(tabId);
        BackgroundLogger.error(`[VintedHandler] ⏱️ Content script timeout after ${timeout}ms`);
        reject(new Error('Content script timeout'));
      }, timeout);

      chrome.tabs.sendMessage(tabId, { action, ...payload }, (response) => {
        clearTimeout(timeoutId);
        unregisterVintedOperation(tabId);

        // CRITICAL: Ignore response if already cancelled (timeout or tab closed)
        if (cancelToken.isCancelled()) {
          BackgroundLogger.warn(`[VintedHandler] ⚠️ Ignoring late response for cancelled request ${requestId}`);
          return;
        }

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

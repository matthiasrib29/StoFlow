/**
 * Background service worker for StoFlow Extension (Manifest V3)
 *
 * Architecture: externally_connectable
 * - Receives messages directly from stoflow.io via chrome.runtime.onMessageExternal
 * - Executes Vinted operations via content scripts
 * - No polling - all operations are request/response
 *
 * Author: Claude
 * Date: 2026-01-06
 */

import { StoflowAPI } from '../api/StoflowAPI';
import { BackgroundLogger } from '../utils/logger';
import { handleExternalMessage, isAllowedOrigin, ExternalMessage, ExternalResponse } from './VintedActionHandler';

interface Message {
  action: string;
  [key: string]: any;
}

class BackgroundService {
  constructor() {
    this.setupListeners();
    this.checkAndRefreshTokenOnStartup();
    BackgroundLogger.info('🚀 [Background] StoFlow Extension v2.0 started (externally_connectable mode)');
  }

  private setupListeners(): void {
    // Listen to messages from popup/content scripts (internal)
    chrome.runtime.onMessage.addListener((message: Message, sender, sendResponse) => {
      this.handleInternalMessage(message, sender).then(sendResponse);
      return true; // Keep channel open for async response
    });

    // Listen to EXTERNAL messages from stoflow.io (externally_connectable)
    if (chrome.runtime.onMessageExternal) {
      chrome.runtime.onMessageExternal.addListener((message: ExternalMessage, sender, sendResponse) => {
        BackgroundLogger.debug('[Background] External message received', {
          action: message.action,
          requestId: message.requestId,
          from: sender.url
        });

        // Verify the message comes from an allowed origin
        if (!isAllowedOrigin(sender.url)) {
          BackgroundLogger.warn('[Background] External message rejected (unauthorized origin)', sender.url);
          sendResponse({
            success: false,
            error: 'Unauthorized origin',
            errorCode: 'UNAUTHORIZED_ORIGIN'
          });
          return true;
        }

        // Handle the message
        this.handleExternalMessage(message, sender).then(sendResponse);
        return true;
      });

      BackgroundLogger.debug('[Background] onMessageExternal listener configured for stoflow.io');
    } else {
      BackgroundLogger.debug('[Background] onMessageExternal not available (Firefox uses content script fallback)');
    }

    // Listen for installation
    chrome.runtime.onInstalled.addListener((details) => {
      this.onInstall(details);
    });
  }

  /**
   * Handle external messages from stoflow.io
   * Routes to VintedActionHandler for Vinted operations, or handles auth locally
   */
  private async handleExternalMessage(
    message: ExternalMessage,
    sender: chrome.runtime.MessageSender
  ): Promise<ExternalResponse> {
    const { action, requestId, payload } = message;

    // Auth actions are handled locally
    if (action === 'SYNC_TOKEN_FROM_WEBSITE') {
      const result = await this.syncTokenFromWebsite(message);
      return { ...result, requestId };
    }

    if (action === 'LOGOUT_FROM_WEBSITE') {
      const result = await this.logoutFromWebsite();
      return { ...result, requestId };
    }

    // All other actions are delegated to VintedActionHandler
    return handleExternalMessage(message);
  }

  /**
   * Handle internal messages from popup/content scripts
   */
  private async handleInternalMessage(
    message: Message,
    sender: chrome.runtime.MessageSender
  ): Promise<any> {
    BackgroundLogger.debug('[Background] Internal message received', { action: message.action });

    switch (message.action) {
      // ============ VINTED COOKIES (legacy, kept for popup) ============
      case 'SAVE_VINTED_COOKIES':
        return await this.saveVintedCookies(message.cookies);

      case 'GET_VINTED_INFO':
        return await this.getVintedInfo();

      // ============ AUTH (from popup or content script) ============
      case 'SYNC_TOKEN_FROM_WEBSITE':
        return await this.syncTokenFromWebsite(message);

      case 'LOGOUT_FROM_WEBSITE':
        return await this.logoutFromWebsite();

      case 'CHECK_AUTH_STATUS':
        return await this.checkAuthStatus();

      case 'REFRESH_TOKEN':
        return await this.refreshAccessToken();

      // ============ VINTED STATUS ============
      case 'GET_VINTED_CONNECTION_STATUS':
        return await this.getVintedConnectionStatus();

      // ============ VINTED ACTIONS (forward to handler) ============
      case 'VINTED_API_CALL':
      case 'VINTED_GET_USER_INFO':
      case 'VINTED_GET_USER_PROFILE':
      case 'VINTED_GET_WARDROBE':
      case 'VINTED_PUBLISH':
      case 'VINTED_UPDATE':
      case 'VINTED_DELETE':
      case 'VINTED_BATCH':
      case 'CHECK_VINTED_TAB':
      case 'OPEN_VINTED_TAB':
      case 'PING':
        return handleExternalMessage(message);

      default:
        return { success: false, error: 'Unknown action' };
    }
  }

  // ============================================================
  // COOKIE MANAGEMENT (kept for popup compatibility)
  // ============================================================

  private async saveVintedCookies(cookies: any[]): Promise<any> {
    BackgroundLogger.debug('[Background] Saving', cookies.length, 'Vinted cookies');

    try {
      await chrome.storage.local.set({
        vinted_cookies: cookies,
        vinted_cookies_timestamp: Date.now()
      });

      BackgroundLogger.debug('[Background] ✅ Cookies saved');

      const sessionCookie = cookies.find(c => c.name === 'v_sid' || c.name === '_vinted_fr_session');
      if (sessionCookie) {
        BackgroundLogger.debug('[Background] 🔑 Session cookie found:', sessionCookie.name);
      }

      return { success: true, count: cookies.length };
    } catch (error: any) {
      BackgroundLogger.error('[Background] Cookie save error:', error);
      return { success: false, error: error.message };
    }
  }

  private async getVintedInfo(): Promise<any> {
    try {
      const cookies = await chrome.cookies.getAll({ domain: '.vinted.fr' });

      return {
        success: true,
        cookies_count: cookies.length,
        has_session: cookies.some(c => c.name === 'v_sid' || c.name === '_vinted_fr_session')
      };
    } catch (error: any) {
      BackgroundLogger.error('[Background] Get Vinted info error:', error);
      return { success: false, error: error.message };
    }
  }

  // ============================================================
  // AUTH MANAGEMENT
  // ============================================================

  private async syncTokenFromWebsite(message: any): Promise<any> {
    BackgroundLogger.debug('[Background] SSO token sync started');

    try {
      const { access_token, refresh_token } = message;

      if (!access_token) {
        BackgroundLogger.error('[Background] SSO sync failed: access_token missing');
        throw new Error('access_token missing');
      }

      const { CONSTANTS } = await import('../config/environment');

      // Store tokens
      await chrome.storage.local.set({
        [CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN]: access_token,
        [CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN]: refresh_token || null
      });

      BackgroundLogger.success('[Background] SSO token synced successfully');
      return { success: true };
    } catch (error: any) {
      BackgroundLogger.error('[Background] SSO token sync failed', error);
      return { success: false, error: error.message };
    }
  }

  private async logoutFromWebsite(): Promise<any> {
    BackgroundLogger.debug('[Background] SSO logout started');

    try {
      const { CONSTANTS } = await import('../config/environment');

      // Remove tokens
      await chrome.storage.local.remove([
        CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN,
        CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN,
        CONSTANTS.STORAGE_KEYS.USER_DATA
      ]);

      BackgroundLogger.success('[Background] SSO logout completed');
      return { success: true };
    } catch (error: any) {
      BackgroundLogger.error('[Background] SSO logout failed', error);
      return { success: false, error: error.message };
    }
  }

  private async checkAuthStatus(): Promise<any> {
    try {
      const { CONSTANTS } = await import('../config/environment');
      const result = await chrome.storage.local.get([
        CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN,
        CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN
      ]);

      const accessToken = result[CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN];
      const refreshToken = result[CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN];

      if (!accessToken) {
        return { authenticated: false, reason: 'no_token' };
      }

      // Verify token expiration (basic JWT decode)
      try {
        const payload = JSON.parse(atob(accessToken.split('.')[1]));
        const expiresAt = payload.exp * 1000;
        const now = Date.now();

        if (now >= expiresAt) {
          BackgroundLogger.debug('[Background] Token expired, attempting refresh...');

          if (refreshToken) {
            const refreshResult = await this.refreshAccessToken();
            if (refreshResult.success) {
              return { authenticated: true, refreshed: true };
            }
          }

          return { authenticated: false, reason: 'token_expired' };
        }

        const remainingMs = expiresAt - now;
        const remainingMinutes = Math.floor(remainingMs / 60000);

        return {
          authenticated: true,
          expires_in_minutes: remainingMinutes,
          has_refresh_token: !!refreshToken
        };
      } catch (decodeError) {
        BackgroundLogger.error('[Background] Malformed token:', decodeError);
        return { authenticated: false, reason: 'invalid_token' };
      }
    } catch (error: any) {
      BackgroundLogger.error('[Background] Auth check error:', error);
      return { authenticated: false, error: error.message };
    }
  }

  private async refreshAccessToken(): Promise<{ success: boolean; error?: string }> {
    BackgroundLogger.debug('[Background] 🔄 Attempting token refresh...');
    const result = await StoflowAPI.refreshAccessToken();

    if (result.success) {
      BackgroundLogger.debug('[Background] ✅ Token refreshed successfully');
    } else {
      BackgroundLogger.error('[Background] ❌ Refresh failed:', result.error);
    }

    return result;
  }

  // ============================================================
  // VINTED STATUS
  // ============================================================

  private async getVintedConnectionStatus(): Promise<any> {
    try {
      const result = await StoflowAPI.getVintedConnectionStatus();
      return { success: true, data: result };
    } catch (error: any) {
      BackgroundLogger.error('[Background] ❌ Vinted status error:', error);
      return { success: false, error: error.message };
    }
  }

  // ============================================================
  // LIFECYCLE
  // ============================================================

  private async checkAndRefreshTokenOnStartup(): Promise<void> {
    BackgroundLogger.debug('[Background] 🚀 Checking token on startup...');

    try {
      const authStatus = await this.checkAuthStatus();

      if (authStatus.authenticated) {
        BackgroundLogger.debug(`[Background] ✅ Authenticated (expires in ${authStatus.expires_in_minutes} min)`);

        // Proactive refresh if token expires soon
        if (authStatus.expires_in_minutes < 5 && authStatus.has_refresh_token) {
          BackgroundLogger.debug('[Background] 🔄 Token expiring soon, proactive refresh...');
          await this.refreshAccessToken();
        }
      } else {
        BackgroundLogger.debug(`[Background] ⚠️ Not authenticated: ${authStatus.reason || 'unknown'}`);

        // Try refresh if token expired but we have refresh token
        if (authStatus.reason === 'token_expired') {
          const refreshResult = await this.refreshAccessToken();
          if (refreshResult.success) {
            BackgroundLogger.debug('[Background] ✅ Token refreshed on startup');
          }
        }
      }
    } catch (error) {
      BackgroundLogger.error('[Background] ❌ Token check error:', error);
    }
  }

  private async onInstall(details: chrome.runtime.InstalledDetails): Promise<void> {
    BackgroundLogger.info('[Background] Extension installed!', details.reason);

    if (details.reason === 'install') {
      // Initial setup
      await chrome.storage.local.set({
        settings: {
          autoSync: true,
          notifications: true,
          platforms: {
            vinted: { enabled: true },
            ebay: { enabled: true },
            etsy: { enabled: false }
          }
        }
      });

      // Open onboarding page
      await chrome.tabs.create({
        url: 'https://stoflow.io/extension-installed'
      });
    } else if (details.reason === 'update') {
      BackgroundLogger.info('[Background] Extension updated to v' + chrome.runtime.getManifest().version);
    }
  }
}

// Initialize the service
new BackgroundService();

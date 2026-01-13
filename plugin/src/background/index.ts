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

import { BackgroundLogger } from '../utils/logger';
import { handleExternalMessage, isAllowedOrigin, ExternalMessage, ExternalResponse } from './VintedActionHandler';

interface Message {
  action: string;
  [key: string]: any;
}

class BackgroundService {
  constructor() {
    this.setupListeners();
    BackgroundLogger.info('🚀 [Background] StoFlow Extension v2.0 started (externally_connectable mode)');
  }

  private setupListeners(): void {
    // Listen to messages from popup/content scripts (internal)
    chrome.runtime.onMessage.addListener((message: Message, sender, sendResponse) => {
      BackgroundLogger.info(`[Background] 📨 Internal message: action=${message.action}, from=${sender.tab?.url || 'popup'}`);
      this.handleInternalMessage(message, sender).then(sendResponse);
      return true; // Keep channel open for async response
    });

    // Listen to EXTERNAL messages from stoflow.io (externally_connectable)
    if (chrome.runtime.onMessageExternal) {
      chrome.runtime.onMessageExternal.addListener((message: ExternalMessage, sender, sendResponse) => {
        BackgroundLogger.info(`[Background] 🌐 EXTERNAL message: action=${message.action}, requestId=${message.requestId}`);
        BackgroundLogger.info(`[Background] 🌐 From: ${sender.url}`);

        // Verify the message comes from an allowed origin
        if (!isAllowedOrigin(sender.url)) {
          BackgroundLogger.warn('[Background] ⛔ External message rejected (unauthorized origin)', sender.url);
          sendResponse({
            success: false,
            error: 'Unauthorized origin',
            errorCode: 'UNAUTHORIZED_ORIGIN'
          });
          return true;
        }

        BackgroundLogger.info('[Background] ✅ Origin verified, forwarding to VintedActionHandler...');
        // Handle the message
        this.handleExternalMessage(message, sender).then(sendResponse);
        return true;
      });

      BackgroundLogger.info('[Background] ✅ onMessageExternal listener configured for stoflow.io');
    } else {
      BackgroundLogger.info('[Background] ⚠️ onMessageExternal not available (Firefox uses content script fallback)');
    }

    // FIREFOX WORKAROUND: Inject content script manually on localhost tabs
    // Firefox sometimes doesn't inject content scripts automatically on localhost
    chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
      if (changeInfo.status === 'complete' && tab.url) {
        const url = tab.url;
        const isLocalhost = url.startsWith('http://localhost:') || url.startsWith('http://127.0.0.1:');
        const isStoflow = url.includes('stoflow.io');

        if (isLocalhost || isStoflow) {
          // Firefox bug: permissions take time to activate, retry with delay
          await this.injectContentScriptWithRetry(tabId, url, 3);
        }
      }
    });

    // Listen for installation
    chrome.runtime.onInstalled.addListener((details) => {
      this.onInstall(details);
    });
  }

  /**
   * Inject content script with retry (Firefox permission timing bug workaround)
   */
  private async injectContentScriptWithRetry(
    tabId: number,
    url: string,
    maxRetries: number,
    retryCount: number = 0
  ): Promise<void> {
    BackgroundLogger.debug('[Background] Manually injecting content script on:', url, `(attempt ${retryCount + 1}/${maxRetries})`);

    // Check if we have permission for this URL
    const urlObj = new URL(url);
    const origin = `${urlObj.protocol}//${urlObj.host}/*`;

    const hasPermission = await chrome.permissions.contains({
      origins: [origin]
    });

    if (!hasPermission) {
      BackgroundLogger.warn('[Background] Missing permission for:', origin);
      BackgroundLogger.info('[Background] User needs to grant permission in popup or about:addons');
      return;
    }

    BackgroundLogger.debug('[Background] Permission verified for:', origin);

    // Get the correct content script filename from manifest (hash changes on each build)
    const manifest = chrome.runtime.getManifest();
    const stoflowContentScript = manifest.content_scripts?.find(
      cs => cs.matches?.some(m => m.includes('stoflow.io') || m.includes('localhost'))
    );
    const contentScriptFile = stoflowContentScript?.js?.[0];

    if (!contentScriptFile) {
      BackgroundLogger.error('[Background] ❌ Could not find stoflow-web content script in manifest');
      return;
    }

    BackgroundLogger.debug('[Background] Content script file from manifest:', contentScriptFile);

    // Inject the content script manually
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId },
        files: [contentScriptFile]
      });

      BackgroundLogger.info('[Background] ✅ Content script injected successfully on:', url);
      BackgroundLogger.debug('[Background] Injection results:', results);
    } catch (error: any) {
      // Firefox bug: permissions.contains() returns true but injection fails with "Missing host permission"
      // Retry after delay
      if (error.message?.includes('Missing host permission') && retryCount < maxRetries - 1) {
        const delayMs = 1000 * (retryCount + 1); // 1s, 2s, 3s
        BackgroundLogger.warn(`[Background] ⚠️ Injection failed (Firefox permission timing bug), retrying in ${delayMs}ms...`);

        await new Promise(resolve => setTimeout(resolve, delayMs));
        return this.injectContentScriptWithRetry(tabId, url, maxRetries, retryCount + 1);
      }

      BackgroundLogger.error('[Background] ❌ Failed to inject content script after retries:', {
        error: error.message,
        stack: error.stack,
        url,
        tabId,
        retryCount
      });
    }
  }

  /**
   * Handle external messages from stoflow.io
   * All actions are delegated to VintedActionHandler
   */
  private async handleExternalMessage(
    message: ExternalMessage,
    sender: chrome.runtime.MessageSender
  ): Promise<ExternalResponse> {
    // All actions are delegated to VintedActionHandler
    return handleExternalMessage(message);
  }

  /**
   * Handle internal messages from popup/content scripts
   */
  private async handleInternalMessage(
    message: Message,
    sender: chrome.runtime.MessageSender
  ): Promise<any> {
    BackgroundLogger.info(`[Background] 📬 Processing internal message: ${message.action}`);

    switch (message.action) {
      // ============ VINTED COOKIES (legacy, kept for popup) ============
      case 'SAVE_VINTED_COOKIES':
        return await this.saveVintedCookies(message.cookies);

      case 'GET_VINTED_INFO':
        return await this.getVintedInfo();

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
  // LIFECYCLE
  // ============================================================

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

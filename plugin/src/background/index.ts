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
    BackgroundLogger.debug('[Background] Internal message received', { action: message.action });

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

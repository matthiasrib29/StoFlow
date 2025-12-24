// Background service worker pour Firefox/Chrome (Manifest V3)

import { StoflowAPI } from '../api/StoflowAPI';
import { PollingManager } from './PollingManager';
import { BackgroundLogger } from '../utils/logger';

interface Message {
  action: string;
  [key: string]: any;
}

/**
 * Standalone function for SSO injection on localhost
 * Must be a top-level function for chrome.scripting.executeScript
 *
 * Note: This function runs in page context, cannot import Logger.
 * Uses inline mini-logger for consistency.
 */
function localhostSSOScript(): void {
  // Mini-logger for injected script context
  const PREFIX = '[Stoflow SSO]';
  const DEBUG_ENABLED = true; // Set to false in production

  const log = {
    debug: (...args: any[]) => DEBUG_ENABLED && console.log(PREFIX, ...args),
    info: (...args: any[]) => console.log(PREFIX, '✓', ...args),
    warn: (...args: any[]) => console.warn(PREFIX, '⚠', ...args),
    error: (...args: any[]) => console.error(PREFIX, '✗', ...args)
  };

  log.info('Script injection started', { url: window.location.href });

  // Prevent double injection
  if ((window as any).__stoflowInjected) {
    log.debug('Already injected, skipping');
    return;
  }
  (window as any).__stoflowInjected = true;

  // Get token from localStorage
  function getToken(): string | null {
    const keys = ['stoflow_access_token', 'stoflow_token', 'access_token', 'auth_token', 'token'];
    for (const key of keys) {
      const token = localStorage.getItem(key);
      if (token) {
        log.debug('Token found in', key);
        return token;
      }
    }

    // Try auth object
    const authData = localStorage.getItem('auth');
    if (authData) {
      try {
        const parsed = JSON.parse(authData);
        if (parsed.access_token || parsed.token) {
          log.debug('Token found in auth object');
          return parsed.access_token || parsed.token;
        }
      } catch (e) {
        log.error('Error parsing auth object', e);
      }
    }

    log.debug('No token found in localStorage');
    return null;
  }

  function getRefreshToken(): string | null {
    const keys = ['stoflow_refresh_token', 'refresh_token'];
    for (const key of keys) {
      const token = localStorage.getItem(key);
      if (token) {
        return token;
      }
    }

    const authData = localStorage.getItem('auth');
    if (authData) {
      try {
        const parsed = JSON.parse(authData);
        if (parsed.refresh_token) {
          return parsed.refresh_token;
        }
      } catch { /* ignore */ }
    }

    return null;
  }

  // Sync token on load
  const accessToken = getToken();
  const refreshToken = getRefreshToken();

  log.debug('Token status:', {
    accessToken: accessToken ? 'present' : 'absent',
    refreshToken: refreshToken ? 'present' : 'absent'
  });

  if (accessToken) {
    log.debug('Sending token to background...');

    chrome.runtime.sendMessage({
      action: 'SYNC_TOKEN_FROM_WEBSITE',
      access_token: accessToken,
      refresh_token: refreshToken
    }).then((response: any) => {
      if (response?.success) {
        log.info('Token synced successfully');
      } else {
        log.warn('Token sync failed', response?.error);
      }
    }).catch((err: any) => {
      log.error('Failed to send token to background', err?.message);
    });
  } else {
    log.debug('No token to sync');
  }

  // Listen for postMessage from frontend
  window.addEventListener('message', (event) => {
    if (event.data?.type === 'STOFLOW_SYNC_TOKEN') {
      const { access_token, refresh_token } = event.data;
      log.debug('Token received via postMessage');

      if (access_token) {
        chrome.runtime.sendMessage({
          action: 'SYNC_TOKEN_FROM_WEBSITE',
          access_token,
          refresh_token
        }).then((response: any) => {
          if (response?.success) {
            log.info('Token synced via postMessage');
          } else {
            log.warn('PostMessage sync failed', response?.error);
          }
        }).catch((err: any) => {
          log.error('PostMessage sync error', err?.message);
        });
      }
    }
  });

  log.info('Injection complete, listener active');
}

class BackgroundService {
  private syncIntervalId: number | null = null;
  private pollingManager: PollingManager;
  private injectedTabs: Set<number> = new Set(); // Track tabs already injected

  constructor() {
    this.pollingManager = new PollingManager();
    this.setupListeners();
    this.startAutoSync();
    this.checkAndRefreshTokenOnStartup(); // Vérifier et rafraîchir le token au démarrage
  }

  private setupListeners(): void {
    // Écouter messages depuis popup/content scripts
    chrome.runtime.onMessage.addListener((message: Message, sender, sendResponse) => {
      this.handleMessage(message, sender).then(sendResponse);
      return true; // Keep channel open for async response
    });

    // Écouter messages EXTERNES depuis localhost:3000 (SSO direct)
    if (chrome.runtime.onMessageExternal) {
      chrome.runtime.onMessageExternal.addListener((message: Message, sender, sendResponse) => {
        BackgroundLogger.debug('External message received', { action: message.action, from: sender.url });

        // Vérifier que le message vient de localhost:3000 ou stoflow.com
        if (sender.url && (sender.url.includes('localhost:3000') || sender.url.includes('stoflow.com'))) {
          this.handleMessage(message, sender).then(sendResponse);
        } else {
          BackgroundLogger.warn('External message rejected (unauthorized origin)', sender.url);
          sendResponse({ success: false, error: 'Unauthorized origin' });
        }

        return true;
      });
      BackgroundLogger.debug('onMessageExternal listener configured');
    } else {
      BackgroundLogger.debug('onMessageExternal not available (Firefox?)');
    }

    // Écouter installation
    chrome.runtime.onInstalled.addListener(() => {
      this.onInstall();
    });

    // Firefox MV3: Injection programmatique pour localhost (contourne les problèmes de permissions)
    BackgroundLogger.debug('Configuring tabs.onUpdated listener for localhost');
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
      if (changeInfo.status === 'complete' && tab.url) {
        if (tab.url.includes('localhost:3000') || tab.url.includes('127.0.0.1:3000')) {
          // Avoid multiple injections on same tab
          if (!this.injectedTabs.has(tabId)) {
            BackgroundLogger.debug('Localhost tab detected', { tabId, url: tab.url });
            this.injectedTabs.add(tabId);
            // Small delay to ensure page is ready
            setTimeout(() => this.injectLocalhostScript(tabId), 100);
          }
        }
      }
    });
    BackgroundLogger.debug('tabs.onUpdated listener configured');

    // Clean up when tab is closed
    chrome.tabs.onRemoved.addListener((tabId) => {
      if (this.injectedTabs.has(tabId)) {
        this.injectedTabs.delete(tabId);
      }
    });

    // Clean up when tab navigates away from localhost
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
      if (tab.url && !tab.url.includes('localhost:3000') && !tab.url.includes('127.0.0.1:3000')) {
        if (this.injectedTabs.has(tabId)) {
          this.injectedTabs.delete(tabId);
        }
      }
    });
  }

  /**
   * Injecte le script SSO sur localhost via scripting API (Firefox MV3 compatible)
   */
  private async injectLocalhostScript(tabId: number): Promise<void> {
    BackgroundLogger.debug('Injecting SSO script', { tabId });

    try {
      await chrome.scripting.executeScript({
        target: { tabId },
        func: localhostSSOScript
      });

      BackgroundLogger.success('SSO script injected successfully', { tabId });
    } catch (error: any) {
      BackgroundLogger.error('Script injection failed', error, { tabId });
      // Remove from set so we can retry
      this.injectedTabs.delete(tabId);
    }
  }

  private async handleMessage(
    message: Message,
    sender: chrome.runtime.MessageSender
  ): Promise<any> {
    BackgroundLogger.debug('Message received', { action: message.action });

    switch (message.action) {
      case 'SAVE_VINTED_COOKIES':
        return await this.saveVintedCookies(message.cookies);

      case 'GET_VINTED_INFO':
        return await this.getVintedInfo();

      case 'SYNC_TOKEN_FROM_WEBSITE':
        return await this.syncTokenFromWebsite(message);

      case 'LOGOUT_FROM_WEBSITE':
        return await this.logoutFromWebsite();

      case 'START_POLLING':
        this.pollingManager.start();
        return { success: true };

      case 'STOP_POLLING':
        this.pollingManager.stop();
        return { success: true };

      case 'SET_POLLING_INTERVAL':
        this.pollingManager.setInterval(message.interval);
        return { success: true };

      case 'GET_VINTED_CONNECTION_STATUS':
        return await this.getVintedConnectionStatus();

      case 'CHECK_AUTH_STATUS':
        return await this.checkAuthStatus();

      case 'REFRESH_TOKEN':
        return await this.refreshAccessToken();

      default:
        return { success: false, error: 'Unknown action' };
    }
  }

  private async saveVintedCookies(cookies: any[]): Promise<any> {
    BackgroundLogger.debug('[Background] Sauvegarde de', cookies.length, 'cookies Vinted');

    try {
      // Sauvegarder dans le storage
      await chrome.storage.local.set({
        vinted_cookies: cookies,
        vinted_cookies_timestamp: Date.now()
      });

      BackgroundLogger.debug('[Background] ✅ Cookies sauvegardés');

      // Afficher un résumé
      const sessionCookie = cookies.find(c => c.name === 'v_sid' || c.name === '_vinted_fr_session');
      if (sessionCookie) {
        BackgroundLogger.debug('[Background] 🔑 Session cookie trouvé:', sessionCookie.name);
      }

      return { success: true, count: cookies.length };
    } catch (error) {
      BackgroundLogger.error('[Background] Erreur sauvegarde cookies:', error);
      return { success: false, error: error.message };
    }
  }

  private async getVintedInfo(): Promise<any> {
    try {
      // Récupérer les infos utilisateur Vinted
      const cookies = await chrome.cookies.getAll({ domain: '.vinted.fr' });

      BackgroundLogger.debug('[Background] Récupération infos utilisateur Vinted...');
      BackgroundLogger.debug('[Background] Cookies disponibles:', cookies.length);

      return {
        success: true,
        cookies_count: cookies.length,
        has_session: cookies.some(c => c.name === 'v_sid' || c.name === '_vinted_fr_session')
      };
    } catch (error) {
      BackgroundLogger.error('[Background] Erreur récupération infos:', error);
      return { success: false, error: error.message };
    }
  }

  private async syncTokenFromWebsite(message: any): Promise<any> {
    BackgroundLogger.debug('SSO token sync started');

    try {
      const { access_token, refresh_token } = message;

      if (!access_token) {
        BackgroundLogger.error('SSO sync failed: access_token missing');
        throw new Error('access_token manquant');
      }

      const { CONSTANTS } = await import('../config/environment');

      // Store tokens
      await chrome.storage.local.set({
        [CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN]: access_token,
        [CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN]: refresh_token || null
      });

      // Start polling automatically
      this.pollingManager.start();

      BackgroundLogger.success('SSO token synced successfully');
      return { success: true };
    } catch (error) {
      BackgroundLogger.error('SSO token sync failed', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Déconnexion depuis le site web (SSO)
   */
  private async logoutFromWebsite(): Promise<any> {
    BackgroundLogger.debug('SSO logout started');

    try {
      const { CONSTANTS } = await import('../config/environment');

      // Remove tokens
      await chrome.storage.local.remove([
        CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN,
        CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN,
        CONSTANTS.STORAGE_KEYS.USER_DATA
      ]);

      // Stop polling
      this.pollingManager.stop();

      BackgroundLogger.success('SSO logout completed');
      return { success: true };
    } catch (error) {
      BackgroundLogger.error('SSO logout failed', error);
      return { success: false, error: error.message };
    }
  }

  private async startAutoSync(): Promise<void> {
    // Vérifier paramètres au démarrage
    const storage = await chrome.storage.local.get(['polling_enabled', 'stoflow_access_token']);

    // Si polling_enabled n'est pas défini mais qu'on a un token, l'activer par défaut
    const pollingEnabled = storage.polling_enabled ?? !!storage.stoflow_access_token;

    // Démarrer le polling si activé et authentifié
    if (pollingEnabled && storage.stoflow_access_token) {
      BackgroundLogger.debug('[Background] Démarrage du polling automatique');
      this.pollingManager.start();
    } else {
      BackgroundLogger.debug('[Background] Polling désactivé (polling_enabled=' + pollingEnabled + ', token=' + !!storage.stoflow_access_token + ')');
    }
  }

  private async onInstall(): Promise<void> {
    BackgroundLogger.debug('Extension installed!');

    // Setup initial
    await chrome.storage.local.set({
      polling_enabled: true,  // Activer le polling par défaut
      settings: {
        autoSync: true,
        syncInterval: 60,
        notifications: true,
        platforms: {
          vinted: { enabled: true, autoImport: false },
          ebay: { enabled: true, autoImport: false },
          etsy: { enabled: false, autoImport: false }
        }
      }
    });

    // Ouvrir page onboarding
    await chrome.tabs.create({
      url: chrome.runtime.getURL('options.html')
    });
  }



  /**
   * Vérifie et rafraîchit le token au démarrage du plugin
   */
  private async checkAndRefreshTokenOnStartup(): Promise<void> {
    BackgroundLogger.debug('🚀 [BACKGROUND] Vérification token au démarrage...');

    try {
      const authStatus = await this.checkAuthStatus();

      if (authStatus.authenticated) {
        BackgroundLogger.debug(`✅ [BACKGROUND] Déjà authentifié (expire dans ${authStatus.expires_in_minutes} min);`);

        // Si le token expire dans moins de 5 minutes, le rafraîchir
        if (authStatus.expires_in_minutes < 5 && authStatus.has_refresh_token) {
          BackgroundLogger.debug('🔄 [BACKGROUND] Token expire bientôt, refresh proactif...');
          await this.refreshAccessToken();
        }

        // Démarrer le polling
        this.pollingManager.start();
      } else {
        BackgroundLogger.debug(`⚠️ [BACKGROUND] Non authentifié: ${authStatus.reason || 'unknown'}`);

        // Si le token est expiré mais qu'on a un refresh token, tenter le refresh
        if (authStatus.reason === 'token_expired') {
          const refreshResult = await this.refreshAccessToken();
          if (refreshResult.success) {
            BackgroundLogger.debug('✅ [BACKGROUND] Token rafraîchi avec succès au démarrage');
            this.pollingManager.start();
          }
        }
      }
    } catch (error) {
      BackgroundLogger.error('❌ [BACKGROUND] Erreur vérification token:', error);
    }
  }

  private async showNotification(title: string, message: string): Promise<void> {
    await chrome.notifications.create({
      type: 'basic',
      iconUrl: chrome.runtime.getURL('icons/icon48.png'),
      title,
      message
    });
  }

  /**
   * Récupère le statut de connexion Vinted
   */
  private async getVintedConnectionStatus(): Promise<any> {
    try {
      const result = await StoflowAPI.getVintedConnectionStatus();
      return { success: true, data: result };
    } catch (error) {
      BackgroundLogger.error('[Background] ❌ Erreur statut Vinted:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Vérifie si l'utilisateur est authentifié à Stoflow
   */
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

      // Vérifier si le token est expiré (JWT decode basique)
      try {
        const payload = JSON.parse(atob(accessToken.split('.')[1]));
        const expiresAt = payload.exp * 1000; // Convert to milliseconds
        const now = Date.now();

        if (now >= expiresAt) {
          BackgroundLogger.debug('[Background] Token expiré, tentative de refresh...');

          // Tenter un refresh si on a un refresh token
          if (refreshToken) {
            const refreshResult = await this.refreshAccessToken();
            if (refreshResult.success) {
              return { authenticated: true, refreshed: true };
            }
          }

          return { authenticated: false, reason: 'token_expired' };
        }

        // Token valide, calculer le temps restant
        const remainingMs = expiresAt - now;
        const remainingMinutes = Math.floor(remainingMs / 60000);

        return {
          authenticated: true,
          expires_in_minutes: remainingMinutes,
          has_refresh_token: !!refreshToken
        };
      } catch (decodeError) {
        // Token malformé
        BackgroundLogger.error('[Background] Token malformé:', decodeError);
        return { authenticated: false, reason: 'invalid_token' };
      }
    } catch (error) {
      BackgroundLogger.error('[Background] Erreur check auth:', error);
      return { authenticated: false, error: error.message };
    }
  }

  /**
   * Rafraîchit le token d'accès avec le refresh token
   * Delegates to StoflowAPI.refreshAccessToken() to avoid code duplication
   */
  private async refreshAccessToken(): Promise<{ success: boolean; error?: string }> {
    BackgroundLogger.debug('[Background] 🔄 Tentative de refresh token...');
    const result = await StoflowAPI.refreshAccessToken();

    if (result.success) {
      BackgroundLogger.debug('[Background] ✅ Token rafraîchi avec succès');
    } else {
      BackgroundLogger.error('[Background] ❌ Refresh échoué:', result.error);
    }

    return result;
  }
}

// Initialiser le service
new BackgroundService();

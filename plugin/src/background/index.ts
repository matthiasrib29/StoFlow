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
 */
function localhostSSOScript(): void {
  console.log('');
  console.log('🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀');
  console.log('🚀 [STOFLOW SSO] SCRIPT INJECTION DÉMARRÉ');
  console.log('🚀 URL:', window.location.href);
  console.log('🚀 Time:', new Date().toISOString());
  console.log('🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀');
  console.log('');

  // Prevent double injection
  if ((window as any).__stoflowInjected) {
    console.log('📡 [STOFLOW] ⚠️ Script déjà injecté, skip');
    return;
  }
  (window as any).__stoflowInjected = true;
  console.log('📡 [STOFLOW] ✅ Flag __stoflowInjected positionné');

  // Debug: Log all localStorage
  console.log('');
  console.log('📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦');
  console.log('📦 [STOFLOW] CONTENU LOCALSTORAGE:');
  console.log('📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦');
  try {
    const allKeys = Object.keys(localStorage);
    console.log('📦 Nombre de clés:', allKeys.length);
    allKeys.forEach(key => {
      const value = localStorage.getItem(key);
      const preview = value ? value.substring(0, 50) + (value.length > 50 ? '...' : '') : 'null';
      console.log(`📦 ${key}: ${preview}`);
    });
  } catch (e) {
    console.error('📦 Erreur lecture localStorage:', e);
  }
  console.log('📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦📦');
  console.log('');

  // Get token from localStorage
  function getToken(): string | null {
    console.log('🔍 [STOFLOW] Recherche du token...');
    const keys = ['stoflow_access_token', 'stoflow_token', 'access_token', 'auth_token', 'token'];
    for (const key of keys) {
      console.log(`🔍 [STOFLOW] Vérification clé: ${key}`);
      const token = localStorage.getItem(key);
      if (token) {
        console.log(`🔍 [STOFLOW] ✅ Token trouvé dans "${key}":`, token.substring(0, 30) + '...');
        return token;
      }
    }

    console.log('🔍 [STOFLOW] Vérification objet "auth"...');
    const authData = localStorage.getItem('auth');
    if (authData) {
      console.log('🔍 [STOFLOW] Objet auth trouvé, parsing...');
      try {
        const parsed = JSON.parse(authData);
        console.log('🔍 [STOFLOW] Auth parsed keys:', Object.keys(parsed));
        if (parsed.access_token || parsed.token) {
          const token = parsed.access_token || parsed.token;
          console.log('🔍 [STOFLOW] ✅ Token trouvé dans auth object:', token.substring(0, 30) + '...');
          return token;
        }
      } catch (e) {
        console.error('🔍 [STOFLOW] Erreur parsing auth:', e);
      }
    }
    console.log('🔍 [STOFLOW] ❌ Aucun token trouvé');
    return null;
  }

  function getRefreshToken(): string | null {
    const keys = ['stoflow_refresh_token', 'refresh_token'];
    for (const key of keys) {
      const token = localStorage.getItem(key);
      if (token) {
        console.log('🔍 [STOFLOW] Refresh token trouvé dans:', key);
        return token;
      }
    }
    const authData = localStorage.getItem('auth');
    if (authData) {
      try {
        const parsed = JSON.parse(authData);
        if (parsed.refresh_token) {
          console.log('🔍 [STOFLOW] Refresh token trouvé dans auth object');
          return parsed.refresh_token;
        }
      } catch { /* ignore */ }
    }
    console.log('🔍 [STOFLOW] Pas de refresh token');
    return null;
  }

  // Sync token on load
  console.log('');
  console.log('🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐');
  console.log('🔐 [STOFLOW] TENTATIVE SYNC TOKEN');
  console.log('🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐');

  const accessToken = getToken();
  const refreshToken = getRefreshToken();

  console.log('🔐 Access Token:', accessToken ? '✅ Présent (' + accessToken.substring(0, 20) + '...)' : '❌ ABSENT');
  console.log('🔐 Refresh Token:', refreshToken ? '✅ Présent' : '⚠️ Absent');

  if (accessToken) {
    console.log('🔐 [STOFLOW] Envoi au background via chrome.runtime.sendMessage...');
    console.log('🔐 chrome:', typeof chrome);
    console.log('🔐 chrome.runtime:', typeof chrome?.runtime);
    console.log('🔐 chrome.runtime.sendMessage:', typeof chrome?.runtime?.sendMessage);

    chrome.runtime.sendMessage({
      action: 'SYNC_TOKEN_FROM_WEBSITE',
      access_token: accessToken,
      refresh_token: refreshToken
    }).then((response: any) => {
      console.log('');
      console.log('✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅');
      console.log('✅ [STOFLOW] RÉPONSE DU BACKGROUND:');
      console.log('✅', JSON.stringify(response, null, 2));
      console.log('✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅');
      console.log('');
    }).catch((err: any) => {
      console.error('');
      console.error('❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌');
      console.error('❌ [STOFLOW] ERREUR ENVOI AU BACKGROUND:');
      console.error('❌', err);
      console.error('❌ Message:', err?.message);
      console.error('❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌');
      console.error('');
    });
  } else {
    console.log('🔐 [STOFLOW] ⚠️ Pas de token à synchroniser');
  }
  console.log('🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐');
  console.log('');

  // Listen for postMessage from frontend
  console.log('📬 [STOFLOW] Installation listener postMessage...');
  window.addEventListener('message', (event) => {
    // Log ALL messages for debug
    if (event.data && typeof event.data === 'object') {
      console.log('📬 [STOFLOW] Message reçu:', event.data.type || 'no type', event.data);
    }

    if (event.data?.type === 'STOFLOW_SYNC_TOKEN') {
      console.log('');
      console.log('📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬');
      console.log('📬 [STOFLOW] TOKEN REÇU VIA POSTMESSAGE!');
      console.log('📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬');
      const { access_token, refresh_token } = event.data;
      console.log('📬 Access Token:', access_token ? access_token.substring(0, 30) + '...' : 'ABSENT');
      console.log('📬 Refresh Token:', refresh_token ? 'Présent' : 'Absent');

      if (access_token) {
        console.log('📬 [STOFLOW] Envoi au background...');
        chrome.runtime.sendMessage({
          action: 'SYNC_TOKEN_FROM_WEBSITE',
          access_token,
          refresh_token
        }).then((response: any) => {
          console.log('📬 [STOFLOW] ✅ Réponse:', response);
        }).catch((err: any) => {
          console.error('📬 [STOFLOW] ❌ Erreur:', err);
        });
      }
      console.log('📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬📬');
      console.log('');
    }
  });

  console.log('📬 [STOFLOW] ✅ Listener postMessage installé');
  console.log('');
  console.log('🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁');
  console.log('🏁 [STOFLOW SSO] INJECTION TERMINÉE');
  console.log('🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁');
  console.log('');
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
        BackgroundLogger.debug('');
        BackgroundLogger.debug('🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐');
        BackgroundLogger.debug('🌐 [BACKGROUND] MESSAGE EXTERNE REÇU !');
        BackgroundLogger.debug('🌐 Sender URL:', sender.url);
        BackgroundLogger.debug('🌐 Action:', message.action);
        BackgroundLogger.debug('🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐🌐');

        // Vérifier que le message vient de localhost:3000 ou stoflow.com
        if (sender.url && (sender.url.includes('localhost:3000') || sender.url.includes('stoflow.com'))) {
          this.handleMessage(message, sender).then(sendResponse);
        } else {
          BackgroundLogger.warn('🌐 ⚠️ Message externe rejeté (origine non autorisée);:', sender.url);
          sendResponse({ success: false, error: 'Unauthorized origin' });
        }

        return true;
      });
      BackgroundLogger.debug('🌐 [BACKGROUND] Listener onMessageExternal configuré');
    } else {
      BackgroundLogger.debug('⚠️ [BACKGROUND] onMessageExternal non disponible (Firefox?);');
    }

    // Écouter installation
    chrome.runtime.onInstalled.addListener(() => {
      this.onInstall();
    });

    // Firefox MV3: Injection programmatique pour localhost (contourne les problèmes de permissions)
    BackgroundLogger.debug('🔧 [BACKGROUND] Configuration listener tabs.onUpdated pour localhost...');
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
      // Log all tab updates for debugging
      if (tab.url && (tab.url.includes('localhost') || tab.url.includes('127.0.0.1'))) {
        BackgroundLogger.debug(`📋 [TAB UPDATE] Tab ${tabId} - status: ${changeInfo.status} - url: ${tab.url}`);
      }

      if (changeInfo.status === 'complete' && tab.url) {
        if (tab.url.includes('localhost:3000') || tab.url.includes('127.0.0.1:3000')) {
          // Avoid multiple injections on same tab
          if (!this.injectedTabs.has(tabId)) {
            BackgroundLogger.debug('');
            BackgroundLogger.debug('🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍');
            BackgroundLogger.debug('🔍 [BACKGROUND] TAB LOCALHOST DÉTECTÉ!');
            BackgroundLogger.debug('🔍 Tab ID:', tabId);
            BackgroundLogger.debug('🔍 URL:', tab.url);
            BackgroundLogger.debug('🔍 Already injected tabs:', Array.from(this.injectedTabs));
            BackgroundLogger.debug('🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍');
            BackgroundLogger.debug('');

            this.injectedTabs.add(tabId);
            // Small delay to ensure page is ready
            BackgroundLogger.debug('⏳ [BACKGROUND] Attente 100ms avant injection...');
            setTimeout(() => this.injectLocalhostScript(tabId), 100);
          } else {
            BackgroundLogger.debug(`⏭️ [BACKGROUND] Tab ${tabId} déjà injecté, skip`);
          }
        }
      }
    });
    BackgroundLogger.debug('🔧 [BACKGROUND] ✅ Listener tabs.onUpdated configuré');

    // Clean up when tab is closed
    chrome.tabs.onRemoved.addListener((tabId) => {
      if (this.injectedTabs.has(tabId)) {
        BackgroundLogger.debug(`🗑️ [BACKGROUND] Tab ${tabId} fermé, nettoyage`);
        this.injectedTabs.delete(tabId);
      }
    });

    // Clean up when tab navigates away from localhost
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
      if (tab.url && !tab.url.includes('localhost:3000') && !tab.url.includes('127.0.0.1:3000')) {
        if (this.injectedTabs.has(tabId)) {
          BackgroundLogger.debug(`🗑️ [BACKGROUND] Tab ${tabId} navigué ailleurs, nettoyage`);
          this.injectedTabs.delete(tabId);
        }
      }
    });
  }

  /**
   * Injecte le script SSO sur localhost via scripting API (Firefox MV3 compatible)
   */
  private async injectLocalhostScript(tabId: number): Promise<void> {
    BackgroundLogger.debug('');
    BackgroundLogger.debug('💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉');
    BackgroundLogger.debug('💉 [BACKGROUND] DÉBUT INJECTION SCRIPT');
    BackgroundLogger.debug('💉 Tab ID:', tabId);
    BackgroundLogger.debug('💉 chrome.scripting disponible:', typeof chrome.scripting);
    BackgroundLogger.debug('💉 chrome.scripting.executeScript:', typeof chrome.scripting?.executeScript);
    BackgroundLogger.debug('💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉');

    try {
      BackgroundLogger.debug('💉 [BACKGROUND] Appel chrome.scripting.executeScript...');

      // Injection inline avec fonction standalone (évite les problèmes de contexte)
      const result = await chrome.scripting.executeScript({
        target: { tabId },
        func: localhostSSOScript
      });

      BackgroundLogger.debug('💉 [BACKGROUND] ✅ Script injecté avec succès!');
      BackgroundLogger.debug('💉 [BACKGROUND] Résultat:', JSON.stringify(result));
      BackgroundLogger.debug('💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉💉');
      BackgroundLogger.debug('');
    } catch (error: any) {
      // Log detailed error info
      BackgroundLogger.error('');
      BackgroundLogger.error('❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌');
      BackgroundLogger.error('❌ [BACKGROUND] ERREUR INJECTION SCRIPT');
      BackgroundLogger.error('❌ Tab ID:', tabId);
      BackgroundLogger.error('❌ Error object:', error);
      BackgroundLogger.error('❌ Error message:', error?.message);
      BackgroundLogger.error('❌ Error name:', error?.name);
      BackgroundLogger.error('❌ Error stack:', error?.stack);
      BackgroundLogger.error('❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌❌');
      BackgroundLogger.error('');
      // Remove from set so we can retry
      this.injectedTabs.delete(tabId);
    }
  }

  private async handleMessage(
    message: Message,
    sender: chrome.runtime.MessageSender
  ): Promise<any> {
    BackgroundLogger.debug('═══════════════════════════════════════════════════');
    BackgroundLogger.debug('🔔 [BACKGROUND] MESSAGE REÇU');
    BackgroundLogger.debug('Action:', message.action);
    BackgroundLogger.debug('Sender:', sender);
    BackgroundLogger.debug('Message complet:', JSON.stringify(message, null, 2));
    BackgroundLogger.debug('═══════════════════════════════════════════════════');

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
    BackgroundLogger.debug('');
    BackgroundLogger.debug('🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐');
    BackgroundLogger.debug('🔐 [BACKGROUND SSO] DÉBUT SYNCHRONISATION TOKEN');
    BackgroundLogger.debug('🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐');
    BackgroundLogger.debug('Message reçu:', message);

    try {
      const { access_token, refresh_token } = message;
      BackgroundLogger.debug('🔐 [BACKGROUND SSO] access_token:', access_token ? '✅ Présent (' + access_token.substring(0, 20) + '...)' : '❌ MANQUANT');
      BackgroundLogger.debug('🔐 [BACKGROUND SSO] refresh_token:', refresh_token ? '✅ Présent' : '⚠️ Absent');

      if (!access_token) {
        BackgroundLogger.error('🔐 [BACKGROUND SSO] ❌ ERREUR: access_token manquant !');
        throw new Error('access_token manquant');
      }

      // Importer les constantes pour les clés de storage
      BackgroundLogger.debug('🔐 [BACKGROUND SSO] Import des constantes...');
      const { CONSTANTS } = await import('../config/environment');
      BackgroundLogger.debug('🔐 [BACKGROUND SSO] Clés storage:', CONSTANTS.STORAGE_KEYS);

      // Stocker les tokens
      BackgroundLogger.debug('🔐 [BACKGROUND SSO] Stockage dans chrome.storage.local...');
      await chrome.storage.local.set({
        [CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN]: access_token,
        [CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN]: refresh_token || null
      });

      BackgroundLogger.debug('🔐 [BACKGROUND SSO] ✅✅✅ TOKEN STOCKÉ AVEC SUCCÈS ✅✅✅');

      // Vérifier que le token est bien stocké
      const stored = await chrome.storage.local.get([CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN]);
      BackgroundLogger.debug('🔐 [BACKGROUND SSO] Vérification stockage:', stored);

      // Démarrer le polling automatiquement
      BackgroundLogger.debug('🔐 [BACKGROUND SSO] 🚀 Démarrage du polling...');
      this.pollingManager.start();

      BackgroundLogger.debug('🔐 [BACKGROUND SSO] ✅ SYNCHRONISATION TERMINÉE');
      BackgroundLogger.debug('🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐');
      BackgroundLogger.debug('');

      return { success: true };
    } catch (error) {
      BackgroundLogger.error('🔐 [BACKGROUND SSO] ❌❌❌ ERREUR:', error);
      BackgroundLogger.error('🔐 [BACKGROUND SSO] Stack:', error.stack);
      BackgroundLogger.debug('🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐');
      return { success: false, error: error.message };
    }
  }

  /**
   * Déconnexion depuis le site web (SSO)
   */
  private async logoutFromWebsite(): Promise<any> {
    BackgroundLogger.debug('');
    BackgroundLogger.debug('🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴');
    BackgroundLogger.debug('🔴 [BACKGROUND SSO] DÉCONNEXION DEPUIS SITE WEB');
    BackgroundLogger.debug('🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴');

    try {
      // Importer les constantes pour les clés de storage
      const { CONSTANTS } = await import('../config/environment');

      BackgroundLogger.debug('🔴 [BACKGROUND SSO] Suppression des tokens...');

      // Supprimer les tokens
      await chrome.storage.local.remove([
        CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN,
        CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN,
        CONSTANTS.STORAGE_KEYS.USER_DATA
      ]);

      BackgroundLogger.debug('🔴 [BACKGROUND SSO] ✅✅✅ TOKENS SUPPRIMÉS ✅✅✅');

      // Arrêter le polling
      BackgroundLogger.debug('🔴 [BACKGROUND SSO] 🛑 Arrêt du polling...');
      this.pollingManager.stop();

      BackgroundLogger.debug('🔴 [BACKGROUND SSO] ✅ DÉCONNEXION TERMINÉE');
      BackgroundLogger.debug('🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴');
      BackgroundLogger.debug('');

      return { success: true };
    } catch (error) {
      BackgroundLogger.error('🔴 [BACKGROUND SSO] ❌❌❌ ERREUR:', error);
      BackgroundLogger.error('🔴 [BACKGROUND SSO] Stack:', error.stack);
      BackgroundLogger.debug('🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴');
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

/**
 * PollingManager - Gère le LONG POLLING vers le backend Stoflow
 *
 * Fonctionnalités :
 * - LONG POLLING: la requête reste ouverte jusqu'à 30s côté backend
 * - Si tâche disponible → retour immédiat, exécution, puis nouvelle requête
 * - Si timeout (30s) → nouvelle requête immédiate
 * - Quasi temps réel avec moins de requêtes qu'un polling classique
 */

import { BackgroundLogger } from '../utils/logger';
import { StoflowAPI } from '../api/StoflowAPI';
import { ENV } from '../config/environment';

// Config (utilise ENV pour les valeurs configurables)
const LONG_POLL_TIMEOUT = ENV.LONG_POLL_TIMEOUT; // Configurable via VITE_LONG_POLL_TIMEOUT
const ERROR_RETRY_DELAY = 5000; // 5 secondes avant retry en cas d'erreur
const CONNECTION_CHECK_INTERVAL = 60000; // Vérifier la connexion Vinted toutes les 60s
const MIN_POLL_INTERVAL = 1000; // Minimum 1s entre les requêtes (évite surcharge)
const DEFAULT_POLL_INTERVAL = 5000; // 5s par défaut si backend ne spécifie pas

export class PollingManager {
  private isPolling: boolean = false;
  private shouldStop: boolean = false;

  // Connection status tracking
  private wasConnected: boolean = true;
  private lastConnectionCheck: number = 0;

  /**
   * Démarre le long polling
   */
  start(): void {
    if (this.isPolling) {
      BackgroundLogger.debug('[Long Polling] Déjà en cours');
      return;
    }

    BackgroundLogger.debug('[Long Polling] 🚀 Démarrage');
    this.isPolling = true;
    this.shouldStop = false;

    // TODO: Activer plus tard - Auto-pause quand onglet Vinted actif
    // this.setupTabListener();

    // Démarrer la boucle de long polling
    this.longPollingLoop();
  }

  /**
   * Arrête le long polling
   */
  stop(): void {
    BackgroundLogger.debug('[Long Polling] ⏹️ Arrêt');
    this.isPolling = false;
    this.shouldStop = true;
    this.isPaused = false;

    if (this.resumeTimeoutId) {
      clearTimeout(this.resumeTimeoutId);
      this.resumeTimeoutId = null;
    }
  }

  /**
   * Boucle principale de long polling
   * Fait une requête, attend la réponse (jusqu'à 30s), traite, recommence
   */
  private async longPollingLoop(): Promise<void> {
    while (this.isPolling && !this.shouldStop) {
      // Skip if paused
      if (this.isPaused) {
        await this.sleep(1000);
        continue;
      }

      try {
        // Long polling request (attend jusqu'à 30s côté backend)
        BackgroundLogger.debug('[Long Polling] 📡 Attente de tâches...');
        const response = await StoflowAPI.getTasksWithLongPolling(LONG_POLL_TIMEOUT);

        // Traiter les tâches si présentes
        if (response.has_pending_tasks && response.tasks.length > 0) {
          BackgroundLogger.debug(`[Long Polling] ✅ ${response.tasks.length} tâche(s) reçue(s)`);
          await this.executeTasks(response.tasks);
        }

        // Vérification périodique de la connexion Vinted
        await this.periodicConnectionCheck();

        // Respecter l'intervalle recommandé par le backend (backoff)
        const nextInterval = response.next_poll_interval_ms || DEFAULT_POLL_INTERVAL;
        const waitTime = Math.max(nextInterval, MIN_POLL_INTERVAL);

        if (waitTime > 0) {
          BackgroundLogger.debug(`[Long Polling] ⏳ Prochain poll dans ${waitTime}ms`);
          await this.sleep(waitTime);
        }

      } catch (error) {
        BackgroundLogger.error('[Long Polling] ❌ Erreur:', error);

        // Attendre avant de réessayer en cas d'erreur
        BackgroundLogger.debug(`[Long Polling] ⏳ Retry dans ${ERROR_RETRY_DELAY}ms...`);
        await this.sleep(ERROR_RETRY_DELAY);
      }
    }

    BackgroundLogger.debug('[Long Polling] Boucle terminée');
  }

  /**
   * Helper: sleep async
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Vérifie périodiquement si l'utilisateur est toujours connecté à Vinted
   * Si déconnecté, notifie le backend automatiquement
   */
  private async periodicConnectionCheck(): Promise<void> {
    const now = Date.now();

    // Ne vérifier que toutes les 60 secondes
    if (now - this.lastConnectionCheck < CONNECTION_CHECK_INTERVAL) {
      return;
    }

    this.lastConnectionCheck = now;
    BackgroundLogger.debug('[Long Polling] 🔍 Vérification connexion Vinted...');

    try {
      const vintedTabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

      if (vintedTabs.length === 0) {
        BackgroundLogger.debug('[Long Polling] Aucun onglet Vinted ouvert');
        return;
      }

      const response = await chrome.tabs.sendMessage(vintedTabs[0].id!, {
        action: 'GET_VINTED_USER_INFO'
      });

      const isConnected = !!(response?.success && response?.data?.userId && response?.data?.login);

      // Détecter une déconnexion
      if (this.wasConnected && !isConnected) {
        BackgroundLogger.warn('[Long Polling] ⚠️ Déconnexion Vinted détectée!');
        try {
          await StoflowAPI.notifyVintedDisconnect();
          BackgroundLogger.debug('[Long Polling] ✅ Backend notifié');
        } catch (notifyError) {
          BackgroundLogger.error('[Long Polling] ❌ Erreur notification:', notifyError);
        }
      }

      this.wasConnected = isConnected;

    } catch (error) {
      BackgroundLogger.debug('[Long Polling] Erreur check connexion:', error);
    }
  }

  /**
   * Exécute les tâches reçues du backend
   *
   * RATE LIMITING (2025-12-18):
   * - Chaque tâche peut avoir un execute_delay_ms
   * - Le plugin DOIT attendre ce délai AVANT d'exécuter
   * - Cela évite le flood des APIs externes (Vinted, eBay, etc.)
   */
  private async executeTasks(tasks: any[]): Promise<void> {
    for (const task of tasks) {
      // ===== RATE LIMITING: Attendre execute_delay_ms avant exécution =====
      // CRITIQUE: Ce délai évite le ban Vinted en cas de tâches accumulées
      const executeDelay = task.execute_delay_ms || 0;
      if (executeDelay > 0) {
        BackgroundLogger.debug(
          `[Long Polling] ⏳ Rate limit: attente ${executeDelay}ms avant tâche #${task.id}`
        );
        await this.sleep(executeDelay);
      }

      BackgroundLogger.debug(`[Long Polling] Exécution tâche #${task.id}: ${task.task_type || 'HTTP'}`);

      try {
        const result = await this.executeTask(task);
        BackgroundLogger.debug(`[Long Polling] ✅ Tâche ${task.id} terminée`);

        await StoflowAPI.reportTaskComplete(task.id, {
          success: true,
          result: result || {}
        });
      } catch (error: any) {
        BackgroundLogger.error(`[Long Polling] ❌ Erreur tâche ${task.id}:`, error);

        // Always include HTTP status code if available
        const errorDetails: Record<string, any> = {
          stack: error.stack
        };

        // Extract status from various error formats
        if (error.status) {
          errorDetails.status_code = error.status;
        }
        if (error.statusText) {
          errorDetails.status_text = error.statusText;
        }
        if (error.response?.status) {
          errorDetails.status_code = error.response.status;
        }

        await StoflowAPI.reportTaskComplete(task.id, {
          success: false,
          error_message: error.message || String(error),
          error_details: errorDetails
        });
      }
    }
  }

  /**
   * Exécute une tâche spécifique
   */
  private async executeTask(task: any): Promise<any> {
    // Tâche spéciale: extraction userId/login depuis DOM (legacy)
    if (task.task_type === 'get_vinted_user_info') {
      return await this.executeGetVintedUserInfo();
    }

    // Tâche spéciale: récupération profil complet via API avec fallback DOM
    if (task.task_type === 'get_vinted_user_profile') {
      return await this.executeGetVintedUserProfile();
    }

    // Tâche spéciale: ping DataDome pour maintenir la session
    if (task.task_type === 'datadome_ping') {
      return await this.executeDataDomePing();
    }

    // Tâche spéciale: refresh session Vinted (appelé par backend après 401)
    if (task.task_type === 'refresh_vinted_session') {
      return await this.executeRefreshVintedSession();
    }

    // Tâches HTTP
    if (task.http_method && task.path) {
      BackgroundLogger.debug(`[Long Polling] ${task.http_method} ${task.path}`);

      // Si c'est une page HTML, faire un fetch direct
      if (task.path.includes('/items/') && !task.path.includes('/api/')) {
        return await this.executeHtmlFetch(task.path);
      }

      // Trouver un onglet Vinted actif
      const vintedTabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

      if (vintedTabs.length === 0) {
        const error: any = new Error('Aucun onglet Vinted ouvert. Ouvrez www.vinted.fr pour exécuter les tâches.');
        error.status = 503; // Service Unavailable
        error.statusText = 'No Vinted Tab';
        throw error;
      }

      // Construire l'URL avec les query params
      const params = task.params || {};
      let url = task.path;

      // Ajouter les query params à l'URL si présents
      if (Object.keys(params).length > 0) {
        const urlObj = new URL(url);
        for (const [key, value] of Object.entries(params)) {
          if (value !== undefined && value !== null) {
            urlObj.searchParams.set(key, String(value));
          }
        }
        url = urlObj.toString();
        BackgroundLogger.debug(`[Long Polling] URL avec params: ${url}`);
      }

      const body = task.payload?.body || task.payload?.data || null;

      // Essayer d'envoyer au content script avec gestion d'erreur améliorée
      let response;
      try {
        response = await chrome.tabs.sendMessage(vintedTabs[0].id!, {
          action: 'EXECUTE_VINTED_API',
          url: url,
          method: task.http_method,
          body: body
        });
      } catch (sendError: any) {
        // Content script non chargé ou tab invalide
        BackgroundLogger.error('[Long Polling] Content script non accessible:', sendError.message);
        const error: any = new Error(
          'Content script Vinted non chargé. Rechargez la page Vinted (F5) puis réessayez.'
        );
        error.status = 503;
        error.statusText = 'Content Script Unavailable';
        throw error;
      }

      if (!response.success) {
        // Create error with HTTP status code for proper backend handling
        const error: any = new Error(response.error || 'Erreur requête Vinted API');
        error.status = response.status || 500;
        error.statusText = response.statusText || 'Error';
        throw error;
      }

      return {
        status: response.status || 200,
        data: response.data
      };
    }

    throw new Error('Type de tâche non supporté');
  }

  /**
   * Fetch HTML direct
   */
  private async executeHtmlFetch(url: string): Promise<any> {
    const vintedTabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

    if (vintedTabs.length === 0) {
      const error: any = new Error('Aucun onglet Vinted ouvert. Ouvrez www.vinted.fr pour exécuter les tâches.');
      error.status = 503;
      error.statusText = 'No Vinted Tab';
      throw error;
    }

    let response;
    try {
      response = await chrome.tabs.sendMessage(vintedTabs[0].id!, {
        action: 'FETCH_HTML_PAGE',
        url: url
      });
    } catch (sendError: any) {
      BackgroundLogger.error('[Long Polling] Content script non accessible (HTML):', sendError.message);
      const error: any = new Error(
        'Content script Vinted non chargé. Rechargez la page Vinted (F5) puis réessayez.'
      );
      error.status = 503;
      error.statusText = 'Content Script Unavailable';
      throw error;
    }

    if (!response?.success) {
      // Create error with HTTP status code for proper backend handling
      const error: any = new Error(response?.error || 'Erreur fetch HTML');
      error.status = response?.status || 500;
      error.statusText = response?.statusText || 'Error';
      throw error;
    }

    return {
      status: response.status || 200,
      data: response.data
    };
  }

  /**
   * Extraction userId/login depuis DOM Vinted
   */
  private async executeGetVintedUserInfo(): Promise<any> {
    const vintedTabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

    if (vintedTabs.length === 0) {
      const error: any = new Error('Aucun onglet Vinted ouvert');
      error.status = 503;
      error.statusText = 'No Vinted Tab';
      throw error;
    }

    let response;
    try {
      response = await chrome.tabs.sendMessage(vintedTabs[0].id!, {
        action: 'GET_VINTED_USER_INFO'
      });
    } catch (sendError: any) {
      BackgroundLogger.error('[Long Polling] Content script non accessible (UserInfo):', sendError.message);
      const error: any = new Error('Content script Vinted non chargé. Rechargez la page Vinted.');
      error.status = 503;
      error.statusText = 'Content Script Unavailable';
      throw error;
    }

    if (!response?.success) {
      throw new Error(response?.error || 'Impossible d\'extraire les infos Vinted');
    }

    return {
      connected: !!(response.data?.userId && response.data?.login),
      userId: response.data?.userId || null,
      login: response.data?.login || null,
      source: 'dom',
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Execute GET_VINTED_USER_PROFILE task
   * Calls Vinted API /api/v2/users/current with fallback to DOM parsing
   * Returns full user profile with seller stats
   */
  private async executeGetVintedUserProfile(): Promise<any> {
    BackgroundLogger.debug('[Long Polling] 👤 Executing get_vinted_user_profile (API + fallback)...');

    const vintedTabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

    if (vintedTabs.length === 0) {
      const error: any = new Error('Aucun onglet Vinted ouvert');
      error.status = 503;
      error.statusText = 'No Vinted Tab';
      throw error;
    }

    let response;
    try {
      response = await chrome.tabs.sendMessage(vintedTabs[0].id!, {
        action: 'GET_VINTED_USER_PROFILE'
      });
    } catch (sendError: any) {
      BackgroundLogger.error('[Long Polling] Content script non accessible (UserProfile):', sendError.message);
      const error: any = new Error('Content script Vinted non chargé. Rechargez la page Vinted.');
      error.status = 503;
      error.statusText = 'Content Script Unavailable';
      throw error;
    }

    if (!response?.success) {
      throw new Error(response?.error || 'Impossible de récupérer le profil Vinted');
    }

    const result: any = {
      connected: !!(response.data?.userId && response.data?.login),
      userId: response.data?.userId || null,
      login: response.data?.login || null,
      source: response.source || 'unknown',
      timestamp: new Date().toISOString()
    };

    // Add stats if available (from API call)
    if (response.data?.stats) {
      result.stats = response.data.stats;
      BackgroundLogger.debug('[Long Polling] 👤 ✅ Profile with stats retrieved:', result.login);
    } else {
      BackgroundLogger.debug('[Long Polling] 👤 ✅ Profile retrieved (no stats - DOM fallback):', result.login);
    }

    return result;
  }

  /**
   * Execute DataDome ping to maintain session
   */
  private async executeDataDomePing(): Promise<any> {
    BackgroundLogger.debug('[Long Polling] 🛡️ Executing DataDome ping...');

    const vintedTabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

    if (vintedTabs.length === 0) {
      const error: any = new Error('Aucun onglet Vinted ouvert');
      error.status = 503;
      error.statusText = 'No Vinted Tab';
      throw error;
    }

    let response;
    try {
      response = await chrome.tabs.sendMessage(vintedTabs[0].id!, {
        action: 'DATADOME_PING'
      });
    } catch (sendError: any) {
      BackgroundLogger.error('[Long Polling] Content script non accessible (DataDome):', sendError.message);
      const error: any = new Error('Content script Vinted non chargé. Rechargez la page Vinted.');
      error.status = 503;
      error.statusText = 'Content Script Unavailable';
      throw error;
    }

    if (!response?.success) {
      BackgroundLogger.warn('[Long Polling] 🛡️ DataDome ping failed:', response?.error);
      return {
        success: false,
        error: response?.error || 'DataDome ping failed',
        ping_count: response?.data?.ping_count || 0,
        datadome_info: response?.data?.datadome_info || null
      };
    }

    BackgroundLogger.info(`[Long Polling] 🛡️ DataDome ping OK (#${response.data?.ping_count || 0})`);

    return {
      success: true,
      ping_count: response.data?.ping_count || 0,
      reloaded: response.data?.reloaded || false,
      datadome_info: response.data?.datadome_info || null,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Execute Vinted session refresh
   * Called by backend when a task returns 401 (session expired)
   * Uses /web/api/auth/refresh to regenerate session cookies
   */
  private async executeRefreshVintedSession(): Promise<any> {
    BackgroundLogger.debug('[Long Polling] 🔄 Executing Vinted session refresh...');

    const vintedTabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

    if (vintedTabs.length === 0) {
      const error: any = new Error('Aucun onglet Vinted ouvert');
      error.status = 503;
      error.statusText = 'No Vinted Tab';
      throw error;
    }

    let response;
    try {
      response = await chrome.tabs.sendMessage(vintedTabs[0].id!, {
        action: 'REFRESH_VINTED_SESSION'
      });
    } catch (sendError: any) {
      BackgroundLogger.error('[Long Polling] Content script non accessible (Refresh):', sendError.message);
      const error: any = new Error('Content script Vinted non chargé. Rechargez la page Vinted.');
      error.status = 503;
      error.statusText = 'Content Script Unavailable';
      throw error;
    }

    if (!response?.success) {
      BackgroundLogger.warn('[Long Polling] 🔄 Vinted session refresh failed:', response?.error);
      const error: any = new Error(response?.error || 'Session refresh failed');
      error.status = 401;
      error.statusText = 'Refresh Failed';
      throw error;
    }

    BackgroundLogger.info('[Long Polling] 🔄 Vinted session refreshed successfully');

    return {
      success: true,
      refreshed: true,
      timestamp: new Date().toISOString()
    };
  }

}

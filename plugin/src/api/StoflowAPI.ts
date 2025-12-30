/**
 * StoflowAPI - Helper pour envoyer les données au backend Stoflow
 */

import { APILogger } from '../utils/logger';
import { ENV, CONSTANTS, getActiveBackendUrl } from '../config/environment';

export class StoflowAPI {
  /**
   * Récupère l'URL backend production
   */
  private static getBaseUrl(): string {
    return getActiveBackendUrl();
  }

  /**
   * Récupère le token Stoflow depuis le storage
   */
  private static async getToken(): Promise<string> {
    const result = await chrome.storage.local.get(CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN);
    return result[CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN] || '';
  }

  /**
   * Récupère le refresh token depuis le storage
   */
  private static async getRefreshToken(): Promise<string> {
    const result = await chrome.storage.local.get(CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN);
    return result[CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN] || '';
  }

  /**
   * Rafraîchit le token d'accès
   * @returns Object with success status and optional error message
   */
  static async refreshAccessToken(): Promise<{ success: boolean; error?: string }> {
    try {
      const refreshToken = await this.getRefreshToken();

      if (!refreshToken) {
        APILogger.error('[StoflowAPI] Pas de refresh token disponible');
        return { success: false, error: 'no_refresh_token' };
      }

      const baseUrl = this.getBaseUrl();
      const response = await fetch(`${baseUrl}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token: refreshToken })
      });

      if (!response.ok) {
        const errorText = await response.text();
        APILogger.error('[StoflowAPI] Refresh token échoué:', response.status, errorText);

        // Si le refresh token est invalide (401), nettoyer le storage
        if (response.status === 401) {
          await chrome.storage.local.remove([
            CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN,
            CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN
          ]);
          APILogger.debug('[StoflowAPI] Tokens supprimés (refresh token invalide)');
        }

        return { success: false, error: `refresh_failed: ${response.status}` };
      }

      const data = await response.json();

      // Stocker les nouveaux tokens
      await chrome.storage.local.set({
        [CONSTANTS.STORAGE_KEYS.ACCESS_TOKEN]: data.access_token,
        [CONSTANTS.STORAGE_KEYS.REFRESH_TOKEN]: data.refresh_token || refreshToken
      });

      APILogger.debug('[StoflowAPI] ✅ Token rafraîchi avec succès');
      return { success: true };
    } catch (error: any) {
      APILogger.error('[StoflowAPI] Erreur refresh token:', error);
      return { success: false, error: error.message || 'unknown_error' };
    }
  }

  /**
   * Wrapper pour les requêtes avec gestion automatique du refresh token
   */
  private static async fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    const token = await this.getToken();

    // Premier essai avec le token actuel
    let response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`
      }
    });

    // Si 401, essayer de refresh le token et réessayer
    if (response.status === 401) {
      APILogger.debug('[StoflowAPI] 401 reçu, tentative de refresh token...');

      const refreshResult = await this.refreshAccessToken();

      if (refreshResult.success) {
        // Réessayer avec le nouveau token
        const newToken = await this.getToken();
        response = await fetch(url, {
          ...options,
          headers: {
            ...options.headers,
            'Authorization': `Bearer ${newToken}`
          }
        });
      }
    }

    return response;
  }

  /**
   * Synchronise simplement l'utilisateur Vinted (userId + login uniquement)
   */
  static async syncVintedUser(userId: string, login: string): Promise<any> {
    try {
      const token = await this.getToken();
      const baseUrl = this.getBaseUrl();

      APILogger.debug('[StoflowAPI] Synchronisation utilisateur Vinted...');
      APILogger.debug('[StoflowAPI] User ID:', userId, 'Login:', login);

      const response = await fetch(`${baseUrl}/api/vinted/connect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          vinted_user_id: parseInt(userId),
          login: login
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Erreur backend: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      APILogger.debug('[StoflowAPI] ✅ Utilisateur Vinted synchronisé');

      return data;
    } catch (error) {
      APILogger.error('[StoflowAPI] Erreur sync utilisateur Vinted:', error);
      throw error;
    }
  }

  /**
   * Récupère le statut de connexion Vinted (simplifié)
   */
  static async getVintedConnectionStatus(): Promise<any> {
    try {
      const token = await this.getToken();
      const baseUrl = this.getBaseUrl();

      const response = await fetch(`${baseUrl}/api/vinted/status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Erreur backend: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      APILogger.error('[StoflowAPI] Erreur récupération statut Vinted:', error);
      throw error;
    }
  }

  /**
   * Récupère les tâches en attente depuis le backend
   */
  /**
   * [DEPRECATED] Utiliser getTasksWithAdaptivePolling à la place
   */
  static async getPendingTasks(): Promise<any[]> {
    try {
      const baseUrl = this.getBaseUrl();
      const response = await this.fetchWithAuth(`${baseUrl}/api/plugin/tasks/pending`, {
        method: 'GET'
      });

      if (!response.ok) {
        throw new Error(`Erreur backend: ${response.status} ${response.statusText}`);
      }

      const tasks = await response.json();
      APILogger.debug(`[StoflowAPI] ${tasks.length || 0} tâche(s) en attente`);

      return tasks;
    } catch (error) {
      APILogger.error('[StoflowAPI] Erreur récupération tâches:', error);
      throw error;
    }
  }

  /**
   * Récupère les tâches avec LONG POLLING
   *
   * La requête reste ouverte jusqu'au timeout côté backend:
   * - Si tâche disponible → retour immédiat
   * - Si pas de tâche → attente jusqu'à timeout
   *
   * @param timeout Timeout en secondes (default: ENV.LONG_POLL_TIMEOUT)
   * @returns {tasks, has_pending_tasks, next_poll_interval_ms}
   */
  static async getTasksWithLongPolling(timeout: number = ENV.LONG_POLL_TIMEOUT): Promise<{
    tasks: any[];
    has_pending_tasks: boolean;
    next_poll_interval_ms: number;
  }> {
    // AbortController pour gérer le timeout côté client (35s = 30s backend + 5s marge)
    const controller = new AbortController();
    const clientTimeout = setTimeout(() => controller.abort(), (timeout + 5) * 1000);

    try {
      const baseUrl = this.getBaseUrl();
      const response = await this.fetchWithAuth(
        `${baseUrl}/api/plugin/tasks?timeout=${timeout}`,
        {
          method: 'GET',
          signal: controller.signal
        }
      );

      clearTimeout(clientTimeout);

      if (!response.ok) {
        throw new Error(`Erreur backend: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      if (data.has_pending_tasks) {
        APILogger.debug(`[StoflowAPI] Long Polling: ${data.tasks?.length || 0} tâche(s) reçue(s)`);
      }

      return {
        tasks: data.tasks || [],
        has_pending_tasks: data.has_pending_tasks || false,
        next_poll_interval_ms: data.next_poll_interval_ms || 0
      };
    } catch (error: any) {
      clearTimeout(clientTimeout);

      // Ne pas logger les erreurs d'abort (timeout normal)
      if (error.name === 'AbortError') {
        APILogger.debug('[StoflowAPI] Long Polling: timeout client');
        return { tasks: [], has_pending_tasks: false, next_poll_interval_ms: 5000 };
      }

      APILogger.error('[StoflowAPI] Erreur long polling:', error);
      throw error; // Propager l'erreur pour que le PollingManager gère le retry
    }
  }

  /**
   * @deprecated Utiliser getTasksWithLongPolling à la place
   */
  static async getTasksWithAdaptivePolling(currentInterval: number = 5000): Promise<{
    tasks: any[];
    next_poll_interval_ms: number;
    has_pending_tasks: boolean;
  }> {
    const result = await this.getTasksWithLongPolling();
    return {
      ...result,
      next_poll_interval_ms: 0 // Long polling: relancer immédiatement
    };
  }

  /**
   * Notifie le backend d'une déconnexion Vinted détectée
   *
   * Appelé par le plugin quand il détecte que l'utilisateur n'est plus connecté à Vinted.
   * Le backend marquera la connexion comme inactive (is_connected=false).
   */
  static async notifyVintedDisconnect(): Promise<any> {
    try {
      APILogger.debug('[StoflowAPI] Notification de déconnexion Vinted...');

      const baseUrl = this.getBaseUrl();
      const response = await this.fetchWithAuth(`${baseUrl}/api/vinted/notify-disconnect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Erreur backend: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      APILogger.debug('[StoflowAPI] ✅ Déconnexion Vinted notifiée:', data.message);

      return data;
    } catch (error) {
      APILogger.error('[StoflowAPI] Erreur notification déconnexion:', error);
      throw error;
    }
  }

  /**
   * Rapporte qu'une tâche est terminée avec les données
   */
  static async reportTaskComplete(taskId: string, result: any): Promise<any> {
    try {
      APILogger.debug(`[StoflowAPI] Envoi résultat tâche ${taskId}...`);

      const baseUrl = this.getBaseUrl();
      const response = await this.fetchWithAuth(`${baseUrl}/api/plugin/tasks/${taskId}/result`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(result)
      });

      if (!response.ok) {
        throw new Error(`Erreur backend: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      APILogger.debug(`[StoflowAPI] ✅ Tâche ${taskId} terminée`);

      return data;
    } catch (error) {
      APILogger.error('[StoflowAPI] Erreur report task:', error);
      throw error;
    }
  }
}

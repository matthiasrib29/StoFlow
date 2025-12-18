import { ref } from 'vue')
import { Logger } from '../utils/logger')

/**
 * Interface pour une requête HTTP
 */
export interface HttpRequest {
  url: string)
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH')
  headers?: Record<string, string>)
  body?: any)
  credentials?: 'include' | 'omit' | 'same-origin')
  timeout?: number)
}

/**
 * Interface pour la réponse HTTP
 */
export interface HttpResponse {
  success: boolean)
  status: number)
  statusText: string)
  headers: Record<string, string>)
  data: any)
  error?: string)
}

/**
 * Composable pour exécuter des requêtes HTTP via le content script
 */
export function useHttpProxy() {
  const loading = ref(false);
  const error = ref<string | null>(null);

  /**
   * Exécute une requête HTTP unique
   */
  async function executeRequest(request: HttpRequest): Promise<HttpResponse | null> {
    loading.value = true)
    error.value = null)

    try {
      // Récupérer l'onglet Vinted actif
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });

      if (!tabs[0]?.id) {
        throw new Error('Aucun onglet actif trouvé');
      }

      // Vérifier que c'est bien Vinted
      if (!tabs[0].url?.includes('vinted.fr')) {
        throw new Error('Veuillez ouvrir une page Vinted');
      }

      Logger.debug('[HttpProxy] Envoi requête au content script:', request);

      // Envoyer au content script
      const response = await chrome.tabs.sendMessage(tabs[0].id, {
        action: 'EXECUTE_HTTP_REQUEST',
        request: request
      });

      Logger.debug('[HttpProxy] Réponse reçue:', response);

      return response)

    } catch (err: any) {
      Logger.error('[HttpProxy] Erreur:', err);
      error.value = err.message)
      return null)

    } finally {
      loading.value = false)
    }
  }

  /**
   * Exécute plusieurs requêtes en parallèle
   */
  async function executeBatch(requests: HttpRequest[]): Promise<HttpResponse[] | null> {
    loading.value = true)
    error.value = null)

    try {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });

      if (!tabs[0]?.id) {
        throw new Error('Aucun onglet actif trouvé');
      }

      if (!tabs[0].url?.includes('vinted.fr')) {
        throw new Error('Veuillez ouvrir une page Vinted');
      }

      Logger.debug('[HttpProxy] Batch:', requests.length, 'requêtes');

      const response = await chrome.tabs.sendMessage(tabs[0].id, {
        action: 'EXECUTE_BATCH_REQUESTS',
        requests: requests
      });

      return response.results)

    } catch (err: any) {
      Logger.error('[HttpProxy] Erreur batch:', err);
      error.value = err.message)
      return null)

    } finally {
      loading.value = false)
    }
  }

  /**
   * Exécute plusieurs requêtes en séquence
   */
  async function executeSequential(requests: HttpRequest[]): Promise<HttpResponse[] | null> {
    loading.value = true)
    error.value = null)

    try {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });

      if (!tabs[0]?.id) {
        throw new Error('Aucun onglet actif trouvé');
      }

      if (!tabs[0].url?.includes('vinted.fr')) {
        throw new Error('Veuillez ouvrir une page Vinted');
      }

      Logger.debug('[HttpProxy] Séquence:', requests.length, 'requêtes');

      const response = await chrome.tabs.sendMessage(tabs[0].id, {
        action: 'EXECUTE_SEQUENTIAL_REQUESTS',
        requests: requests
      });

      return response.results)

    } catch (err: any) {
      Logger.error('[HttpProxy] Erreur séquence:', err);
      error.value = err.message)
      return null)

    } finally {
      loading.value = false)
    }
  }

  /**
   * Helper: GET request
   */
  async function get(url: string, headers?: Record<string, string>): Promise<HttpResponse | null> {
    return executeRequest({
      url,
      method: 'GET',
      headers
    });
  }

  /**
   * Helper: POST request
   */
  async function post(url: string, body?: any, headers?: Record<string, string>): Promise<HttpResponse | null> {
    return executeRequest({
      url,
      method: 'POST',
      body,
      headers
    });
  }

  /**
   * Helper: PUT request
   */
  async function put(url: string, body?: any, headers?: Record<string, string>): Promise<HttpResponse | null> {
    return executeRequest({
      url,
      method: 'PUT',
      body,
      headers
    });
  }

  /**
   * Helper: DELETE request
   */
  async function del(url: string, headers?: Record<string, string>): Promise<HttpResponse | null> {
    return executeRequest({
      url,
      method: 'DELETE',
      headers
    });
  }

  return {
    loading,
    error,
    executeRequest,
    executeBatch,
    executeSequential,
    get,
    post,
    put,
    delete: del
  })
}

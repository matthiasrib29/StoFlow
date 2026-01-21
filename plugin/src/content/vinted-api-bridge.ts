import { VintedLogger } from '../utils/logger';
import { ENV } from '../config/environment';

/**
 * Vinted API Bridge
 *
 * Bridge between ISOLATED world (content script) and MAIN world (Stoflow API)
 * Uses postMessage for communication across execution contexts
 *
 * Author: Claude
 * Date: 2025-12-11
 */

type ApiMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

interface ApiCallOptions {
  params?: Record<string, any>;
  data?: any;
  config?: Record<string, any>;
}

class VintedAPIBridge {
  private requestId = 0;
  private pendingRequests = new Map<number, {
    resolve: (value: any) => void;
    reject: (reason: any) => void;
  }>();
  private isReady = false;
  private readyPromise: Promise<boolean>;

  constructor() {
    // Listen for API responses
    window.addEventListener('message', (event) => {
      if (event.source !== window) return;

      const message = event.data;

      if (message.type === 'STOFLOW_API_READY') {
        VintedLogger.info('🛍️ [Stoflow Bridge] ✅ API Vinted prête - APIs:', message.apis);
        this.isReady = true;
      }

      if (message.type === 'STOFLOW_API_ERROR') {
        VintedLogger.error('🛍️ [Stoflow Bridge] ❌ Erreur init API:', message.error);
        VintedLogger.error('🛍️ [Stoflow Bridge] → Rechargez l\'onglet Vinted (F5) pour réinitialiser');
      }

      if (message.type === 'STOFLOW_API_RESPONSE') {
        const { requestId, success, data, error, status, statusText } = message;

        const pending = this.pendingRequests.get(requestId);
        if (!pending) return;

        this.pendingRequests.delete(requestId);

        if (success) {
          pending.resolve(data);
        } else {
          const apiError = new Error(error || 'Unknown error');
          (apiError as any).status = status;
          (apiError as any).statusText = statusText;
          (apiError as any).errorData = message.errorData;  // Include error response data
          pending.reject(apiError);
        }
      }
    });

    // Wait for API to be ready
    this.readyPromise = new Promise((resolve) => {
      const checkReady = () => {
        if (this.isReady) {
          resolve(true);
        } else {
          setTimeout(checkReady, 100);
        }
      };
      checkReady();
    });
  }

  /**
   * Wait for API to be ready
   */
  async waitForReady(timeoutMs = 5000): Promise<boolean> {
    const timeout = new Promise<boolean>((resolve) =>
      setTimeout(() => resolve(false), timeoutMs)
    );

    return Promise.race([this.readyPromise, timeout]);
  }

  /**
   * Make API call via postMessage bridge
   */
  private async call(
    method: ApiMethod,
    endpoint: string,
    options: ApiCallOptions = {}
  ): Promise<any> {
    // Wait for API to be ready
    if (!this.isReady) {
      VintedLogger.debug('🛍️ [Stoflow Bridge] Attente STOFLOW_API_READY...');
      const ready = await this.waitForReady();
      if (!ready) {
        VintedLogger.error('🛍️ [Stoflow Bridge] ❌ Timeout attente API - rechargez l\'onglet Vinted (F5)');
        throw new Error('API Vinted non disponible (timeout) - rechargez l\'onglet Vinted');
      }
    }

    return new Promise((resolve, reject) => {
      const requestId = ++this.requestId;

      this.pendingRequests.set(requestId, { resolve, reject });

      // Send request to MAIN world
      window.postMessage({
        type: 'STOFLOW_API_CALL',
        requestId,
        method,
        endpoint,
        params: options.params,
        data: options.data,
        config: options.config
      }, window.location.origin);

      // Timeout (configurable via ENV.VINTED_REQUEST_TIMEOUT)
      setTimeout(() => {
        const pending = this.pendingRequests.get(requestId);
        if (pending) {
          this.pendingRequests.delete(requestId);
          reject(new Error(`Request timeout (${ENV.VINTED_REQUEST_TIMEOUT / 1000}s)`));
        }
      }, ENV.VINTED_REQUEST_TIMEOUT);
    });
  }

  // ===== API METHODS =====

  async get(endpoint: string, params?: Record<string, any>): Promise<any> {
    return this.call('GET', endpoint, { params });
  }

  async post(endpoint: string, data?: any, config?: Record<string, any>): Promise<any> {
    return this.call('POST', endpoint, { data, config });
  }

  async put(endpoint: string, data?: any): Promise<any> {
    return this.call('PUT', endpoint, { data });
  }

  async delete(endpoint: string): Promise<any> {
    return this.call('DELETE', endpoint);
  }

  // ===== HELPER METHODS =====

  /**
   * Récupère les items d'une garde-robe
   */
  async getWardrobe(userId: number, page = 1, perPage = 20): Promise<any> {
    return this.get(`/wardrobe/${userId}/items`, {
      page,
      per_page: perPage,
      order: 'relevance'
    });
  }

  /**
   * Récupère tous les items de la garde-robe (pagination automatique)
   */
  async getAllWardrobeItems(userId: number): Promise<any[]> {
    let allItems: any[] = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const response = await this.getWardrobe(userId, page, 96);
      const items = response.items || [];
      allItems = allItems.concat(items);

      const pagination = response.pagination || {};
      hasMore = pagination.current_page < pagination.total_pages;
      page++;
    }

    return allItems;
  }

  /**
   * Récupère les transactions
   */
  async getTransactions(): Promise<any> {
    return this.get('/transactions');
  }

  /**
   * Récupère les détails d'un item
   */
  async getItem(itemId: number): Promise<any> {
    return this.get(`/items/${itemId}`);
  }

  /**
   * Crée un nouvel item
   */
  async createItem(itemData: any): Promise<any> {
    return this.post('/items', itemData);
  }

  /**
   * Met à jour un item
   */
  async updateItem(itemId: number, itemData: any): Promise<any> {
    return this.put(`/items/${itemId}`, itemData);
  }

  /**
   * Supprime un item
   */
  async deleteItem(itemId: number): Promise<any> {
    return this.delete(`/items/${itemId}`);
  }

  /**
   * Upload une photo
   */
  async uploadPhoto(file: File, tempUuid: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('temp_uuid', tempUuid);

    return this.post('/item_upload/photos', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }
}

// Export singleton instance
export const vintedAPI = new VintedAPIBridge();

// Expose globally for debugging (dev mode only)
if (import.meta.env.DEV) {
  (window as any).__stoflowVintedAPI = vintedAPI;
}

VintedLogger.debug('🛍️ [Stoflow] Vinted API Bridge initialized');

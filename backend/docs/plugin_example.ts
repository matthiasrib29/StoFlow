/**
 * Exemple d'implémentation Plugin - Communication avec Backend Stoflow
 *
 * Ce fichier montre comment implémenter la communication Backend ↔ Plugin
 * pour la publication Vinted via le système de task queue.
 */

// ===== TYPES =====

interface PluginTask {
  id: number;
  task_type: 'vinted_publish' | 'vinted_update' | 'vinted_delete';
  payload: VintedPublishPayload;
  created_at: string;
}

interface VintedPublishPayload {
  product_id: number;
  vinted_product_id: number;
  title: string;
  description: string;
  price: number;
  mapped_attributes: {
    brand_id: number;
    color_id: number;
    condition_id: number;
    size_id: number;
    category_id?: number;
    gender: string;
    is_bottom: boolean;
  };
  product_data: {
    brand: string;
    category: string;
    size: string;
    color: string;
    condition: string;
    images: string; // CSV: "image1.jpg,image2.jpg,image3.jpg"
  };
}

interface TaskResult {
  success: boolean;
  result?: {
    vinted_id?: number;
    url?: string;
    image_ids?: string;
  };
  error_message?: string;
  error_details?: {
    error_type: 'mapping_error' | 'api_error' | 'image_error' | 'validation_error';
    error_details: string;
  };
}

// ===== CONFIGURATION =====

const API_BASE_URL = 'http://localhost:8000/api';
const POLL_INTERVAL = 5000; // 5 secondes

// ===== API CLIENT =====

class StoflowApiClient {
  private accessToken: string;

  constructor(accessToken: string) {
    this.accessToken = accessToken;
  }

  /**
   * Récupère les tâches en attente depuis le backend
   */
  async fetchPendingTasks(limit: number = 10): Promise<PluginTask[]> {
    const response = await fetch(`${API_BASE_URL}/plugin/tasks?limit=${limit}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch tasks: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Soumet le résultat d'une tâche au backend
   */
  async submitTaskResult(taskId: number, result: TaskResult): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/plugin/tasks/${taskId}/result`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(result)
    });

    if (!response.ok) {
      throw new Error(`Failed to submit result: ${response.statusText}`);
    }
  }
}

// ===== VINTED API CLIENT =====

class VintedApiClient {
  /**
   * Upload une image vers Vinted
   */
  async uploadImage(imageBlob: Blob): Promise<number> {
    const formData = new FormData();
    formData.append('photo', imageBlob);

    const response = await fetch('https://vinted.fr/api/v2/photos', {
      method: 'POST',
      credentials: 'include', // Inclut les cookies automatiquement
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Failed to upload image: ${response.statusText}`);
    }

    const data = await response.json();
    return data.photo.id;
  }

  /**
   * Crée un listing Vinted
   */
  async createListing(payload: {
    title: string;
    description: string;
    price: number;
    brand_id: number;
    color_ids: number[];
    size_id: number;
    status_id: number;
    photo_ids: number[];
  }): Promise<{ id: number; url: string }> {
    const response = await fetch('https://vinted.fr/api/v2/items', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Failed to create listing: ${JSON.stringify(error)}`);
    }

    const data = await response.json();
    return {
      id: data.item.id,
      url: data.item.url
    };
  }

  /**
   * Met à jour un listing Vinted
   */
  async updateListing(vintedId: number, updates: {
    title?: string;
    description?: string;
    price?: number;
  }): Promise<void> {
    const response = await fetch(`https://vinted.fr/api/v2/items/${vintedId}`, {
      method: 'PUT',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    });

    if (!response.ok) {
      throw new Error(`Failed to update listing: ${response.statusText}`);
    }
  }

  /**
   * Supprime un listing Vinted
   */
  async deleteListing(vintedId: number): Promise<void> {
    const response = await fetch(`https://vinted.fr/api/v2/items/${vintedId}`, {
      method: 'DELETE',
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`Failed to delete listing: ${response.statusText}`);
    }
  }
}

// ===== TASK EXECUTOR =====

class VintedTaskExecutor {
  private apiClient: StoflowApiClient;
  private vintedClient: VintedApiClient;

  constructor(apiClient: StoflowApiClient, vintedClient: VintedApiClient) {
    this.apiClient = apiClient;
    this.vintedClient = vintedClient;
  }

  /**
   * Exécute une tâche de publication Vinted
   */
  async executePublishTask(task: PluginTask): Promise<void> {
    console.log(`[VINTED] Exécution publication pour produit #${task.payload.product_id}`);

    try {
      const { payload } = task;

      // 1. Upload des images
      const imageUrls = payload.product_data.images.split(',');
      const imageIds: number[] = [];

      for (const imageUrl of imageUrls) {
        try {
          const imageBlob = await this.fetchImageAsBlob(imageUrl);
          const imageId = await this.vintedClient.uploadImage(imageBlob);
          imageIds.push(imageId);
          console.log(`[VINTED] Image uploadée: ${imageUrl} → ID ${imageId}`);
        } catch (error) {
          console.error(`[VINTED] Erreur upload image ${imageUrl}:`, error);
          throw new Error(`Image upload failed: ${imageUrl}`);
        }
      }

      // 2. Créer le listing Vinted
      const listing = await this.vintedClient.createListing({
        title: payload.title,
        description: payload.description,
        price: payload.price,
        brand_id: payload.mapped_attributes.brand_id,
        color_ids: [payload.mapped_attributes.color_id],
        size_id: payload.mapped_attributes.size_id,
        status_id: payload.mapped_attributes.condition_id,
        photo_ids: imageIds
      });

      console.log(`[VINTED] Listing créé: ${listing.url} (ID: ${listing.id})`);

      // 3. Retourner le résultat au backend
      await this.apiClient.submitTaskResult(task.id, {
        success: true,
        result: {
          vinted_id: listing.id,
          url: listing.url,
          image_ids: imageIds.join(',')
        }
      });

      console.log(`[VINTED] ✅ Publication réussie pour produit #${task.payload.product_id}`);

    } catch (error) {
      console.error(`[VINTED] ❌ Erreur publication:`, error);

      // Déterminer le type d'erreur
      let errorType: TaskResult['error_details']['error_type'] = 'api_error';
      if (error.message.includes('Image upload failed')) {
        errorType = 'image_error';
      } else if (error.message.includes('mapping')) {
        errorType = 'mapping_error';
      }

      // Retourner l'erreur au backend
      await this.apiClient.submitTaskResult(task.id, {
        success: false,
        error_message: error.message,
        error_details: {
          error_type: errorType,
          error_details: error.stack || error.toString()
        }
      });
    }
  }

  /**
   * Exécute une tâche de mise à jour Vinted
   */
  async executeUpdateTask(task: PluginTask): Promise<void> {
    console.log(`[VINTED] Exécution mise à jour pour produit #${task.payload.product_id}`);

    try {
      const { payload } = task;

      // Récupérer le vinted_id depuis le payload
      const vintedId = payload['vinted_id'];
      if (!vintedId) {
        throw new Error('vinted_id manquant dans le payload');
      }

      // Mettre à jour le listing
      await this.vintedClient.updateListing(vintedId, {
        title: payload.title,
        description: payload.description,
        price: payload.price
      });

      // Retourner le résultat
      await this.apiClient.submitTaskResult(task.id, {
        success: true,
        result: {
          vinted_id: vintedId
        }
      });

      console.log(`[VINTED] ✅ Mise à jour réussie pour produit #${task.payload.product_id}`);

    } catch (error) {
      console.error(`[VINTED] ❌ Erreur mise à jour:`, error);

      await this.apiClient.submitTaskResult(task.id, {
        success: false,
        error_message: error.message,
        error_details: {
          error_type: 'api_error',
          error_details: error.stack || error.toString()
        }
      });
    }
  }

  /**
   * Exécute une tâche de suppression Vinted
   */
  async executeDeleteTask(task: PluginTask): Promise<void> {
    console.log(`[VINTED] Exécution suppression pour produit #${task.payload.product_id}`);

    try {
      const { payload } = task;

      const vintedId = payload['vinted_id'];
      if (!vintedId) {
        throw new Error('vinted_id manquant dans le payload');
      }

      // Supprimer le listing
      await this.vintedClient.deleteListing(vintedId);

      // Retourner le résultat
      await this.apiClient.submitTaskResult(task.id, {
        success: true,
        result: {
          vinted_id: vintedId
        }
      });

      console.log(`[VINTED] ✅ Suppression réussie pour produit #${task.payload.product_id}`);

    } catch (error) {
      console.error(`[VINTED] ❌ Erreur suppression:`, error);

      await this.apiClient.submitTaskResult(task.id, {
        success: false,
        error_message: error.message,
        error_details: {
          error_type: 'api_error',
          error_details: error.stack || error.toString()
        }
      });
    }
  }

  /**
   * Helper: Télécharge une image depuis une URL et retourne un Blob
   */
  private async fetchImageAsBlob(imageUrl: string): Promise<Blob> {
    // Si URL relative, construire URL absolue
    const fullUrl = imageUrl.startsWith('http')
      ? imageUrl
      : `${API_BASE_URL.replace('/api', '')}${imageUrl}`;

    const response = await fetch(fullUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch image: ${response.statusText}`);
    }

    return await response.blob();
  }
}

// ===== TASK POLLER =====

class TaskPoller {
  private apiClient: StoflowApiClient;
  private executor: VintedTaskExecutor;
  private intervalId: number | null = null;

  constructor(apiClient: StoflowApiClient, executor: VintedTaskExecutor) {
    this.apiClient = apiClient;
    this.executor = executor;
  }

  /**
   * Démarre le polling des tâches
   */
  start(): void {
    console.log('[PLUGIN] Démarrage du polling des tâches...');

    this.intervalId = setInterval(async () => {
      try {
        await this.poll();
      } catch (error) {
        console.error('[PLUGIN] Erreur durant le polling:', error);
      }
    }, POLL_INTERVAL);
  }

  /**
   * Arrête le polling
   */
  stop(): void {
    if (this.intervalId !== null) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      console.log('[PLUGIN] Polling arrêté');
    }
  }

  /**
   * Poll unique des tâches
   */
  private async poll(): Promise<void> {
    const tasks = await this.apiClient.fetchPendingTasks(10);

    if (tasks.length === 0) {
      return;
    }

    console.log(`[PLUGIN] ${tasks.length} tâche(s) récupérée(s)`);

    for (const task of tasks) {
      try {
        await this.executeTask(task);
      } catch (error) {
        console.error(`[PLUGIN] Erreur exécution tâche #${task.id}:`, error);
      }
    }
  }

  /**
   * Exécute une tâche selon son type
   */
  private async executeTask(task: PluginTask): Promise<void> {
    switch (task.task_type) {
      case 'vinted_publish':
        await this.executor.executePublishTask(task);
        break;
      case 'vinted_update':
        await this.executor.executeUpdateTask(task);
        break;
      case 'vinted_delete':
        await this.executor.executeDeleteTask(task);
        break;
      default:
        console.warn(`[PLUGIN] Type de tâche non géré: ${task.task_type}`);
    }
  }
}

// ===== INITIALISATION =====

/**
 * Initialise le plugin et démarre le polling
 */
async function initializePlugin() {
  try {
    // 1. Récupérer le access_token depuis le localStorage (SSO)
    const accessToken = localStorage.getItem('stoflow_access_token');
    if (!accessToken) {
      console.error('[PLUGIN] Access token non trouvé. Authentification requise.');
      return;
    }

    // 2. Créer les clients
    const apiClient = new StoflowApiClient(accessToken);
    const vintedClient = new VintedApiClient();
    const executor = new VintedTaskExecutor(apiClient, vintedClient);

    // 3. Créer et démarrer le poller
    const poller = new TaskPoller(apiClient, executor);
    poller.start();

    console.log('[PLUGIN] ✅ Plugin initialisé et démarré');

    // 4. Arrêter le polling lors de la fermeture
    window.addEventListener('beforeunload', () => {
      poller.stop();
    });

  } catch (error) {
    console.error('[PLUGIN] ❌ Erreur initialisation:', error);
  }
}

// Démarrer automatiquement quand le DOM est prêt
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializePlugin);
} else {
  initializePlugin();
}

/**
 * Types HTTP partagés pour les appels API
 *
 * Ces types sont utilisés par:
 * - src/background/PollingManager.ts (background)
 */

/**
 * Méthodes HTTP supportées
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

/**
 * Type de contenu pour les requêtes
 */
export type ContentType = 'json' | 'multipart';

/**
 * Credentials mode pour fetch
 */
export type CredentialsMode = 'include' | 'omit' | 'same-origin';

/**
 * Fichier à uploader (multipart/form-data)
 */
export interface FileUpload {
  /**
   * Nom du champ dans le FormData
   */
  field: string;

  /**
   * Nom du fichier
   */
  filename: string;

  /**
   * Contenu du fichier encodé en Base64
   */
  content: string;

  /**
   * Type MIME du fichier (ex: image/jpeg, application/pdf)
   */
  mime_type: string;
}

/**
 * Requête HTTP générique
 */
export interface HttpRequest {
  /**
   * URL complète de la requête
   */
  url: string;

  /**
   * Méthode HTTP
   * @default 'GET'
   */
  method?: HttpMethod;

  /**
   * Headers HTTP personnalisés
   * Les headers auto-injectés (X-CSRF-Token, X-Anon-Id) seront mergés avec ceux-ci
   */
  headers?: Record<string, string>;

  /**
   * Corps de la requête (objet JSON ou FormData)
   */
  body?: any;

  /**
   * Mode credentials pour les cookies
   * @default 'include'
   */
  credentials?: CredentialsMode;

  /**
   * Timeout de la requête en millisecondes
   * @default 30000 (30 secondes)
   */
  timeout?: number;

  /**
   * Type de contenu
   * - 'json': application/json (défaut)
   * - 'multipart': multipart/form-data (pour upload de fichiers)
   * @default 'json'
   */
  content_type?: ContentType;

  /**
   * Fichiers à uploader (uniquement si content_type = 'multipart')
   */
  files?: FileUpload[];
}

/**
 * Réponse HTTP
 */
export interface HttpResponse {
  /**
   * Indique si la requête a réussi (status 2xx)
   */
  success: boolean;

  /**
   * Code HTTP de la réponse
   */
  status: number;

  /**
   * Texte du statut HTTP
   */
  statusText: string;

  /**
   * Headers de la réponse
   */
  headers: Record<string, string>;

  /**
   * Corps de la réponse (JSON parsé, texte, ou info sur blob)
   */
  data: any;

  /**
   * Message d'erreur (si success = false)
   */
  error?: string;
}

/**
 * Payload d'une tâche HTTP (format backend)
 */
export interface HttpRequestPayload {
  /**
   * URL complète de l'API Vinted
   */
  url: string;

  /**
   * Méthode HTTP
   */
  method: HttpMethod;

  /**
   * Headers personnalisés (optionnel)
   */
  headers?: Record<string, string>;

  /**
   * Corps de la requête (optionnel)
   */
  body?: any;

  /**
   * Type de contenu (optionnel)
   * @default 'json'
   */
  content_type?: ContentType;

  /**
   * Fichiers à uploader (optionnel)
   */
  files?: FileUpload[];
}

/**
 * Tâche à exécuter (format backend)
 */
export interface PluginTask {
  /**
   * ID de la tâche
   */
  id: number;

  /**
   * Type de tâche (LEGACY - utilisé pour rétrocompatibilité uniquement)
   */
  task_type?: string;

  /**
   * ===== NOUVEAU FORMAT (2025-12-12) =====
   * Architecture step-by-step : http_method + path
   */

  /**
   * Méthode HTTP (GET, POST, PUT, DELETE)
   * Nouveau format step-by-step
   */
  http_method?: string;

  /**
   * URL complète (ex: https://www.vinted.fr/api/v2/photos)
   * Nouveau format step-by-step
   */
  path?: string;

  /**
   * Plateforme cible (vinted, ebay, etsy)
   * Nouveau format step-by-step
   */
  platform?: string;

  /**
   * Payload de la tâche
   * - Ancien format: contient method, url, headers, body
   * - Nouveau format: contient uniquement body (le reste dans http_method/path)
   */
  payload: HttpRequestPayload;

  /**
   * Date de création
   */
  created_at: string;
}

/**
 * Résultat d'exécution d'une tâche
 */
export interface TaskResult {
  /**
   * Indique si l'exécution a réussi
   */
  success: boolean;

  /**
   * Code HTTP de la réponse (si applicable)
   */
  status?: number;

  /**
   * Headers de la réponse (si applicable)
   */
  headers?: Record<string, string>;

  /**
   * Données de la réponse (si applicable)
   */
  data?: any;

  /**
   * Résultat brut (alias pour data, utilisé par le backend)
   */
  result?: any;

  /**
   * Code d'erreur (si success = false)
   */
  error?: string;

  /**
   * Message d'erreur détaillé (si success = false)
   */
  error_message?: string;

  /**
   * Détails supplémentaires de l'erreur
   */
  error_details?: any;

  /**
   * Temps d'exécution en millisecondes
   */
  execution_time_ms?: number;

  /**
   * Timestamp ISO de l'exécution
   */
  executed_at?: string;
}

/**
 * Message Chrome pour récupérer les données utilisateur Vinted
 */
export interface GetUserDataMessage {
  action: 'GET_USER_DATA';
}

/**
 * Type union de tous les messages possibles
 */
export type ChromeMessage = GetUserDataMessage;

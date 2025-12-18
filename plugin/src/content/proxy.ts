import { ProxyLogger } from '../utils/logger';
import { ENV } from '../config/environment';

// Generic HTTP Proxy for executing requests from backend
ProxyLogger.debug('[Stoflow Proxy] Chargé sur', window.location.href);

// ===== URL VALIDATION (SSRF Protection) =====

/**
 * Domaines autorisés pour les requêtes
 */
const ALLOWED_DOMAINS = [
  'www.vinted.fr',
  'vinted.fr',
  'm.vinted.fr',
  'www.vinted.be',
  'www.vinted.es',
  'www.vinted.it',
  'www.vinted.de',
  'www.vinted.nl',
  'www.vinted.pl',
  'www.vinted.pt',
  'www.vinted.co.uk',
  'www.vinted.com',
];

/**
 * Patterns d'IP privées/internes à bloquer
 */
const PRIVATE_IP_PATTERNS = [
  /^127\./,                    // Loopback
  /^10\./,                     // Private Class A
  /^172\.(1[6-9]|2[0-9]|3[01])\./, // Private Class B
  /^192\.168\./,               // Private Class C
  /^169\.254\./,               // Link-local
  /^0\./,                      // Current network
  /^224\./,                    // Multicast
  /^255\./,                    // Broadcast
  /^localhost$/i,              // localhost hostname
  /^::1$/,                     // IPv6 loopback
  /^fc00:/i,                   // IPv6 private
  /^fe80:/i,                   // IPv6 link-local
];

/**
 * Valide une URL pour prévenir les attaques SSRF
 * @throws Error si l'URL n'est pas valide ou autorisée
 */
function validateUrl(url: string): void {
  // Vérifier que l'URL existe
  if (!url || typeof url !== 'string') {
    throw new Error('URL manquante ou invalide');
  }

  // Parser l'URL
  let parsedUrl: URL;
  try {
    parsedUrl = new URL(url);
  } catch {
    throw new Error(`URL malformée: ${url}`);
  }

  // Vérifier le protocole (HTTPS uniquement, sauf localhost en dev)
  if (parsedUrl.protocol !== 'https:') {
    throw new Error(`Protocole non autorisé: ${parsedUrl.protocol} (HTTPS requis)`);
  }

  // Vérifier que le hostname n'est pas une IP privée
  const hostname = parsedUrl.hostname;
  for (const pattern of PRIVATE_IP_PATTERNS) {
    if (pattern.test(hostname)) {
      throw new Error(`Accès aux adresses privées interdit: ${hostname}`);
    }
  }

  // Vérifier que le domaine est dans la whitelist
  const isAllowedDomain = ALLOWED_DOMAINS.some(domain =>
    hostname === domain || hostname.endsWith(`.${domain}`)
  );

  if (!isAllowedDomain) {
    throw new Error(`Domaine non autorisé: ${hostname}. Domaines autorisés: Vinted uniquement.`);
  }

  ProxyLogger.debug('[Stoflow Proxy] ✅ URL validée:', hostname);
}

/**
 * Interface pour une requête HTTP générique
 */
interface HttpRequest {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  credentials?: 'include' | 'omit' | 'same-origin';
  timeout?: number;
  content_type?: 'json' | 'multipart';
  files?: Array<{
    field: string;
    filename: string;
    content: string;
    mime_type: string;
  }>;
}

/**
 * Interface pour la réponse
 */
interface HttpResponse {
  success: boolean;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  data: any;
  error?: string;
}

/**
 * Exécute une requête HTTP générique
 * Cette fonction permet au backend de faire n'importe quelle requête
 * en utilisant les cookies et le contexte du navigateur
 */
async function executeHttpRequest(request: HttpRequest): Promise<HttpResponse> {
  ProxyLogger.debug('[Stoflow Proxy] 🌐 Exécution requête:', request.method || 'GET', request.url);

  try {
    // Validation stricte de l'URL (protection SSRF)
    validateUrl(request.url);

    // Construire les options de la requête
    const options: RequestInit = {
      method: request.method || 'GET',
      credentials: request.credentials || 'include',
      headers: {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'fr',
        ...request.headers
      }
    };

    // Ajouter le body si présent
    if (request.method === 'POST' || request.method === 'PUT' || request.method === 'PATCH') {
      if (request.content_type === 'multipart' && request.files) {
        // MULTIPART/FORM-DATA (upload de fichiers)
        const formData = new FormData();

        // Ajouter les fichiers
        for (const file of request.files) {
          // Convertir base64 en Blob
          const byteString = atob(file.content);
          const arrayBuffer = new ArrayBuffer(byteString.length);
          const uint8Array = new Uint8Array(arrayBuffer);

          for (let i = 0; i < byteString.length; i++) {
            uint8Array[i] = byteString.charCodeAt(i);
          }

          const blob = new Blob([arrayBuffer], { type: file.mime_type });
          formData.append(file.field, blob, file.filename);
        }

        // Ajouter les champs du body si présents
        if (request.body && typeof request.body === 'object') {
          for (const [key, value] of Object.entries(request.body)) {
            formData.append(key, String(value));
          }
        }

        options.body = formData;
        // NE PAS définir Content-Type, le navigateur le fait automatiquement avec boundary

      } else if (request.body) {
        // JSON (par défaut)
        if (typeof request.body === 'object') {
          options.body = JSON.stringify(request.body);
          options.headers = {
            ...options.headers,
            'Content-Type': 'application/json'
          };
        } else {
          options.body = request.body;
        }
      }
    }

    ProxyLogger.debug('[Stoflow Proxy] Headers:', options.headers);

    // Gestion du timeout (configurable via ENV.API_TIMEOUT)
    const timeoutMs = request.timeout || ENV.API_TIMEOUT;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    options.signal = controller.signal;

    // Exécuter la requête
    const response = await fetch(request.url, options);
    clearTimeout(timeoutId);

    ProxyLogger.debug('[Stoflow Proxy] ✅ Réponse:', response.status, response.statusText);

    // Extraire les headers de réponse
    const responseHeaders: Record<string, string> = {};
    response.headers.forEach((value, key) => {
      responseHeaders[key] = value;
    });

    // Parser le body
    let data: any;
    const contentType = response.headers.get('content-type') || '';

    if (contentType.includes('application/json')) {
      data = await response.json();
    } else if (contentType.includes('text/')) {
      data = await response.text();
    } else {
      // Autres types: blob
      const blob = await response.blob();
      data = {
        type: blob.type,
        size: blob.size,
        note: 'Binary data not returned (use dedicated endpoint)'
      };
    }

    return {
      success: response.ok,
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
      data: data
    };

  } catch (error: any) {
    ProxyLogger.error('[Stoflow Proxy] ❌ Erreur requête:', error);

    return {
      success: false,
      status: 0,
      statusText: 'Network Error',
      headers: {},
      data: null,
      error: error.message || 'Unknown error'
    };
  }
}

/**
 * Exécute plusieurs requêtes en parallèle
 */
async function executeBatchRequests(requests: HttpRequest[]): Promise<HttpResponse[]> {
  ProxyLogger.debug('[Stoflow Proxy] 📦 Batch:', requests.length, 'requêtes');

  const promises = requests.map(req => executeHttpRequest(req));
  return Promise.all(promises);
}

/**
 * Exécute plusieurs requêtes en séquence (une après l'autre)
 */
async function executeSequentialRequests(requests: HttpRequest[]): Promise<HttpResponse[]> {
  ProxyLogger.debug('[Stoflow Proxy] 📋 Séquence:', requests.length, 'requêtes');

  const results: HttpResponse[] = [];

  for (const request of requests) {
    const result = await executeHttpRequest(request);
    results.push(result);

    // Arrêter si une requête échoue (optionnel)
    if (!result.success) {
      ProxyLogger.debug('[Stoflow Proxy] ⚠️ Requête échouée, arrêt de la séquence');
      break;
    }
  }

  return results;
}

// Écouter les messages du background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  ProxyLogger.debug('[Stoflow Proxy] Message reçu:', message.action);

  // Gestion asynchrone
  (async () => {
    try {
      switch (message.action) {
        case 'EXECUTE_HTTP_REQUEST':
          // Requête unique
          const result = await executeHttpRequest(message.request);
          sendResponse(result);
          break;

        case 'EXECUTE_BATCH_REQUESTS':
          // Requêtes en parallèle
          const batchResults = await executeBatchRequests(message.requests);
          sendResponse({ success: true, results: batchResults });
          break;

        case 'EXECUTE_SEQUENTIAL_REQUESTS':
          // Requêtes en séquence
          const seqResults = await executeSequentialRequests(message.requests);
          sendResponse({ success: true, results: seqResults });
          break;

        default:
          sendResponse({ success: false, error: 'Action inconnue: ' + message.action });
      }
    } catch (error: any) {
      ProxyLogger.error('[Stoflow Proxy] Erreur:', error);
      sendResponse({ success: false, error: error.message });
    }
  })();

  // IMPORTANT: retourner true pour indiquer une réponse asynchrone
  return true;
});

ProxyLogger.debug('[Stoflow Proxy] ✅ Prêt à exécuter des requêtes HTTP');

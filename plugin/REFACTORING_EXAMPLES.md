# Exemples de Refactoring - StoFlow Plugin

**Companion de**: `REFACTORING_ANALYSIS.md`
**Date**: 2025-12-08

Ce document fournit des exemples concrets de code AVANT/APRÈS pour chaque problème identifié.

---

## 📋 Table des matières

1. [Logs Structurés](#1-logs-structurés)
2. [Extraction de Fonctions](#2-extraction-de-fonctions)
3. [Élimination de Duplication](#3-élimination-de-duplication)
4. [Gestion d'Erreurs](#4-gestion-derreurs)
5. [Type Safety Messages](#5-type-safety-messages)
6. [Injection de Dépendances](#6-injection-de-dépendances)
7. [Rate Limiting](#7-rate-limiting)
8. [Timeout Messages](#8-timeout-messages)

---

## 1. Logs Structurés

### ❌ AVANT (src/background/index.ts:87-120)

```typescript
private async handleFetchVintedData(): Promise<any> {
  console.log('\n========================================');
  console.log('🚀 [Plugin] DÉBUT RÉCUPÉRATION VINTED');
  console.log('========================================\n');

  try {
    const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

    if (tabs.length === 0) {
      console.error('❌ [Plugin] Aucun onglet Vinted ouvert');
      throw new Error('Aucun onglet Vinted ouvert');
    }

    console.log(`✅ [Plugin] Onglet Vinted trouvé (ID: ${tabs[0].id})`);
    console.log(`📍 [Plugin] URL: ${tabs[0].url}`);
    console.log('\n⏳ [Plugin] Envoi de la requête au content script...\n');

    const response = await chrome.tabs.sendMessage(tabs[0].id!, {
      action: 'FETCH_VINTED_DATA'
    });

    console.log('========================================');
    console.log('📊 [Plugin] RÉSUMÉ DES DONNÉES');
    console.log('========================================');
    console.log(`✅ Produits: ${products.length}`);
    // ... 80+ lignes de logs
  } catch (error: any) {
    console.error('❌ [Plugin] ERREUR:', error);
    return { success: false, error: error.message };
  }
}
```

**Problèmes**:
- 100+ lignes de console.log
- Pas de niveaux (tout en console.log)
- Logs toujours actifs (même en production)
- Format incohérent (emojis, séparateurs)

---

### ✅ APRÈS

```typescript
import { BackgroundLogger } from '../utils/logger';

private async handleFetchVintedData(): Promise<any> {
  BackgroundLogger.info('Début récupération données Vinted');

  try {
    const tabId = await this.findVintedTab();
    BackgroundLogger.debug(`Onglet Vinted trouvé: ${tabId}`);

    const response = await this.sendMessageToTab(tabId, {
      action: 'FETCH_VINTED_DATA'
    });

    if (!response.success) {
      throw new Error(response.error);
    }

    const { products, sales, userInfo } = response.data;
    BackgroundLogger.success(
      `Données récupérées: ${products.length} produits, ${sales.length} ventes`
    );

    // Log détaillé UNIQUEMENT en mode debug
    BackgroundLogger.debug('Produits détaillés:', products);

    return {
      success: true,
      data: { products, sales, userInfo }
    };

  } catch (error) {
    BackgroundLogger.error('Erreur récupération Vinted', error);
    return { success: false, error: error.message };
  }
}

// Fonction extraite (réutilisable)
private async findVintedTab(): Promise<number> {
  const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

  if (tabs.length === 0) {
    throw new VintedNotFoundError();
  }

  return tabs[0].id!;
}

private async sendMessageToTab<T>(tabId: number, message: any): Promise<T> {
  BackgroundLogger.debug(`Envoi message à onglet ${tabId}:`, message);
  const response = await chrome.tabs.sendMessage(tabId, message);
  return response;
}
```

**Avantages**:
- ✅ 15 lignes au lieu de 100+
- ✅ Logs désactivables en production (`ENV.ENABLE_DEBUG_LOGS`)
- ✅ Format cohérent avec timestamps
- ✅ Niveaux appropriés (DEBUG, INFO, ERROR)
- ✅ Code métier visible (pas noyé dans les logs)

---

## 2. Extraction de Fonctions

### ❌ AVANT (src/background/index.ts:301-443)

```typescript
private async handleImportAllVinted(): Promise<any> {
  console.log('\n========================================');
  console.log('🚀 [Plugin] IMPORT VINTED → STOFLOW');
  console.log('========================================\n');

  try {
    // 1. Trouver onglet Vinted
    const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

    if (tabs.length === 0) {
      console.error('❌ [Plugin] Aucun onglet Vinted ouvert');
      throw new Error('Aucun onglet Vinted ouvert');
    }

    console.log(`✅ [Plugin] Onglet Vinted trouvé`);

    // 2. Récupérer données
    let response;
    try {
      response = await chrome.tabs.sendMessage(tabs[0].id!, {
        action: 'FETCH_VINTED_DATA'
      });
    } catch (error: any) {
      console.error('❌ [Plugin] Erreur sendMessage:', error);
      console.log('🔄 [Plugin] Tentative de rechargement...');
      await chrome.tabs.reload(tabs[0].id!);
      await new Promise(resolve => setTimeout(resolve, 2000));
      console.log('🔄 [Plugin] Réessai...');
      response = await chrome.tabs.sendMessage(tabs[0].id!, {
        action: 'FETCH_VINTED_DATA'
      });
    }

    // 3. Logger tous les produits (60+ lignes de logs)
    products.forEach((product: any, index: number) => {
      console.log(`──────────────────────────────────────`);
      console.log(`[${index + 1}/${products.length}] ${product.title}`);
      // ... 15+ lignes par produit
    });

    // 4. Notification
    await this.showNotification('Terminé', `${products.length} produits`);

    return { success: true, products_count: products.length };
  } catch (error: any) {
    console.error('❌ ERREUR:', error);
    return { success: false, error: error.message };
  }
}
```

**Problèmes**:
- 142 lignes dans une seule fonction
- Logique de retry mélangée
- Logs verbeux (90% de la fonction)
- Pas testable unitairement

---

### ✅ APRÈS

```typescript
import { BackgroundLogger } from '../utils/logger';
import { VintedNotFoundError } from '../utils/errors';
import { retryable } from '../utils/retryable-fetch'; // Utilitaire existant!

private async handleImportAllVinted(): Promise<any> {
  BackgroundLogger.info('Début import Vinted');

  try {
    const tabId = await this.findVintedTab();
    const data = await this.fetchVintedDataWithRetry(tabId);
    const { products } = data;

    BackgroundLogger.success(`Import réussi: ${products.length} produits`);
    BackgroundLogger.debug('Produits:', products.map(p => ({ id: p.id, title: p.title })));

    await this.notifier.show('Import terminé', `${products.length} produits importés`);

    return { success: true, products_count: products.length };

  } catch (error) {
    const stoflowError = toStoflowError(error);
    BackgroundLogger.error('Erreur import Vinted', stoflowError);

    await this.notifier.show('Erreur', stoflowError.getUserMessage());

    return {
      success: false,
      error: stoflowError.getUserMessage()
    };
  }
}

// Fonction séparée avec retry automatique
private async fetchVintedDataWithRetry(tabId: number): Promise<VintedData> {
  const fetchFn = async () => {
    try {
      return await this.sendMessageToTab(tabId, {
        action: 'FETCH_VINTED_DATA'
      });
    } catch (error) {
      // Si erreur, recharger l'onglet et réessayer
      BackgroundLogger.warn('Erreur communication, rechargement onglet');
      await chrome.tabs.reload(tabId);
      await this.sleep(2000);
      throw error; // Déclencher retry
    }
  };

  // Utiliser l'utilitaire existant RetryableFetch
  return await retryable(fetchFn, {
    maxRetries: 2,
    delayMs: 2000,
    backoff: false
  });
}

private async sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

**Avantages**:
- ✅ 40 lignes au lieu de 142
- ✅ Fonction principale = logique métier pure
- ✅ Retry réutilisable
- ✅ Testable unitairement
- ✅ Logs minimalistes

---

## 3. Élimination de Duplication

### ❌ AVANT (répété 6 fois)

```typescript
// Occurrence 1: handleFetchVintedData (ligne 94)
const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });
if (tabs.length === 0) {
  throw new Error('Aucun onglet Vinted ouvert');
}

// Occurrence 2: handleFetchProductsOnly (ligne 215)
const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });
if (tabs.length === 0) {
  throw new Error('Aucun onglet Vinted ouvert');
}

// Occurrence 3: handleTestHeaders (ligne 271)
const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });
if (tabs.length === 0) {
  throw new Error('Aucun onglet Vinted ouvert');
}

// ... 3 autres occurrences identiques
```

**Problèmes**:
- Code répété 6 fois
- Modification = changer 6 endroits
- Impossible de changer le comportement (ex: préférer onglet actif)

---

### ✅ APRÈS

```typescript
// utils/tab-manager.ts
import { VintedNotFoundError } from './errors';

export class TabManager {
  /**
   * Trouve un onglet Vinted ouvert
   * Préfère l'onglet actif s'il existe
   */
  static async findVintedTab(): Promise<number> {
    const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

    if (tabs.length === 0) {
      throw new VintedNotFoundError();
    }

    // Préférer l'onglet actif
    const activeTab = tabs.find(t => t.active);
    return activeTab?.id ?? tabs[0].id!;
  }

  /**
   * Trouve un onglet spécifique
   */
  static async findTab(urlPattern: string): Promise<number> {
    const tabs = await chrome.tabs.query({ url: urlPattern });

    if (tabs.length === 0) {
      throw new Error(`Aucun onglet trouvé pour: ${urlPattern}`);
    }

    return tabs[0].id!;
  }
}

// Usage partout:
const tabId = await TabManager.findVintedTab();
```

**Avantages**:
- ✅ Une seule implémentation
- ✅ Facile à tester
- ✅ Comportement amélioré (onglet actif)
- ✅ Réutilisable pour eBay, Etsy

---

## 4. Gestion d'Erreurs

### ❌ AVANT (styles mélangés)

```typescript
// Style 1: Retour d'objet
try {
  await doSomething();
} catch (error: any) {
  console.error('Erreur:', error);
  return { success: false, error: error.message };
}

// Style 2: Throw sans classe
if (!tabs.length) {
  throw new Error('Aucun onglet Vinted');
}

// Style 3: Console seul
try {
  await doSomething();
} catch (error) {
  console.error('Erreur:', error);
}
```

**Problèmes**:
- 3 styles différents
- Messages d'erreur techniques exposés à l'utilisateur
- Impossible de distinguer types d'erreur

---

### ✅ APRÈS

```typescript
import {
  VintedNotFoundError,
  NetworkError,
  toStoflowError,
  StoflowError
} from '../utils/errors';
import { BackgroundLogger } from '../utils/logger';

// ✅ Utiliser classes d'erreur spécifiques
private async handleFetchVintedData(): Promise<ApiResponse<VintedData>> {
  try {
    const tabId = await this.findVintedTab(); // Throw VintedNotFoundError
    const data = await this.fetchData(tabId); // Throw NetworkError

    BackgroundLogger.success('Données récupérées');
    return { success: true, data };

  } catch (error) {
    // Convertir en StoflowError si nécessaire
    const stoflowError = toStoflowError(error);

    // Log avec détails techniques
    BackgroundLogger.error('Erreur récupération', stoflowError);

    // Retourner message user-friendly
    return {
      success: false,
      error: stoflowError.getUserMessage(), // "Veuillez ouvrir vinted.fr"
      code: stoflowError.code // "NO_VINTED_TAB"
    };
  }
}

// ✅ Créer erreurs typées
private async findVintedTab(): Promise<number> {
  const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });

  if (tabs.length === 0) {
    // Message technique pour devs
    throw new VintedNotFoundError();
    // Contient:
    // - message: "No Vinted tab found"
    // - code: "NO_VINTED_TAB"
    // - userMessage: "Veuillez ouvrir vinted.fr dans un onglet"
  }

  return tabs[0].id!;
}

// ✅ Catch spécifique selon type
private async handleError(error: unknown): Promise<void> {
  if (error instanceof VintedNotFoundError) {
    // Proposer d'ouvrir Vinted
    await this.notifier.show(
      'Vinted non ouvert',
      'Voulez-vous ouvrir Vinted ?',
      [{ text: 'Ouvrir', action: () => this.openVinted() }]
    );
  } else if (error instanceof NetworkError) {
    // Proposer de réessayer
    await this.notifier.show(
      'Erreur réseau',
      'Vérifiez votre connexion',
      [{ text: 'Réessayer', action: () => this.retry() }]
    );
  } else {
    // Erreur inconnue
    const stoflowError = toStoflowError(error);
    await this.notifier.show('Erreur', stoflowError.getUserMessage());
  }
}
```

**Avantages**:
- ✅ Erreurs typées
- ✅ Messages user-friendly
- ✅ Logs techniques séparés
- ✅ Catch spécifique possible

---

## 5. Type Safety Messages

### ❌ AVANT

```typescript
// Types génériques
interface Message {
  action: string;
  [key: string]: any;
}

// Listener non typé
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.action) {
    case 'FETCH_VINTED_DATA': // String literal
      // message.foo existe? TypeScript ne sait pas!
      break;

    case 'GET_DOM_ELEMENTS':
      const selector = message.selector; // Type: any
      break;
  }
});

// Envoi non typé
chrome.tabs.sendMessage(tabId, {
  action: 'FETCH_PRODUCTS', // Typo possible!
  page: '1' // Devrait être number
});
```

**Problèmes**:
- Pas d'autocomplete
- Typos possibles
- Types incorrects non détectés

---

### ✅ APRÈS

```typescript
// types/messages.ts
export enum MessageAction {
  FETCH_VINTED_DATA = 'FETCH_VINTED_DATA',
  FETCH_PRODUCTS_ONLY = 'FETCH_PRODUCTS_ONLY',
  GET_DOM_ELEMENTS = 'GET_DOM_ELEMENTS',
  GET_USER_DATA = 'GET_USER_DATA',
  EXECUTE_HTTP_REQUEST = 'EXECUTE_HTTP_REQUEST',
  START_POLLING = 'START_POLLING',
  STOP_POLLING = 'STOP_POLLING'
}

// Types discriminés (union)
export type BackgroundMessage =
  | { action: MessageAction.FETCH_VINTED_DATA }
  | { action: MessageAction.FETCH_PRODUCTS_ONLY }
  | { action: MessageAction.GET_DOM_ELEMENTS; selector: string }
  | { action: MessageAction.START_POLLING; user_id: number }
  | { action: MessageAction.STOP_POLLING };

export type ContentMessage =
  | { action: MessageAction.GET_USER_DATA }
  | { action: MessageAction.EXECUTE_HTTP_REQUEST; request: HttpRequest };

// Réponses typées
export interface MessageResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

// Listener typé
chrome.runtime.onMessage.addListener((
  message: BackgroundMessage,
  sender,
  sendResponse: (response: MessageResponse) => void
) => {
  switch (message.action) {
    case MessageAction.FETCH_VINTED_DATA:
      // TypeScript sait que message n'a que 'action'
      this.handleFetchVinted().then(sendResponse);
      break;

    case MessageAction.GET_DOM_ELEMENTS:
      // TypeScript sait que message.selector existe et est un string
      const selector = message.selector; // Type: string ✅
      this.handleGetDom(selector).then(sendResponse);
      break;

    case MessageAction.START_POLLING:
      // TypeScript sait que message.user_id existe et est un number
      const userId = message.user_id; // Type: number ✅
      initPolling(userId).then(sendResponse);
      break;
  }

  return true; // Async response
});

// Envoi typé
async function sendMessage<T>(
  tabId: number,
  message: BackgroundMessage
): Promise<MessageResponse<T>> {
  return chrome.tabs.sendMessage(tabId, message);
}

// Usage avec autocomplete!
const response = await sendMessage(tabId, {
  action: MessageAction.GET_DOM_ELEMENTS,
  selector: 'body'
  // ✅ TypeScript valide que selector existe
  // ✅ Autocomplete sur action
  // ❌ Erreur si typo: { action: 'GET_DOM_ELEMENZ' }
});
```

**Avantages**:
- ✅ Autocomplete complet
- ✅ Détection typos compile-time
- ✅ Types validés
- ✅ Refactoring safe

---

## 6. Injection de Dépendances

### ❌ AVANT

```typescript
class BackgroundService {
  constructor() {
    // Couplage fort avec chrome API
    chrome.runtime.onMessage.addListener(/* ... */);
  }

  private async handleMessage(message: Message) {
    // Impossible de tester sans vraie extension
    const tabs = await chrome.tabs.query(/* ... */);
    await chrome.storage.local.set(/* ... */);
    await chrome.notifications.create(/* ... */);
  }
}

// Test impossible!
describe('BackgroundService', () => {
  it('should handle message', async () => {
    const service = new BackgroundService();
    // ❌ Comment tester sans chrome API réel?
  });
});
```

**Problèmes**:
- Impossible de tester unitairement
- Couplage fort chrome API
- Mocking difficile

---

### ✅ APRÈS

```typescript
// abstractions/tab-manager.interface.ts
export interface ITabManager {
  findVintedTab(): Promise<number>;
  sendMessage<T>(tabId: number, message: any): Promise<T>;
  reload(tabId: number): Promise<void>;
}

export interface IStorageManager {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T): Promise<void>;
  remove(key: string): Promise<void>;
}

export interface INotifier {
  show(title: string, message: string): Promise<void>;
}

// implementations/chrome-tab-manager.ts
export class ChromeTabManager implements ITabManager {
  async findVintedTab(): Promise<number> {
    const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });
    if (tabs.length === 0) throw new VintedNotFoundError();
    return tabs[0].id!;
  }

  async sendMessage<T>(tabId: number, message: any): Promise<T> {
    return chrome.tabs.sendMessage(tabId, message);
  }

  async reload(tabId: number): Promise<void> {
    await chrome.tabs.reload(tabId);
  }
}

// background-service.ts
export class BackgroundService {
  constructor(
    private tabManager: ITabManager,
    private storage: IStorageManager,
    private notifier: INotifier
  ) {
    // Injection de dépendances
  }

  async handleFetchVinted(): Promise<VintedData> {
    const tabId = await this.tabManager.findVintedTab();
    const data = await this.tabManager.sendMessage(tabId, {
      action: 'FETCH_VINTED_DATA'
    });
    return data;
  }
}

// Production (main.ts)
const service = new BackgroundService(
  new ChromeTabManager(),
  new ChromeStorageManager(),
  new ChromeNotifier()
);

// Tests (background-service.test.ts)
class MockTabManager implements ITabManager {
  async findVintedTab(): Promise<number> {
    return 123; // Tab ID mockée
  }

  async sendMessage<T>(tabId: number, message: any): Promise<T> {
    return { success: true, data: [] } as T;
  }

  async reload(tabId: number): Promise<void> {}
}

describe('BackgroundService', () => {
  it('should fetch vinted data', async () => {
    const service = new BackgroundService(
      new MockTabManager(),
      new MockStorageManager(),
      new MockNotifier()
    );

    const result = await service.handleFetchVinted();

    // ✅ Test unitaire pur, sans chrome API!
    expect(result).toEqual({ success: true, data: [] });
  });
});
```

**Avantages**:
- ✅ Tests unitaires purs
- ✅ Mocking facile
- ✅ Code découplé
- ✅ Remplaçable (ex: Firefox API)

---

## 7. Rate Limiting

### ❌ AVANT

```typescript
async function getAllProducts(): Promise<any[]> {
  let page = 1;
  let allProducts: any[] = [];

  while (hasMore) {
    // ❌ Requête immédiate, pas de délai
    const data = await fetchVinted(
      `/api/v2/wardrobe/${userId}/items?page=${page}&per_page=20`
    );

    allProducts = allProducts.concat(data.items);
    page++;
  }

  return allProducts;
}
```

**Problèmes**:
- Boucle sans throttling
- Risque ban IP Vinted
- Pas de respect limites API

---

### ✅ APRÈS

```typescript
import { RateLimiter } from '../utils/rate-limiter'; // Existe déjà!

// Configuration Vinted: 5 requêtes / 10 secondes
const vintedRateLimiter = new RateLimiter(5, 10000);

async function fetchVinted(endpoint: string): Promise<any> {
  // Attendre si limite atteinte
  await vintedRateLimiter.acquire();

  BackgroundLogger.debug(`Requête Vinted: ${endpoint}`);

  const response = await fetch(`https://www.vinted.fr${endpoint}`, {
    credentials: 'include',
    headers: getVintedHeaders()
  });

  if (!response.ok) {
    throw new VintedAPIError(
      response.status,
      response.statusText,
      endpoint
    );
  }

  return response.json();
}

async function getAllProducts(): Promise<any[]> {
  let page = 1;
  let allProducts: any[] = [];

  while (hasMore) {
    // ✅ Rate limiter automatique
    const data = await fetchVinted(
      `/api/v2/wardrobe/${userId}/items?page=${page}&per_page=20`
    );

    allProducts = allProducts.concat(data.items);

    BackgroundLogger.info(`Page ${page}: ${data.items.length} produits`);

    page++;

    // Optionnel: délai supplémentaire entre pages
    if (hasMore) {
      await sleep(500); // 500ms entre pages
    }
  }

  return allProducts;
}
```

**Avantages**:
- ✅ Rate limiting automatique
- ✅ Protection ban API
- ✅ Configurable
- ✅ Réutilisable

---

## 8. Timeout Messages

### ❌ AVANT

```typescript
// Envoi sans timeout
const response = await chrome.tabs.sendMessage(tabId, {
  action: 'FETCH_VINTED_DATA'
});
// ❌ Si content script ne répond jamais → freeze infini
```

**Problèmes**:
- Freeze si content script crash
- Pas de feedback utilisateur
- UI bloquée

---

### ✅ APRÈS

```typescript
// utils/message-with-timeout.ts
import { TimeoutError } from './errors';

export async function sendMessageWithTimeout<T>(
  tabId: number,
  message: any,
  timeoutMs: number = 10000
): Promise<T> {
  return new Promise((resolve, reject) => {
    // Timer timeout
    const timer = setTimeout(() => {
      reject(new TimeoutError(
        `Content script did not respond within ${timeoutMs}ms`,
        'content-script',
        timeoutMs
      ));
    }, timeoutMs);

    // Envoi message
    chrome.tabs.sendMessage(tabId, message, (response) => {
      clearTimeout(timer);

      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(response);
      }
    });
  });
}

// Usage
private async handleFetchVinted(): Promise<VintedData> {
  const tabId = await this.findVintedTab();

  try {
    const response = await sendMessageWithTimeout<MessageResponse<VintedData>>(
      tabId,
      { action: MessageAction.FETCH_VINTED_DATA },
      10000 // 10 secondes max
    );

    if (!response.success) {
      throw new Error(response.error);
    }

    return response.data!;

  } catch (error) {
    if (error instanceof TimeoutError) {
      // Gérer timeout spécifiquement
      BackgroundLogger.error('Content script timeout, rechargement onglet');

      // Recharger et réessayer
      await chrome.tabs.reload(tabId);
      await sleep(2000);

      return this.handleFetchVinted(); // Retry
    }

    throw error;
  }
}
```

**Avantages**:
- ✅ Timeout configurable
- ✅ Erreur spécifique
- ✅ Retry possible
- ✅ UI non bloquée

---

## 🎯 Script de Migration Automatique

Pour faciliter la migration des logs, voici un script Node.js :

```javascript
// scripts/migrate-logs.js
const fs = require('fs');
const path = require('path');

const CONTEXT_MAP = {
  'background': 'BackgroundLogger',
  'content': 'ContentLogger',
  'popup': 'PopupLogger',
  'auth': 'AuthLogger',
  'task-poller': 'TaskPollerLogger',
  'proxy': 'ProxyLogger',
  'vinted': 'VintedLogger',
  'api': 'APILogger'
};

function detectContext(filePath) {
  if (filePath.includes('/background/')) return 'BackgroundLogger';
  if (filePath.includes('/content/')) return 'ContentLogger';
  if (filePath.includes('/popup/')) return 'PopupLogger';
  if (filePath.includes('/composables/useAuth')) return 'AuthLogger';
  if (filePath.includes('/api/')) return 'APILogger';
  return 'Logger';
}

function migrateFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  const context = detectContext(filePath);

  // Ajouter import si nécessaire
  if (!content.includes('import') && content.includes('console.log')) {
    content = `import { ${context} } from '../utils/logger';\n\n` + content;
  }

  // Remplacer console.log
  content = content.replace(/console\.log\((.*?)\);?/g, (match, args) => {
    return `${context}.debug(${args});`;
  });

  // Remplacer console.error
  content = content.replace(/console\.error\((.*?)\);?/g, (match, args) => {
    return `${context}.error(${args});`;
  });

  // Remplacer console.warn
  content = content.replace(/console\.warn\((.*?)\);?/g, (match, args) => {
    return `${context}.warn(${args});`;
  });

  // Supprimer les séparateurs ASCII
  content = content.replace(/console\.log\('=+'\);?\n?/g, '');

  fs.writeFileSync(filePath, content, 'utf8');
  console.log(`✅ Migrated: ${filePath}`);
}

// Parcourir tous les fichiers .ts
function migrateAll(dir) {
  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      migrateAll(fullPath);
    } else if (file.endsWith('.ts') && !file.endsWith('.test.ts')) {
      migrateFile(fullPath);
    }
  });
}

// Lancer migration
migrateAll('./src');
console.log('✅ Migration terminée!');
```

**Usage**:
```bash
node scripts/migrate-logs.js
```

---

## ✅ Checklist de Validation

Après chaque refactoring :

- [ ] Code compile sans erreur TypeScript
- [ ] Tests unitaires passent
- [ ] Test manuel Chrome
- [ ] Test manuel Firefox
- [ ] Logs en dev : activés
- [ ] Logs en prod : désactivés
- [ ] Performance identique ou meilleure
- [ ] Pas de régression fonctionnelle

---

## 📚 Ressources

- [TypeScript Handbook - Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [Discriminated Unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions)
- [Dependency Injection in TypeScript](https://dev.to/willmcconnell/dependency-injection-in-typescript-2m5k)
- [Rate Limiting Strategies](https://stripe.com/blog/rate-limiters)

---

**Fin des exemples**

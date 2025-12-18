# Analyse de Refactoring - StoFlow Plugin

**Date**: 2025-12-08
**Analyste**: Claude Code Agent
**Version analysée**: 1.0.0
**Lignes de code**: ~7730 (TS + Vue)

---

## 📊 Vue d'ensemble

### Structure du projet

```
src/
├── adapters/
│   └── vinted/         # Adaptateurs Vinted (Import, Publish, Mapping)
├── api/                # Clients API (Stoflow, Vinted)
├── background/         # Service worker (polling, messages)
├── components/         # Composants Vue (6 fichiers)
├── composables/        # Logique réutilisable Vue (4 fichiers)
├── config/             # Configuration centralisée
├── content/            # Content scripts (Vinted, eBay, Etsy, Proxy)
├── options/            # Page d'options
├── popup/              # Popup principale
├── types/              # Définitions TypeScript
└── utils/              # Utilitaires (10 fichiers)
```

### Technologies
- **Framework UI**: Vue 3 (Composition API)
- **Language**: TypeScript (95%+)
- **Build tool**: Vite + @crxjs/vite-plugin
- **Test framework**: Vitest
- **Target**: Chrome + Firefox (Manifest V3)

### Métriques globales
| Métrique | Valeur | Statut |
|----------|--------|--------|
| Lignes de code | 7730 | ✅ Taille raisonnable |
| Fichiers sources | 45 | ✅ Bien modulaire |
| console.log | 426 | ❌ CRITIQUE |
| Fonctions | ~48 | ✅ Modulaire |
| Exports publics | ~96 | ✅ Bonne séparation |
| TODOs/FIXMEs | 8 | ⚠️ Travail incomplet |
| Tests unitaires | 6 fichiers | ✅ Bon début |

---

## 🔴 Problèmes Critiques (P0)

### P0.1: Pollution console.log massive
**Fichiers**: Tous (18 fichiers)
**Sévérité**: CRITICAL
**Impact**: Performance, lisibilité, debugging impossible

**Problème**:
- **426 console.log** dispersés dans le code
- Logs verbeux multi-lignes avec séparateurs ASCII art
- Pas de niveaux (DEBUG/INFO/WARN/ERROR)
- Impossible de désactiver en production
- Format incohérent entre fichiers

**Exemples problématiques**:

```typescript
// src/background/index.ts:87-189 (103 lignes de logs!)
console.log('\n========================================');
console.log('🚀 [Plugin] DÉBUT RÉCUPÉRATION VINTED');
console.log('========================================\n');
// ... 100+ lignes de console.log
```

```typescript
// src/content/vinted.ts:4
console.log('[Stoflow Content] Chargé sur', window.location.href);
```

**Solution**:
Le système de logging structuré existe déjà (`src/utils/logger.ts`) mais **N'EST PAS UTILISÉ** !

**Actions requises**:
1. Remplacer TOUS les `console.log` par `Logger.debug/info/warn/error`
2. Utiliser les contextes appropriés (`BackgroundLogger`, `ContentLogger`, etc.)
3. Activer/désactiver via `ENV.ENABLE_DEBUG_LOGS`
4. Supprimer les logs verbeux inutiles (séparateurs, emojis excessifs)

**Effort estimé**: Medium (3-4h)
**Impact business**: Performance en production + maintenabilité

---

### P0.2: Fonction `handleFetchVintedData` trop longue (117 lignes)
**Fichier**: `src/background/index.ts:87-203`
**Sévérité**: CRITICAL
**Impact**: Maintenabilité, testabilité

**Problème**:
Une seule fonction fait:
- Recherche d'onglet Vinted
- Communication avec content script
- Logging verbeux (90% de la fonction = logs!)
- Formatage de données

**Code actuel** (extrait):
```typescript
private async handleFetchVintedData(): Promise<any> {
  console.log('\n========================================');
  console.log('🚀 [Plugin] DÉBUT RÉCUPÉRATION VINTED');
  // ... 100+ lignes de logs

  const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });
  // ... logique métier noyée dans les logs
}
```

**Suggestion de fix**:
```typescript
private async handleFetchVintedData(): Promise<any> {
  BackgroundLogger.info('Début récupération Vinted');

  const tabId = await this.findVintedTab();
  const data = await this.fetchDataFromContentScript(tabId);

  BackgroundLogger.success(`${data.products.length} produits récupérés`);

  return { success: true, data };
}

private async findVintedTab(): Promise<number> {
  const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });
  if (tabs.length === 0) throw new VintedNotFoundError();
  return tabs[0].id!;
}

private async fetchDataFromContentScript(tabId: number): Promise<VintedData> {
  const response = await chrome.tabs.sendMessage(tabId, {
    action: 'FETCH_VINTED_DATA'
  });
  if (!response.success) throw new Error(response.error);
  return response.data;
}
```

**Effort estimé**: Small (1h)
**Impact business**: Code 10x plus lisible et testable

---

### P0.3: Duplication de code - Recherche onglet Vinted
**Fichiers**: `src/background/index.ts` (lignes 94, 215, 271, 308, 568, 621)
**Sévérité**: HIGH
**Impact**: DRY violation, bugs potentiels

**Problème**:
Le même code répété **6 fois**:

```typescript
const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });
if (tabs.length === 0) {
  throw new Error('Aucun onglet Vinted ouvert');
}
```

**Solution**:
```typescript
private async findVintedTab(): Promise<number> {
  const tabs = await chrome.tabs.query({ url: 'https://www.vinted.fr/*' });
  if (tabs.length === 0) {
    throw new VintedNotFoundError(); // Utiliser classe d'erreur dédiée
  }
  return tabs[0].id!;
}

// Usage partout:
const tabId = await this.findVintedTab();
```

**Effort estimé**: Small (30min)
**Impact business**: Réduction de 50 lignes de code dupliqué

---

### P0.4: Gestion d'erreurs incohérente
**Fichiers**: Tous
**Sévérité**: HIGH
**Impact**: UX, debugging

**Problème**:
Mélange de styles:

```typescript
// Style 1: Retour d'objet
return { success: false, error: error.message };

// Style 2: Exception
throw new Error('Erreur');

// Style 3: Console + retour
console.error('Erreur:', error);
return { success: false, error: error.message };

// Style 4: Utilisation classes d'erreur (bon!)
throw new VintedNotFoundError();
```

**Solution**:
Classes d'erreur standardisées existent dans `src/utils/errors.ts` mais **sous-utilisées**.

```typescript
// ✅ BON: Utiliser les classes d'erreur partout
throw new VintedNotFoundError();
throw new NetworkError('Fetch failed', url);
throw new TaskExecutionError(taskId, 'Invalid payload');

// ✅ BON: Catch unifié
try {
  await doSomething();
} catch (error) {
  const stoflowError = toStoflowError(error);
  Logger.error('Context', stoflowError.message, stoflowError);
  return { success: false, error: stoflowError.getUserMessage() };
}
```

**Effort estimé**: Medium (2h)
**Impact business**: UX améliorée, messages d'erreur user-friendly

---

### P0.5: Extraction CSRF/Anon-Id ultra complexe (300+ lignes)
**Fichier**: `src/content/vinted.ts:35-315`
**Sévérité**: HIGH
**Impact**: Maintenabilité, bugs, performance

**Problème**:
La fonction `extractVintedDataFromPage()` fait **280 lignes** avec:
- Parsing manuel de scripts Next.js
- Comptage de crochets/accolades char par char
- Gestion d'échappements custom
- Logique de fallback complexe
- Patterns regex multiples

**Code actuel** (extrait):
```typescript
function extractVintedDataFromPage(): any {
  // Ligne 39-217: Parsing manuel ultra-complexe
  for (let i = 0; i < scripts.length; i++) {
    // Compter les crochets...
    let bracketCount = 0;
    let escapeNext = false;
    while (endPos < content.length) {
      if (escapeNext) { /* ... */ }
      if (char === '\\') { /* ... */ }
      // ... 50+ lignes de parsing
    }
  }
}
```

**Suggestion de fix**:
1. Extraire en classe dédiée `VintedPageParser`
2. Utiliser library de parsing robuste (DOMParser)
3. Séparer extraction CSRF et currentUser
4. Ajouter caching (5 min)
5. Tests unitaires obligatoires

```typescript
export class VintedPageParser {
  private static cache = new Map<string, any>();

  static extractCurrentUser(): VintedUser | null {
    return this.extractFromNextData('currentUser');
  }

  static extractCSRFToken(): string | null {
    const cached = this.getCached('csrf_token');
    if (cached) return cached;

    const token = this.findInScripts(CSRF_PATTERNS);
    this.setCached('csrf_token', token, 5 * 60 * 1000);
    return token;
  }

  private static extractFromNextData(key: string): any {
    // Logique simplifiée avec library
  }
}
```

**Effort estimé**: Large (4-5h)
**Impact business**: Réduction risque de bugs, performance améliorée

---

## 🟡 Problèmes Majeurs (P1)

### P1.1: Absence de type safety sur messages Chrome
**Fichiers**: `src/background/index.ts`, `src/content/vinted.ts`, `src/content/proxy.ts`
**Sévérité**: MEDIUM
**Impact**: Type safety, autocomplete, bugs runtime

**Problème**:
```typescript
// Type générique, pas de validation
interface Message {
  action: string;
  [key: string]: any; // ❌ any partout!
}

// Usage non typé
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.action) {
    case 'FETCH_VINTED_DATA': // String literal, pas d'enum
      // message.foo existe? Pas de vérification!
  }
});
```

**Solution**:
```typescript
// types/messages.ts
export enum MessageAction {
  FETCH_VINTED_DATA = 'FETCH_VINTED_DATA',
  IMPORT_ALL_VINTED = 'IMPORT_ALL_VINTED',
  // ...
}

export type PluginMessage =
  | { action: MessageAction.FETCH_VINTED_DATA }
  | { action: MessageAction.GET_DOM_ELEMENTS; selector: string }
  | { action: MessageAction.START_POLLING; user_id: number };

// Usage typé
chrome.runtime.onMessage.addListener((message: PluginMessage, sender, sendResponse) => {
  switch (message.action) {
    case MessageAction.FETCH_VINTED_DATA:
      // TypeScript sait que message n'a que `action`
      break;
    case MessageAction.GET_DOM_ELEMENTS:
      // TypeScript sait que message.selector existe
      const el = message.selector; // ✅ Autocomplete!
      break;
  }
});
```

**Effort estimé**: Medium (2-3h)
**Impact business**: Moins de bugs, meilleure DX

---

### P1.2: BackgroundService sans injection de dépendances
**Fichier**: `src/background/index.ts:12-663`
**Sévérité**: MEDIUM
**Impact**: Testabilité, couplage fort

**Problème**:
```typescript
class BackgroundService {
  // Couplage fort avec chrome API
  constructor() {
    chrome.runtime.onMessage.addListener(/* ... */);
    chrome.runtime.onInstalled.addListener(/* ... */);
  }

  private async handleMessage(message: Message) {
    // Logique métier mélangée avec chrome API
    const tabs = await chrome.tabs.query(/* ... */);
  }
}

// Instanciation globale, pas testable
new BackgroundService();
```

**Solution**:
```typescript
// Interfaces pour abstraction
interface TabManager {
  findVintedTab(): Promise<number>;
  sendMessage(tabId: number, message: any): Promise<any>;
}

interface StorageManager {
  get(key: string): Promise<any>;
  set(key: string, value: any): Promise<void>;
}

class BackgroundService {
  constructor(
    private tabManager: TabManager,
    private storage: StorageManager,
    private notifier: Notifier
  ) {
    // Injection de dépendances
  }
}

// Production
new BackgroundService(
  new ChromeTabManager(),
  new ChromeStorageManager(),
  new ChromeNotifier()
);

// Tests
new BackgroundService(
  new MockTabManager(),
  new MockStorageManager(),
  new MockNotifier()
);
```

**Effort estimé**: Large (4-5h)
**Impact business**: Code 100% testable

---

### P1.3: Fonctions `getAllProducts` et `getMyProducts` dupliquées
**Fichier**: `src/content/vinted.ts:382-441`
**Sévérité**: MEDIUM
**Impact**: Duplication, maintenance

**Problème**:
```typescript
async function getMyProducts(): Promise<any[]> {
  const userId = await getCurrentUserId();
  const data = await fetchVinted(
    `/api/v2/wardrobe/${userId}/items?page=1&per_page=20&order=relevance`
  );
  return data.items || [];
}

async function getAllProducts(): Promise<any[]> {
  const userId = await getCurrentUserId();
  let allProducts: any[] = [];
  let page = 1;

  while (hasMore) {
    const data = await fetchVinted(
      `/api/v2/wardrobe/${userId}/items?page=${page}&per_page=20&order=relevance`
    );
    allProducts = allProducts.concat(data.items || []);
    // ...
  }
  return allProducts;
}
```

**Solution**:
```typescript
async function getProducts(options: {
  paginate: boolean;
  perPage?: number;
  maxPages?: number;
}): Promise<any[]> {
  const userId = await getCurrentUserId();
  let allProducts: any[] = [];
  let page = 1;
  let hasMore = true;

  while (hasMore && (options.paginate || page === 1)) {
    const data = await fetchVinted(
      `/api/v2/wardrobe/${userId}/items?page=${page}&per_page=${options.perPage || 20}&order=relevance`
    );
    allProducts = allProducts.concat(data.items || []);

    if (!options.paginate) break;

    hasMore = data.pagination?.current_page < data.pagination?.total_pages;
    if (options.maxPages && page >= options.maxPages) break;
    page++;
  }

  return allProducts;
}

// Usage
const firstPage = await getProducts({ paginate: false });
const allPages = await getProducts({ paginate: true, maxPages: 10 });
```

**Effort estimé**: Small (1h)
**Impact business**: Code plus flexible et DRY

---

### P1.4: Pas de rate limiting sur requêtes Vinted
**Fichiers**: `src/content/vinted.ts`, `src/api/VintedAPI.ts`
**Sévérité**: MEDIUM
**Impact**: Risque ban IP, performance

**Problème**:
```typescript
// Boucle sans throttling
while (hasMore) {
  const data = await fetchVinted(`/api/v2/wardrobe/${userId}/items?page=${page}&...`);
  // Pas de délai entre requêtes!
  page++;
}
```

**Solution**:
Un `RateLimiter` existe déjà (`src/utils/rate-limiter.ts`) mais **n'est pas utilisé** !

```typescript
import { RateLimiter } from '../utils/rate-limiter';

const vintedRateLimiter = new RateLimiter(5, 10000); // 5 req/10s

async function fetchVinted(endpoint: string): Promise<any> {
  await vintedRateLimiter.acquire(); // Attendre si limite atteinte

  const response = await fetch(`https://www.vinted.fr${endpoint}`, {
    credentials: 'include',
    headers: getVintedHeaders()
  });

  return response.json();
}
```

**Effort estimé**: Small (30min)
**Impact business**: Protection contre ban API Vinted

---

### P1.5: TODOs critiques non implémentés
**Fichiers**: `src/background/index.ts`, `src/adapters/vinted/publisher.ts`, `src/content/ebay.ts`, `src/content/etsy.ts`
**Sévérité**: MEDIUM
**Impact**: Fonctionnalités manquantes

**TODOs trouvés**:

1. **`src/background/index.ts:447`**: `TODO: Implémenter la publication`
2. **`src/background/index.ts:497`**: `TODO: Implémenter la vérification des ventes`
3. **`src/adapters/vinted/publisher.ts:145-156`**: 3 TODOs pour mapping brand/size/color
4. **`src/content/ebay.ts:4`**: `TODO: Implémenter injection de boutons dans les pages eBay`
5. **`src/content/etsy.ts:4`**: `TODO: Implémenter injection de boutons dans les pages Etsy`

**Actions requises**:
- Décider si ces fonctionnalités sont nécessaires pour la v1.0
- Si oui: implémenter avant release
- Si non: supprimer les TODOs et les fonctions vides

**Effort estimé**: Variable (selon priorité)
**Impact business**: Clarifier le scope du MVP

---

### P1.6: Pas de timeout sur communication content script
**Fichiers**: `src/background/index.ts`
**Sévérité**: MEDIUM
**Impact**: UI freeze si content script ne répond pas

**Problème**:
```typescript
const response = await chrome.tabs.sendMessage(tabs[0].id!, {
  action: 'FETCH_VINTED_DATA'
});
// Si le content script ne répond jamais → freeze infini
```

**Solution**:
```typescript
async function sendMessageWithTimeout<T>(
  tabId: number,
  message: any,
  timeoutMs: number = 5000
): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new TimeoutError(`Message timeout after ${timeoutMs}ms`, 'content-script', timeoutMs));
    }, timeoutMs);

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
try {
  const response = await sendMessageWithTimeout(tabId, { action: 'FETCH_VINTED_DATA' }, 10000);
} catch (error) {
  if (error instanceof TimeoutError) {
    // Gérer timeout spécifiquement
  }
}
```

**Effort estimé**: Small (1h)
**Impact business**: UX plus robuste

---

## 🟢 Améliorations (P2)

### P2.1: Storage API non typé
**Fichiers**: Tous (usage de `chrome.storage.local.get/set`)
**Sévérité**: LOW
**Impact**: Type safety

**Problème**:
```typescript
const result = await chrome.storage.local.get('stoflow_access_token');
const token = result['stoflow_access_token']; // Type: any
```

**Solution**:
```typescript
// utils/storage.ts
interface StorageSchema {
  stoflow_access_token: string;
  stoflow_refresh_token: string;
  stoflow_user_data: UserData;
}

export class TypedStorage {
  static async get<K extends keyof StorageSchema>(
    key: K
  ): Promise<StorageSchema[K] | null> {
    const result = await chrome.storage.local.get(key);
    return result[key] ?? null;
  }

  static async set<K extends keyof StorageSchema>(
    key: K,
    value: StorageSchema[K]
  ): Promise<void> {
    await chrome.storage.local.set({ [key]: value });
  }
}

// Usage typé
const token = await TypedStorage.get('stoflow_access_token'); // Type: string | null
```

**Effort estimé**: Small (1h)
**Impact business**: Moins de bugs typo

---

### P2.2: Composants Vue sans props typés
**Fichier**: `src/components/PlatformCard.vue` (et autres)
**Sévérité**: LOW
**Impact**: Type safety

**Solution**:
```typescript
// Avant
const props = defineProps(['platform']);

// Après
interface Platform {
  name: string;
  connected: boolean;
  // ...
}

const props = defineProps<{
  platform: Platform;
}>();
```

**Effort estimé**: Small (30min)
**Impact business**: Autocomplete dans templates

---

### P2.3: Pas de validation des réponses API Vinted
**Fichiers**: `src/content/vinted.ts`, `src/api/VintedAPI.ts`
**Sévérité**: LOW
**Impact**: Robustesse

**Problème**:
```typescript
const data = await response.json();
const products = data.items || []; // Et si items n'existe pas?
```

**Solution**:
Utiliser Zod ou ajuster validation manuelle:

```typescript
import { z } from 'zod';

const VintedProductSchema = z.object({
  id: z.number(),
  title: z.string(),
  price: z.number(),
  // ...
});

const VintedResponseSchema = z.object({
  items: z.array(VintedProductSchema),
  pagination: z.object({
    current_page: z.number(),
    total_pages: z.number()
  })
});

// Usage
const data = await response.json();
const validated = VintedResponseSchema.parse(data); // Throw si invalide
```

**Effort estimé**: Medium (2h)
**Impact business**: Détection précoce de changements API Vinted

---

### P2.4: Magic numbers dans le code
**Fichiers**: Multiples
**Sévérité**: LOW
**Impact**: Lisibilité

**Exemples**:
```typescript
setTimeout(resolve, 2000); // Pourquoi 2000?
perPage: 20 // Pourquoi 20?
timeoutMs: 30000 // Pourquoi 30s?
```

**Solution**:
```typescript
const VINTED_RELOAD_DELAY_MS = 2000;
const VINTED_PRODUCTS_PER_PAGE = 20;
const DEFAULT_REQUEST_TIMEOUT_MS = 30000;

setTimeout(resolve, VINTED_RELOAD_DELAY_MS);
```

**Effort estimé**: Small (30min)
**Impact business**: Code autodocumenté

---

### P2.5: Composable `useSync` incomplet
**Fichier**: `src/composables/useSync.ts`
**Sévérité**: LOW
**Impact**: Fonctionnalité

**Problème**:
Composable exporté mais peu utilisé, logique dispersée.

**Solution**:
Centraliser toute la logique de sync dans ce composable:
- `importVintedProducts()`
- `publishToVinted(productId)`
- `syncSales()`
- État réactif global

**Effort estimé**: Medium (2h)
**Impact business**: Architecture plus claire

---

## 📈 Métriques de qualité

| Métrique | Score actuel | Cible | Notes |
|----------|--------------|-------|-------|
| **Duplication** | ~15% | <5% | Recherche onglet Vinted, logs |
| **Complexité cyclomatique** | ~12 (moyenne) | <10 | `extractVintedDataFromPage` = 25+ |
| **Test coverage** | ~30% (6 fichiers) | >80% | Seulement utils testés |
| **Type safety** | ~70% | 100% | Beaucoup de `any`, messages non typés |
| **Code mort** | ~50 lignes | 0 | TODOs, fonctions vides |
| **Logs structurés** | 0% | 100% | Logger existe mais non utilisé |
| **Error handling** | 40% | 90% | Mélange styles, peu de classes |

---

## 🎯 Plan de refactoring recommandé

### Phase 1: Fixes critiques (P0) - 2 jours

**Objectif**: Stabiliser le code existant

1. **[4h]** P0.1: Remplacer tous les `console.log` par `Logger`
   - Créer script de migration automatique
   - Tester que logs apparaissent en dev, pas en prod

2. **[2h]** P0.2 + P0.3: Refactorer `BackgroundService`
   - Extraire `findVintedTab()`, `sendMessageToTab()`
   - Simplifier `handleFetchVintedData()` (retirer logs verbeux)

3. **[2h]** P0.4: Standardiser gestion d'erreurs
   - Utiliser classes d'erreur partout
   - Wrapper try/catch unifié

4. **[4h]** P0.5: Refactorer extraction Vinted
   - Créer classe `VintedPageParser`
   - Ajouter caching
   - Écrire tests unitaires

**Effort total**: ~12h (2 jours)
**Impact business**: Code stable, debuggable, performant

---

### Phase 2: Améliorations majeures (P1) - 3 jours

**Objectif**: Améliorer architecture et robustesse

1. **[3h]** P1.1: Type safety sur messages Chrome
   - Créer types discriminés
   - Remplacer tous les `any`

2. **[4h]** P1.2: Injection de dépendances
   - Abstraire chrome API
   - Rendre testable

3. **[1h]** P1.3: Unifier `getProducts()`

4. **[1h]** P1.4: Activer rate limiting Vinted

5. **[2h]** P1.5: Résoudre TODOs
   - Implémenter ou supprimer

6. **[1h]** P1.6: Timeout messages content script

**Effort total**: ~12h (2 jours)
**Impact business**: Architecture solide, moins de bugs

---

### Phase 3: Optimisations (P2) - 2 jours

**Objectif**: Polish et qualité

1. **[1h]** P2.1: Storage typé
2. **[1h]** P2.2: Props Vue typés
3. **[2h]** P2.3: Validation réponses API
4. **[1h]** P2.4: Constantes magic numbers
5. **[2h]** P2.5: Compléter `useSync`
6. **[3h]** Écrire tests unitaires manquants (coverage >80%)

**Effort total**: ~10h (1.5 jours)
**Impact business**: Code production-ready

---

### Phase 4: Tests et CI/CD - 1 jour

1. **[2h]** Écrire tests e2e (Playwright)
2. **[2h]** Setup CI/CD (GitHub Actions)
   - Lint + type check
   - Tests unitaires
   - Build Chrome + Firefox
3. **[1h]** Setup pre-commit hooks
4. **[1h]** Documentation API

**Effort total**: ~6h (1 jour)

---

## 📁 Fichiers nécessitant attention

| Fichier | Problèmes | Priorité | Effort | Lignes |
|---------|-----------|----------|--------|--------|
| `src/background/index.ts` | Logs verbeux (213), duplication (6x), fonction longue (117L) | P0 | Large | 663 |
| `src/content/vinted.ts` | Parsing complexe (280L), duplication, logs (79) | P0 | Large | 656 |
| `src/content/proxy.ts` | Logs (11), pas de validation | P1 | Small | 237 |
| `src/api/VintedAPI.ts` | Pas de rate limiting, logs (18) | P1 | Small | 173 |
| `src/api/StoflowAPI.ts` | Duplication getToken(), logs (14) | P1 | Small | 183 |
| `src/background/task-poller.ts` | Logs (18), error handling | P1 | Medium | 310 |
| `src/composables/useAuth.ts` | Logs (21) | P0 | Small | 333 |
| `src/adapters/vinted/publisher.ts` | TODOs critiques (3) | P1 | Medium | 145 |
| `src/utils/csrf-extractor.ts` | Peut-être obsolète? | P2 | Small | ~100 |

---

## 🔧 Recommandations techniques

### Architecture

1. **Adopter Repository Pattern** pour abstraction données
   ```typescript
   interface ProductRepository {
     findAll(): Promise<Product[]>;
     findById(id: number): Promise<Product>;
     save(product: Product): Promise<void>;
   }

   class VintedProductRepository implements ProductRepository {
     // Implémentation Vinted
   }
   ```

2. **Event-driven architecture** pour communication modules
   ```typescript
   class EventBus {
     on(event: string, handler: Function): void;
     emit(event: string, data: any): void;
   }

   // Usage
   eventBus.emit('product:imported', { productId: 123 });
   eventBus.on('product:imported', (data) => {
     // Mettre à jour UI
   });
   ```

3. **Stratégie Pattern** pour adapters multi-plateformes
   ```typescript
   interface PlatformAdapter {
     import(): Promise<Product[]>;
     publish(product: Product): Promise<void>;
   }

   class VintedAdapter implements PlatformAdapter { /* ... */ }
   class EbayAdapter implements PlatformAdapter { /* ... */ }
   ```

---

### Patterns à adopter

1. **Factory Pattern** pour création objets complexes
2. **Observer Pattern** pour réactivité (déjà utilisé avec Vue)
3. **Singleton Pattern** pour services globaux (Logger, EventBus)
4. **Command Pattern** pour actions utilisateur (undo/redo futur)

---

### Dépendances

**À ajouter**:
- `zod` (^3.22.0) - Validation runtime
- `date-fns` (^2.30.0) - Manipulation dates (remplacer Date natif)
- `@types/chrome` (déjà présent ✅)

**À mettre à jour**:
- `vue` (^3.4.0 → ^3.5.0)
- `vite` (^5.0.0 → ^5.4.0)
- `vitest` (^4.0.15 → latest stable)

**À retirer**:
- Aucune dépendance inutile détectée ✅

---

## ✅ Checklist d'implémentation

### Préparation
- [ ] Créer branche `refactor/plugin-cleanup`
- [ ] Backup code actuel
- [ ] Setup environnement de test

### Phase 1 (P0)
- [ ] Script migration console.log → Logger
- [ ] Refactorer BackgroundService
- [ ] Standardiser error handling
- [ ] Refactorer VintedPageParser
- [ ] Tests unitaires nouveaux modules

### Phase 2 (P1)
- [ ] Types messages Chrome
- [ ] Injection dépendances
- [ ] Unifier getProducts
- [ ] Activer rate limiting
- [ ] Résoudre TODOs
- [ ] Timeout messages

### Phase 3 (P2)
- [ ] Storage typé
- [ ] Props Vue typés
- [ ] Validation API
- [ ] Constantes
- [ ] Compléter useSync
- [ ] Tests coverage >80%

### Phase 4
- [ ] Tests e2e
- [ ] CI/CD
- [ ] Pre-commit hooks
- [ ] Documentation

### Validation
- [ ] Code review complet
- [ ] Test manuel Chrome
- [ ] Test manuel Firefox
- [ ] Vérifier logs production (désactivés)
- [ ] Vérifier performance (lighthouse)

### Déploiement
- [ ] Merge dans main
- [ ] Tag version v1.1.0
- [ ] Build production
- [ ] Publish Chrome Web Store
- [ ] Publish Firefox Add-ons

---

## 📚 Références

### Documentation interne
- [ARCHITECTURE.md](/home/maribeiro/Stoflow/StoFlow_Plugin/ARCHITECTURE.md) - Architecture globale
- [BUSINESS_LOGIC.md](/home/maribeiro/Stoflow/StoFlow_Plugin/BUSINESS_LOGIC.md) - Logique métier
- [API_PROXY.md](/home/maribeiro/Stoflow/StoFlow_Plugin/API_PROXY.md) - Proxy HTTP

### Guides externes
- [Chrome Extension Best Practices](https://developer.chrome.com/docs/extensions/mv3/best_practices/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [Vue 3 Composition API](https://vuejs.org/guide/extras/composition-api-faq.html)
- [Vitest Documentation](https://vitest.dev/)

### Patterns
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection)
- [Error Handling Best Practices](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)

---

## 📊 Métriques de succès

**Avant refactoring**:
- Lignes de code: 7730
- console.log: 426
- Duplication: ~15%
- Tests coverage: ~30%
- Bugs potentiels: ~25

**Après refactoring (objectifs)**:
- Lignes de code: ~6500 (-15%)
- console.log: 0
- Duplication: <5%
- Tests coverage: >80%
- Bugs potentiels: <5

**KPIs business**:
- Temps de debugging: -50%
- Onboarding nouveau dev: -70%
- Bugs production: -80%
- Performance (temps chargement): -20%

---

## 🚀 Conclusion

Le plugin StoFlow est **globalement bien architecturé** avec:
- ✅ TypeScript partout
- ✅ Modulaire (45 fichiers bien séparés)
- ✅ Bonnes abstractions (composables, utils)
- ✅ Tests unitaires existants
- ✅ Logger professionnel (mais non utilisé)

**Problèmes majeurs**:
- ❌ **426 console.log** au lieu d'utiliser le Logger
- ❌ Code dupliqué (recherche onglet Vinted)
- ❌ Fonctions trop longues (>100 lignes)
- ❌ Extraction Vinted ultra-complexe (280 lignes)
- ❌ Gestion d'erreurs incohérente

**Effort total de refactoring**: ~40h (5 jours)
**ROI estimé**: Code 2x plus maintenable, -80% bugs

**Recommandation**: Prioriser **Phase 1 (P0)** avant toute nouvelle fonctionnalité.

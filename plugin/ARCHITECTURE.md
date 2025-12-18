# 🏗️ Architecture du Plugin StoFlow

## 📋 Vue d'ensemble

StoFlow est une extension Firefox (Manifest V3) qui extrait automatiquement les données utilisateur depuis les pages Vinted pour permettre la synchronisation avec l'application StoFlow.

---

## 🎯 Architecture Générale

```
┌─────────────────────────────────────────────────────────┐
│                    FIREFOX BROWSER                       │
│                                                          │
│  ┌────────────────┐      ┌──────────────────┐          │
│  │  Popup UI      │◄────►│  Background      │          │
│  │  (Vue 3)       │      │  Service Worker  │          │
│  └────────────────┘      └──────────────────┘          │
│         │                         │                      │
│         │                         │                      │
│         └─────────┬───────────────┘                      │
│                   │                                      │
│                   ▼                                      │
│         ┌──────────────────┐                            │
│         │  Content Script  │                            │
│         │  (vinted.ts)     │                            │
│         └──────────────────┘                            │
│                   │                                      │
└───────────────────┼──────────────────────────────────────┘
                    │
                    ▼
          ┌─────────────────┐
          │  VINTED.FR      │
          │  (DOM + APIs)   │
          └─────────────────┘
```

---

## 📦 Structure des Fichiers

```
StoFlow_Plugin/
├── manifest.json           # Configuration de l'extension
├── src/
│   ├── popup/             # Interface utilisateur (Vue 3)
│   │   ├── Popup.vue      # Composant principal du popup
│   │   └── index.html     # Point d'entrée HTML
│   │
│   ├── background/        # Service Worker (coordination)
│   │   └── index.ts       # Gestion des messages entre composants
│   │
│   ├── content/           # Scripts injectés dans les pages
│   │   └── vinted.ts      # 🔥 CŒUR: Extraction des données Vinted
│   │
│   ├── components/        # Composants Vue réutilisables
│   │   └── UserDataCard.vue  # Affichage des données utilisateur
│   │
│   ├── composables/       # Hooks Vue (logique réutilisable)
│   │   └── useVinted.ts   # Hook pour récupérer les données Vinted
│   │
│   └── adapters/          # Adaptateurs par plateforme
│       └── vinted/
│           └── api.ts     # Requêtes API Vinted
│
├── dist/                  # Fichiers compilés (généré par build)
└── icons/                 # Icônes de l'extension
```

---

## 🔄 Flux de Données

### 1️⃣ Extraction des Données Utilisateur

```
USER ouvre vinted.fr
    │
    ├─► Content Script (vinted.ts) s'injecte automatiquement
    │   │
    │   ├─► MÉTHODE 3A: Parse les scripts Next.js
    │   │   ├─► Cherche self.__next_f.push([...])
    │   │   ├─► Extrait l'array JSON
    │   │   ├─► Parse la string data
    │   │   └─► Extrait l'objet currentUser
    │   │
    │   └─► MÉTHODE 6: Parse les scripts pour CSRF
    │       ├─► Cherche "CSRF_TOKEN":"uuid"
    │       └─► Extrait le token avec 11 patterns regex
    │
    └─► Données extraites:
        ├─ user_id
        ├─ anon_id
        ├─ csrf_token
        ├─ login
        ├─ email
        └─ real_name
```

### 2️⃣ Communication entre Composants

```
Popup UI (Vue 3)
    │
    │ 1. User clique "Récupérer mes données"
    │
    ├──► chrome.runtime.sendMessage('GET_USER_DATA')
    │
    └──► Background Service Worker
            │
            │ 2. Reçoit le message
            │
            ├──► chrome.tabs.sendMessage(tabId, 'GET_USER_DATA')
            │
            └──► Content Script (vinted.ts)
                    │
                    │ 3. Execute extractVintedDataFromPage()
                    │
                    └──► Retourne les données
                            │
                            └──► Background ──► Popup UI
                                                    │
                                                    └─► Affiche dans UserDataCard
```

### 3️⃣ Récupération des Produits

```
Content Script appelle fetchVinted('/api/v2/wardrobe/{user_id}/items')
    │
    ├─► Utilise credentials: 'include' (cookies automatiques)
    │
    ├─► Headers ajoutés:
    │   ├─ X-CSRF-Token: {csrf_token}
    │   ├─ X-Anon-Id: {anon_id}
    │   └─ Accept-Language: fr
    │
    └─► Récupère tous les produits avec pagination:
        ├─ Page 1: 20 produits
        ├─ Page 2: 20 produits
        │   ...
        └─ Page N: produits restants
```

---

## 🛡️ Système d'Extraction Robuste

### MÉTHODE 3A - Extraction de `currentUser`

**Cible** : Scripts Next.js/React contenant `self.__next_f.push([...])`

**Algorithme** :

1. **Détection du pattern**
   ```javascript
   Patterns acceptés:
   - self.__next_f.push([...])
   - window.__next_f.push([...])
   - __next_f.push([...])
   - .__next_f.push([...])
   ```

2. **Extraction de l'array**
   ```javascript
   Comptage intelligent des crochets [ ]
   - Ignore les [ ] dans les strings
   - Gère les échappements \"
   - Trouve la fin exacte de l'array
   ```

3. **Parsing de l'array**
   ```javascript
   Array format: [id, "stringData"]
   - Cherche la string contenant "currentUser"
   - Peut être à l'index [0], [1], [2], etc.
   ```

4. **Extraction de l'objet**
   ```javascript
   Comptage intelligent des accolades { }
   - Trouve "currentUser" : {
   - Compte les { } en ignorant les échappés
   - Extrait l'objet JSON complet
   ```

**Robustesse** :
- ✅ Fonctionne si le nom de variable change (`self` → `window`)
- ✅ Fonctionne si la position dans l'array change
- ✅ Fonctionne si le format d'échappement change
- ✅ Gère les scripts minifiés/uglifiés

---

### MÉTHODE 6 - Extraction du `CSRF_TOKEN`

**Cible** : Scripts contenant le CSRF token

**Algorithme** :

1. **Détection rapide**
   ```javascript
   Recherche includes('CSRF') || includes('csrf')
   → Optimisation: évite de tester les regex sur tous les scripts
   ```

2. **11 Patterns Regex** (du plus spécifique au plus générique)
   ```javascript
   1. \\"CSRF_TOKEN\\":\\"([a-f0-9-]{36})\\"   // Échappé
   2. "CSRF_TOKEN":"([a-f0-9-]{36})"          // Normal
   3. "CSRF-TOKEN":"([a-f0-9-]{36})"          // Tiret
   4. CSRF_TOKEN : "uuid"                      // Flexible
   5. CSRF[_-]?TOKEN : "uuid"                  // Générique
   ... (11 patterns au total)
   ```

3. **Validation UUID**
   ```javascript
   [a-f0-9-]{36}  // UUID standard (stricte)
   [a-f0-9-]{30,40}  // UUID générique (flexible)
   ```

**Robustesse** :
- ✅ Fonctionne avec n'importe quelle casse (CSRF, csrf, Csrf)
- ✅ Fonctionne avec différents séparateurs (_, -)
- ✅ Fonctionne avec différents échappements (\", ", ')
- ✅ S'arrête dès qu'un pattern match (optimisé)

---

## 🔧 Technologies Utilisées

### Frontend
- **Vue 3** - Framework UI réactif (Composition API)
- **TypeScript** - Typage fort pour éviter les erreurs
- **Vite** - Build tool rapide

### Extension
- **Manifest V3** - Format moderne des extensions Firefox
- **Content Scripts** - Injection dans les pages Vinted
- **Background Service Worker** - Coordination entre composants

### API
- **Fetch API** - Requêtes HTTP avec `credentials: 'include'`
- **DOM API** - Manipulation du HTML pour extraction

---

## 📊 Performance

### Taille des fichiers compilés
```
vinted.ts (content script)    8.84 kB  (optimisé -40%)
popup.js (UI)                  9.88 kB
background.js (worker)        22.00 kB
```

### Temps d'extraction
```
Méthode 3A (currentUser)      ~10-50ms
Méthode 6 (CSRF)              ~5-20ms
Total                         ~15-70ms
```

### Optimisations
- ✅ Code minifié et compressé (gzip)
- ✅ Recherche rapide `includes()` avant regex
- ✅ Arrêt dès qu'un pattern match
- ✅ Pas de boucles récursives profondes

---

## 🔐 Sécurité

### Gestion des Cookies
- ✅ Les cookies restent dans le navigateur
- ✅ Utilisation de `credentials: 'include'` pour les requêtes
- ✅ Pas de stockage local des cookies

### Données Sensibles
- ✅ Aucune donnée envoyée à un serveur tiers
- ✅ Extraction locale uniquement
- ✅ Les tokens CSRF sont utilisés localement

### Permissions
```json
{
  "permissions": ["tabs"],
  "host_permissions": ["https://www.vinted.fr/*"]
}
```
- Accès uniquement à vinted.fr
- Pas d'accès à d'autres sites

---

## 🚀 Évolutivité

### Ajout d'une nouvelle plateforme

Pour ajouter une nouvelle plateforme (ex: eBay, Etsy) :

1. Créer `src/content/ebay.ts`
2. Implémenter les méthodes d'extraction
3. Ajouter dans `manifest.json` :
   ```json
   {
     "matches": ["https://www.ebay.fr/*"],
     "js": ["src/content/ebay.ts"]
   }
   ```
4. Créer un adaptateur `src/adapters/ebay/api.ts`

### Ajout d'une nouvelle donnée à extraire

1. Modifier `extractVintedDataFromPage()` dans `vinted.ts`
2. Ajouter la logique d'extraction
3. Mettre à jour le type de retour
4. Afficher dans `UserDataCard.vue`

---

## 🧪 Tests

### Tests manuels
1. Ouvrir Firefox
2. Charger l'extension (`about:debugging`)
3. Naviguer sur vinted.fr
4. Ouvrir la console (F12)
5. Vérifier les logs d'extraction

### Points de validation
- ✅ currentUser extrait avec toutes les clés
- ✅ CSRF_TOKEN trouvé (format UUID)
- ✅ anon_id présent
- ✅ Pas d'erreurs dans la console

---

## 📝 Logs de Debug

Le plugin affiche des logs détaillés pour le debug :

```
[Stoflow Content] 🔍 Recherche des données currentUser...
[Stoflow Content] 221 scripts trouvés
[Stoflow Content] Script 164 contient "currentUser"
[Stoflow Content] Pattern détecté: "self.__next_f.push(" à position 0
[Stoflow Content] ✅ Array extrait, longueur: 62989
[Stoflow Content] ✅ Array parsé avec 2 éléments
[Stoflow Content] ✅✅✅ currentUser parsé avec succès !
[Stoflow Content] User ID: 29535217
[Stoflow Content] anon_id: 6f646e72-5010-4da3-8640-6c0cf62aa346

[Stoflow Content] 🔍 Recherche du CSRF token...
[Stoflow Content] ✅ CSRF trouvé dans script 118 avec pattern: ...
[Stoflow Content] CSRF Token: 75f6c9fa-dc8e-4e52-a000-e09dd4084b3e

[Stoflow Content] ✅ Données extraites:
  - user_id: 29535217
  - anon_id: 6f646e72-5010-4da3-8640-6c0cf62aa346
  - csrf_token: ✅ Présent
  - login: shop.ton.outfit
  - email: matthiasribeiro77@gmail.com
```

---

## 🔄 Cycle de Vie

### Au chargement de la page
```
1. Content script injecté automatiquement
2. Attend le message 'GET_USER_DATA'
3. Reste en attente
```

### Quand l'utilisateur ouvre le popup
```
1. Popup s'affiche
2. Envoie 'GET_USER_DATA' au background
3. Background transmet au content script
4. Content script extrait les données
5. Retourne au popup
6. Popup affiche dans UserDataCard
```

### Quand l'utilisateur ferme le popup
```
1. Popup se ferme
2. Content script reste actif
3. Prêt pour la prochaine requête
```

---

## 📚 Références

- [Firefox Extension API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions)
- [Manifest V3](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json)
- [Content Scripts](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_scripts)
- [Vue 3 Composition API](https://vuejs.org/guide/introduction.html)

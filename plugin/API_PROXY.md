# 🌐 API HTTP Proxy - Documentation Backend

## 🎯 Vue d'ensemble

Le plugin StoFlow inclut maintenant un **proxy HTTP générique** qui permet au backend d'exécuter **n'importe quelle requête HTTP** en utilisant le navigateur de l'utilisateur.

### Avantages

- ✅ **Cookies automatiques** : Les cookies Vinted sont inclus automatiquement
- ✅ **Pas de CORS** : Les requêtes sont faites depuis le domaine vinted.fr
- ✅ **Flexible** : Supporte GET, POST, PUT, DELETE, PATCH
- ✅ **Générique** : Fonctionne avec n'importe quelle API
- ✅ **Pas de mise à jour** : Le plugin n'a pas besoin d'être modifié pour ajouter des fonctionnalités

---

## 📡 Communication Backend ↔ Plugin

### Architecture

```
Backend StoFlow
    │
    │ 1. Envoie requête HTTP à exécuter
    │    (URL, méthode, headers, body)
    │
    ├─► WebSocket / HTTP vers Frontend
    │
    └─► Frontend (Extension)
            │
            │ 2. Transmet au Content Script
            │
            └─► Content Script (Proxy)
                    │
                    │ 3. Exécute la requête avec fetch()
                    │    + cookies automatiques
                    │
                    └─► Vinted API
                            │
                            │ 4. Réponse
                            │
                            └─► Retour au Backend
```

---

## 🔌 API Endpoints du Proxy

### 1️⃣ Exécuter une requête unique

**Message** :
```javascript
{
  "action": "EXECUTE_HTTP_REQUEST",
  "request": {
    "url": "https://www.vinted.fr/api/v2/users/current",
    "method": "GET",  // GET, POST, PUT, DELETE, PATCH
    "headers": {
      "X-CSRF-Token": "75f6c9fa-dc8e-4e52-a000-e09dd4084b3e",
      "X-Anon-Id": "6f646e72-5010-4da3-8640-6c0cf62aa346"
    },
    "body": null,  // Optionnel (pour POST/PUT/PATCH)
    "credentials": "include",  // include | omit | same-origin
    "timeout": 30000  // Timeout en ms (défaut: 30000)
  }
}
```

**Réponse** :
```javascript
{
  "success": true,
  "status": 200,
  "statusText": "OK",
  "headers": {
    "content-type": "application/json",
    "x-request-id": "abc123",
    ...
  },
  "data": {
    // Données de la réponse (JSON parsé automatiquement)
    "id": 29535217,
    "login": "shop.ton.outfit",
    ...
  }
}
```

**Erreur** :
```javascript
{
  "success": false,
  "status": 403,
  "statusText": "Forbidden",
  "headers": {},
  "data": null,
  "error": "CSRF token invalid"
}
```

---

### 2️⃣ Exécuter plusieurs requêtes en parallèle

**Message** :
```javascript
{
  "action": "EXECUTE_BATCH_REQUESTS",
  "requests": [
    {
      "url": "https://www.vinted.fr/api/v2/users/current",
      "method": "GET"
    },
    {
      "url": "https://www.vinted.fr/api/v2/wardrobe/29535217/items?page=1",
      "method": "GET",
      "headers": {
        "X-CSRF-Token": "..."
      }
    },
    {
      "url": "https://www.vinted.fr/api/v2/catalog",
      "method": "GET"
    }
  ]
}
```

**Réponse** :
```javascript
{
  "success": true,
  "results": [
    {
      "success": true,
      "status": 200,
      "data": {...}
    },
    {
      "success": true,
      "status": 200,
      "data": {...}
    },
    {
      "success": true,
      "status": 200,
      "data": {...}
    }
  ]
}
```

---

### 3️⃣ Exécuter plusieurs requêtes en séquence

**Message** :
```javascript
{
  "action": "EXECUTE_SEQUENTIAL_REQUESTS",
  "requests": [
    {
      "url": "https://www.vinted.fr/api/v2/users/current",
      "method": "GET"
    },
    {
      "url": "https://www.vinted.fr/api/v2/wardrobe/29535217/items?page=1",
      "method": "GET"
    }
  ]
}
```

**Comportement** :
- Exécute les requêtes **une par une** dans l'ordre
- Si une requête échoue, **arrête la séquence**
- Utile pour des requêtes dépendantes

**Réponse** :
```javascript
{
  "success": true,
  "results": [
    {
      "success": true,
      "status": 200,
      "data": {...}
    },
    {
      "success": true,
      "status": 200,
      "data": {...}
    }
  ]
}
```

---

## 💻 Exemples d'Utilisation

### Exemple 1 : Récupérer les infos utilisateur

```javascript
// Depuis le backend
const request = {
  action: 'EXECUTE_HTTP_REQUEST',
  request: {
    url: 'https://www.vinted.fr/api/v2/users/current',
    method: 'GET',
    credentials: 'include'  // Cookies automatiques
  }
};

// Envoyer au plugin via WebSocket/HTTP
const response = await sendToPlugin(request);

console.log(response.data);
// {
//   "id": 29535217,
//   "login": "shop.ton.outfit",
//   "email": "user@example.com",
//   ...
// }
```

---

### Exemple 2 : Récupérer les produits avec pagination

```javascript
// Backend: récupérer toutes les pages de produits
async function fetchAllProducts(userId, csrfToken, anonId) {
  let allProducts = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const response = await sendToPlugin({
      action: 'EXECUTE_HTTP_REQUEST',
      request: {
        url: `https://www.vinted.fr/api/v2/wardrobe/${userId}/items?page=${page}&per_page=20`,
        method: 'GET',
        headers: {
          'X-CSRF-Token': csrfToken,
          'X-Anon-Id': anonId
        }
      }
    });

    if (!response.success) {
      throw new Error(`Erreur page ${page}: ${response.error}`);
    }

    allProducts = allProducts.concat(response.data.items);

    // Vérifier s'il y a d'autres pages
    hasMore = response.data.pagination.current_page < response.data.pagination.total_pages;
    page++;
  }

  return allProducts;
}
```

---

### Exemple 3 : Créer un nouveau produit (POST)

```javascript
const newProduct = {
  title: 'T-shirt Nike',
  description: 'Très bon état',
  price: '15.00',
  currency: 'EUR',
  brand_id: 53,
  size_id: 206,
  // ...
};

const response = await sendToPlugin({
  action: 'EXECUTE_HTTP_REQUEST',
  request: {
    url: 'https://www.vinted.fr/api/v2/items',
    method: 'POST',
    headers: {
      'X-CSRF-Token': csrfToken,
      'X-Anon-Id': anonId,
      'Content-Type': 'application/json'
    },
    body: newProduct  // Automatiquement converti en JSON
  }
});

if (response.success) {
  console.log('Produit créé:', response.data.item.id);
}
```

---

### Exemple 4 : Modifier un produit (PUT)

```javascript
const updates = {
  price: '12.00',
  description: 'Prix réduit !'
};

const response = await sendToPlugin({
  action: 'EXECUTE_HTTP_REQUEST',
  request: {
    url: `https://www.vinted.fr/api/v2/items/${itemId}`,
    method: 'PUT',
    headers: {
      'X-CSRF-Token': csrfToken,
      'X-Anon-Id': anonId
    },
    body: updates
  }
});
```

---

### Exemple 5 : Supprimer un produit (DELETE)

```javascript
const response = await sendToPlugin({
  action: 'EXECUTE_HTTP_REQUEST',
  request: {
    url: `https://www.vinted.fr/api/v2/items/${itemId}`,
    method: 'DELETE',
    headers: {
      'X-CSRF-Token': csrfToken,
      'X-Anon-Id': anonId
    }
  }
});

if (response.success && response.status === 204) {
  console.log('Produit supprimé');
}
```

---

### Exemple 6 : Requêtes en batch (parallèle)

```javascript
// Récupérer plusieurs pages en même temps
const responses = await sendToPlugin({
  action: 'EXECUTE_BATCH_REQUESTS',
  requests: [
    {
      url: 'https://www.vinted.fr/api/v2/wardrobe/29535217/items?page=1',
      method: 'GET',
      headers: { 'X-CSRF-Token': csrfToken, 'X-Anon-Id': anonId }
    },
    {
      url: 'https://www.vinted.fr/api/v2/wardrobe/29535217/items?page=2',
      method: 'GET',
      headers: { 'X-CSRF-Token': csrfToken, 'X-Anon-Id': anonId }
    },
    {
      url: 'https://www.vinted.fr/api/v2/wardrobe/29535217/items?page=3',
      method: 'GET',
      headers: { 'X-CSRF-Token': csrfToken, 'X-Anon-Id': anonId }
    }
  ]
});

// Combiner tous les résultats
const allItems = responses.results
  .filter(r => r.success)
  .flatMap(r => r.data.items);

console.log(`Total: ${allItems.length} produits`);
```

---

## 🔐 Sécurité

### Headers CSRF et Anon-ID

**Important** : Pour la plupart des requêtes POST/PUT/DELETE, Vinted requiert :

```javascript
headers: {
  'X-CSRF-Token': 'uuid',  // Obtenu via GET_USER_DATA
  'X-Anon-Id': 'uuid'      // Obtenu via GET_USER_DATA
}
```

**Comment obtenir ces tokens** :

```javascript
// 1. D'abord récupérer les données utilisateur
const userData = await sendToPlugin({
  action: 'GET_USER_DATA'
});

// 2. Utiliser les tokens pour les requêtes suivantes
const csrfToken = userData.csrf_token;
const anonId = userData.anon_id;
```

---

### Validation des Réponses

**Toujours vérifier** :

```javascript
const response = await sendToPlugin({...});

if (!response.success) {
  // Gérer l'erreur
  console.error('Erreur:', response.status, response.error);

  switch (response.status) {
    case 401:
      // Utilisateur non connecté
      console.log('Veuillez vous connecter à Vinted');
      break;

    case 403:
      // CSRF token invalide ou expiré
      console.log('Token expiré, récupérer un nouveau');
      break;

    case 404:
      // Ressource non trouvée
      console.log('Produit non trouvé');
      break;

    case 429:
      // Rate limit
      console.log('Trop de requêtes, attendre');
      break;

    default:
      console.log('Erreur inconnue');
  }

  return;
}

// Traiter les données
console.log(response.data);
```

---

## 📊 Gestion des Erreurs

### Types d'erreurs

| Erreur | Cause | Solution |
|--------|-------|----------|
| `success: false, status: 0` | Erreur réseau / Timeout | Réessayer après délai |
| `status: 401` | Non authentifié | Demander connexion Vinted |
| `status: 403` | Token CSRF invalide | Récupérer nouveau token |
| `status: 404` | Ressource non trouvée | Vérifier URL/ID |
| `status: 429` | Rate limit | Attendre puis réessayer |
| `status: 500+` | Erreur serveur Vinted | Réessayer plus tard |

---

### Retry Logic (Exemple)

```javascript
async function fetchWithRetry(request, maxRetries = 3) {
  let attempt = 0;

  while (attempt < maxRetries) {
    const response = await sendToPlugin({
      action: 'EXECUTE_HTTP_REQUEST',
      request
    });

    if (response.success) {
      return response;
    }

    // Si erreur temporaire, réessayer
    if (response.status === 429 || response.status >= 500) {
      attempt++;
      const delay = Math.pow(2, attempt) * 1000; // Backoff exponentiel
      console.log(`Tentative ${attempt}/${maxRetries}, attente ${delay}ms`);
      await sleep(delay);
      continue;
    }

    // Si erreur permanente, arrêter
    throw new Error(`Erreur ${response.status}: ${response.error}`);
  }

  throw new Error('Max retries atteint');
}
```

---

## ⚡ Performance

### Throttling

Vinted limite les requêtes :
- **Maximum** : ~10 requêtes/seconde
- **Recommandé** : 1 requête toutes les 100ms

**Exemple avec throttling** :

```javascript
async function fetchWithThrottle(requests) {
  const results = [];
  const delay = 100; // ms

  for (const request of requests) {
    const response = await sendToPlugin({
      action: 'EXECUTE_HTTP_REQUEST',
      request
    });

    results.push(response);

    // Attendre avant la prochaine requête
    await sleep(delay);
  }

  return results;
}
```

---

### Batch vs Séquentiel

**Utiliser BATCH** quand :
- Les requêtes sont **indépendantes**
- Vous voulez la **vitesse maximale**
- Exemple : Récupérer plusieurs pages de produits

**Utiliser SEQUENTIAL** quand :
- Une requête **dépend** de la précédente
- Vous voulez **respecter l'ordre**
- Exemple : Créer produit → Upload photo → Publier

---

## 🎯 Use Cases Complets

### Use Case 1 : Synchronisation complète

```javascript
async function syncVintedToStoflow(userId) {
  // 1. Récupérer les données utilisateur
  const userData = await sendToPlugin({ action: 'GET_USER_DATA' });

  const { csrf_token, anon_id } = userData;

  // 2. Récupérer tous les produits
  const allProducts = await fetchAllProducts(userId, csrf_token, anon_id);

  // 3. Envoyer à StoFlow backend
  await saveToStoflow({
    user: userData,
    products: allProducts
  });

  console.log(`✅ ${allProducts.length} produits synchronisés`);
}
```

---

### Use Case 2 : Mise à jour des prix

```javascript
async function updateAllPrices(priceUpdates) {
  const userData = await sendToPlugin({ action: 'GET_USER_DATA' });

  const requests = priceUpdates.map(update => ({
    url: `https://www.vinted.fr/api/v2/items/${update.itemId}`,
    method: 'PUT',
    headers: {
      'X-CSRF-Token': userData.csrf_token,
      'X-Anon-Id': userData.anon_id
    },
    body: {
      price: update.newPrice
    }
  }));

  // Exécuter en séquence avec throttling
  const response = await sendToPlugin({
    action: 'EXECUTE_SEQUENTIAL_REQUESTS',
    requests
  });

  const successful = response.results.filter(r => r.success).length;
  console.log(`✅ ${successful}/${requests.length} prix mis à jour`);
}
```

---

## 📝 Checklist d'Implémentation Backend

- [ ] Implémenter la communication WebSocket/HTTP avec le plugin
- [ ] Gérer les messages `EXECUTE_HTTP_REQUEST`
- [ ] Gérer les messages `EXECUTE_BATCH_REQUESTS`
- [ ] Gérer les messages `EXECUTE_SEQUENTIAL_REQUESTS`
- [ ] Implémenter la récupération des tokens (GET_USER_DATA)
- [ ] Ajouter retry logic pour erreurs temporaires
- [ ] Ajouter throttling pour respecter les limites Vinted
- [ ] Logger toutes les requêtes/réponses
- [ ] Gérer les timeouts
- [ ] Afficher les erreurs côté utilisateur

---

## 🚀 Prochaines Étapes

Maintenant que le proxy est en place, le backend peut :

1. ✅ Faire **n'importe quelle requête** à l'API Vinted
2. ✅ Ajouter de nouvelles fonctionnalités **sans modifier le plugin**
3. ✅ Tester rapidement de nouveaux endpoints
4. ✅ Créer des workflows complexes (batch, séquence)

**Le plugin n'a plus besoin d'être mis à jour** sauf pour :
- Corrections de bugs
- Optimisations de performance
- Nouvelles plateformes (eBay, Etsy, etc.)

---

**Version** : 2.0.0 (Proxy Générique)
**Dernière mise à jour** : 2024-12-07

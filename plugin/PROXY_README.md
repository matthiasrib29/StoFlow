# 🌐 Proxy HTTP Générique - Guide Rapide

## 🎯 Qu'est-ce que c'est ?

Le plugin StoFlow inclut maintenant un **proxy HTTP générique** qui permet d'exécuter **n'importe quelle requête HTTP** depuis le backend en utilisant le navigateur de l'utilisateur.

### Avant (Version 1.0)
```
Backend → Plugin → Code spécifique Vinted → API Vinted
```
❌ Besoin de modifier le plugin pour chaque nouvelle fonctionnalité

### Maintenant (Version 2.0)
```
Backend → Plugin (Proxy) → N'importe quelle API
```
✅ Le plugin est **générique**, le backend contrôle tout

---

## 🚀 Utilisation Simple

### Frontend (Extension)

```typescript
import { useHttpProxy } from '@/composables/useHttpProxy';

const { get, post, put, delete: del } = useHttpProxy();

// GET request
const response = await get('https://www.vinted.fr/api/v2/users/current');

// POST request
const newProduct = await post(
  'https://www.vinted.fr/api/v2/items',
  { title: 'T-shirt', price: '15.00' },
  { 'X-CSRF-Token': csrfToken }
);

// PUT request
const updated = await put(
  `https://www.vinted.fr/api/v2/items/${itemId}`,
  { price: '12.00' },
  { 'X-CSRF-Token': csrfToken }
);

// DELETE request
await del(
  `https://www.vinted.fr/api/v2/items/${itemId}`,
  { 'X-CSRF-Token': csrfToken }
);
```

---

### Backend (Node.js / Python / etc.)

```javascript
// Envoyer une requête au plugin via WebSocket
const response = await sendToPlugin({
  action: 'EXECUTE_HTTP_REQUEST',
  request: {
    url: 'https://www.vinted.fr/api/v2/users/current',
    method: 'GET',
    headers: {
      'X-CSRF-Token': csrfToken,
      'X-Anon-Id': anonId
    }
  }
});

if (response.success) {
  console.log('Données:', response.data);
}
```

---

## 📦 Fonctionnalités

### 1. Requête Unique
```javascript
const response = await executeRequest({
  url: 'https://www.vinted.fr/api/v2/items',
  method: 'POST',
  headers: { 'X-CSRF-Token': '...' },
  body: { title: 'Produit' }
});
```

### 2. Requêtes en Parallèle (Batch)
```javascript
const responses = await executeBatch([
  { url: 'https://...?page=1', method: 'GET' },
  { url: 'https://...?page=2', method: 'GET' },
  { url: 'https://...?page=3', method: 'GET' }
]);
```

### 3. Requêtes en Séquence
```javascript
const responses = await executeSequential([
  { url: 'https://.../create', method: 'POST', body: {...} },
  { url: 'https://.../upload', method: 'POST', body: {...} },
  { url: 'https://.../publish', method: 'POST' }
]);
```

---

## 🔥 Exemples Concrets

### Récupérer tous les produits

```javascript
async function getAllProducts(userId, csrfToken, anonId) {
  let allProducts = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const response = await executeRequest({
      url: `https://www.vinted.fr/api/v2/wardrobe/${userId}/items?page=${page}`,
      method: 'GET',
      headers: {
        'X-CSRF-Token': csrfToken,
        'X-Anon-Id': anonId
      }
    });

    allProducts.push(...response.data.items);
    hasMore = page < response.data.pagination.total_pages;
    page++;
  }

  return allProducts;
}
```

### Modifier plusieurs prix en masse

```javascript
async function updatePrices(items, newPrice) {
  const requests = items.map(item => ({
    url: `https://www.vinted.fr/api/v2/items/${item.id}`,
    method: 'PUT',
    headers: { 'X-CSRF-Token': csrfToken },
    body: { price: newPrice }
  }));

  const results = await executeBatch(requests);

  const success = results.filter(r => r.success).length;
  console.log(`✅ ${success}/${items.length} prix modifiés`);
}
```

---

## 🔐 Sécurité

### Tokens CSRF et Anon-ID

Pour modifier des données, Vinted requiert :

```javascript
headers: {
  'X-CSRF-Token': 'uuid',  // Token CSRF
  'X-Anon-Id': 'uuid'      // ID anonyme
}
```

**Obtenir ces tokens** :

```javascript
// 1. Extraire les données utilisateur
const userData = await sendToPlugin({ action: 'GET_USER_DATA' });

// 2. Utiliser les tokens
const csrfToken = userData.csrf_token;
const anonId = userData.anon_id;
```

---

## ⚡ Performance

### Rate Limiting

Vinted limite à **~10 requêtes/seconde**.

**Recommandation** : 1 requête toutes les 100ms

```javascript
for (const request of requests) {
  await executeRequest(request);
  await sleep(100); // Throttling
}
```

### Batch vs Séquentiel

| Type | Quand l'utiliser | Vitesse |
|------|------------------|---------|
| **Batch** | Requêtes indépendantes | ⚡ Rapide (parallèle) |
| **Séquentiel** | Requêtes dépendantes | 🐢 Lent (une par une) |

---

## 📚 Documentation Complète

- **[API_PROXY.md](./API_PROXY.md)** - Documentation complète de l'API
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Architecture technique
- **[BUSINESS_LOGIC.md](./BUSINESS_LOGIC.md)** - Logique métier

---

## ✅ Checklist Backend

- [ ] Implémenter communication avec le plugin
- [ ] Gérer `EXECUTE_HTTP_REQUEST`
- [ ] Gérer `EXECUTE_BATCH_REQUESTS`
- [ ] Gérer `EXECUTE_SEQUENTIAL_REQUESTS`
- [ ] Récupérer les tokens CSRF/Anon-ID
- [ ] Ajouter retry logic
- [ ] Ajouter throttling
- [ ] Logger les requêtes/erreurs

---

## 🎉 Avantages

✅ **Flexibilité totale** - Toutes les requêtes possibles
✅ **Pas de mise à jour** - Le plugin reste fixe
✅ **Cookies automatiques** - Pas de gestion manuelle
✅ **Pas de CORS** - Requêtes depuis vinted.fr
✅ **Simple** - Interface claire et documentée

---

**Version** : 2.0.0
**Dernière mise à jour** : 2024-12-07

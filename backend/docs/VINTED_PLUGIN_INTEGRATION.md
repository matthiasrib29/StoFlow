# Intégration Vinted - Communication Backend ↔ Plugin

## 🎯 Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌──────────────┐
│                 │         │                  │         │              │
│  Stoflow Web    │────────▶│  Backend API     │────────▶│   Database   │
│  (Frontend)     │         │  (FastAPI)       │         │  PostgreSQL  │
│                 │         │                  │         │              │
└─────────────────┘         └──────────────────┘         └──────────────┘
                                     │
                                     │ PluginTask
                                     │ (VINTED_PUBLISH)
                                     │
                                     ▼
                            ┌──────────────────┐
                            │                  │
                            │  Plugin Browser  │
                            │  (Chrome/Firefox)│
                            │                  │
                            └──────────────────┘
                                     │
                                     │ Exécute requête
                                     │ avec cookies
                                     ▼
                            ┌──────────────────┐
                            │                  │
                            │   Vinted API     │
                            │  (vinted.fr)     │
                            │                  │
                            └──────────────────┘
```

## 📋 Flux de Publication Complet

### 1. Utilisateur demande publication (Frontend)

```javascript
// Frontend: POST /api/vinted/publish
const response = await fetch('http://localhost:8000/api/vinted/publish', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    product_id: 123
  })
});

// Réponse:
// {
//   "product_id": 123,
//   "status": "pending",
//   "message": "Demande de publication créée (task #456), en attente du plugin",
//   "vinted_product_id": 789
// }
```

**Backend crée automatiquement** :
- ✅ `VintedProduct` (status='pending', title, price générés)
- ✅ `PluginTask` (type='vinted_publish', payload avec données préparées)

---

### 2. Plugin récupère les tâches (Polling toutes les 5s)

```javascript
// Plugin: GET /api/plugin/tasks
const response = await fetch('http://localhost:8000/api/plugin/tasks?limit=10', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

// Réponse: Liste des tâches pending
// [
//   {
//     "id": 456,
//     "task_type": "vinted_publish",
//     "payload": {
//       "product_id": 123,
//       "vinted_product_id": 789,
//       "title": "Levi's 501 Jean Regular Taille 32 Très bon état Bleu Vintage 90s (A3) [123]",
//       "description": "✨ Découvrez ce magnifique jean Levi's 501 vintage des années 90s !...",
//       "price": 27.90,
//       "mapped_attributes": {
//         "brand_id": 53,
//         "color_id": 12,
//         "condition_id": 1,
//         "size_id": 207
//       },
//       "product_data": {
//         "brand": "Levi's",
//         "category": "Jeans",
//         "size": "32",
//         "color": "Blue",
//         "condition": "EXCELLENT",
//         "images": "image1.jpg,image2.jpg,image3.jpg"
//       }
//     },
//     "created_at": "2024-12-10T10:30:00Z"
//   }
// ]
```

---

### 3. Plugin exécute la publication sur Vinted

```javascript
// Plugin: Exécuter la tâche
async function executeVintedPublish(task) {
  try {
    const { payload } = task;

    // 1. Uploader les images vers Vinted
    const imageIds = await uploadImagesToVinted(payload.product_data.images);

    // 2. Créer le listing Vinted
    const vintedResponse = await fetch('https://vinted.fr/api/v2/items', {
      method: 'POST',
      headers: {
        'Cookie': getCookiesFromStorage(),  // Cookies utilisateur
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: payload.title,
        description: payload.description,
        price: payload.price,
        brand_id: payload.mapped_attributes.brand_id,
        color_ids: [payload.mapped_attributes.color_id],
        size_id: payload.mapped_attributes.size_id,
        status_id: payload.mapped_attributes.condition_id,
        photo_ids: imageIds
        // ... autres champs Vinted
      })
    });

    const data = await vintedResponse.json();

    // 3. Retourner le résultat au backend
    await submitTaskResult(task.id, {
      success: true,
      result: {
        vinted_id: data.item.id,
        url: data.item.url,
        image_ids: imageIds.join(',')
      }
    });

  } catch (error) {
    // En cas d'erreur
    await submitTaskResult(task.id, {
      success: false,
      error_message: error.message,
      error_details: {
        error_type: 'api_error',
        error_details: error.stack
      }
    });
  }
}
```

---

### 4. Plugin retourne le résultat au Backend

```javascript
// Plugin: POST /api/plugin/tasks/{task_id}/result
async function submitTaskResult(taskId, result) {
  const response = await fetch(`http://localhost:8000/api/plugin/tasks/${taskId}/result`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(result)
  });

  return await response.json();
}

// Exemple résultat SUCCESS:
// {
//   "success": true,
//   "result": {
//     "vinted_id": 987654321,
//     "url": "https://vinted.fr/items/987654321",
//     "image_ids": "123,456,789"
//   }
// }

// Exemple résultat FAILED:
// {
//   "success": false,
//   "error_message": "Brand not found on Vinted",
//   "error_details": {
//     "error_type": "mapping_error",
//     "error_details": "Brand 'UnknownBrand' n'existe pas dans l'API Vinted"
//   }
// }
```

**Backend traite automatiquement le résultat** :
- ✅ `VintedTaskHandler.handle_task_result()` déclenché
- ✅ `VintedProduct` mis à jour (status='published', vinted_id, url, image_ids)
- ✅ En cas d'erreur: `VintedErrorLog` créé, `VintedProduct.status='error'`

---

## 🔄 Gestion des Erreurs et Retry

### Retry automatique

```
Tentative 1: FAILED → retry_count = 1, status = PENDING (retry)
Tentative 2: FAILED → retry_count = 2, status = PENDING (retry)
Tentative 3: FAILED → retry_count = 3, status = FAILED (abandon)
```

### Timeout automatique

- Tâches non exécutées après **1 heure** → `status = TIMEOUT`
- Cleanup automatique lors du prochain poll

---

## 📦 Format du Payload (VINTED_PUBLISH)

```json
{
  "product_id": 123,
  "vinted_product_id": 789,
  "title": "Levi's 501 Jean Regular Taille 32 Très bon état Bleu Vintage 90s (A3) [123]",
  "description": "✨ Découvrez ce magnifique jean Levi's 501 vintage des années 90s !\n\n📋 Informations:\n• Marque: Levi's\n• Modèle: 501\n...",
  "price": 27.90,
  "mapped_attributes": {
    "brand_id": 53,
    "color_id": 12,
    "condition_id": 1,
    "size_id": 207,
    "category_id": null,
    "gender": "male",
    "is_bottom": true
  },
  "product_data": {
    "brand": "Levi's",
    "category": "Jeans",
    "size": "32",
    "color": "Blue",
    "condition": "EXCELLENT",
    "images": "image1.jpg,image2.jpg,image3.jpg"
  }
}
```

---

## 🔑 Endpoints API disponibles

### Backend → Plugin

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/plugin/tasks` | Récupère les tâches pending (poll toutes les 5s) |
| `POST` | `/api/plugin/tasks/{id}/result` | Soumet le résultat d'une tâche |
| `GET` | `/api/plugin/health` | Health check |
| `GET` | `/api/plugin/platforms` | Liste des plateformes supportées |
| `POST` | `/api/plugin/sync` | Sync cookies et test connexion |

### Frontend → Backend

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/vinted/publish` | Demander publication d'un produit |
| `POST` | `/api/vinted/publish/batch` | Publier plusieurs produits |
| `POST` | `/api/vinted/prepare/{id}` | Préparer/valider produit (preview) |
| `GET` | `/api/vinted/products` | Lister produits Vinted |
| `GET` | `/api/vinted/products/{id}` | Détails produit Vinted |
| `PATCH` | `/api/vinted/products/{id}/analytics` | Mettre à jour analytics (views, favourites) |
| `DELETE` | `/api/vinted/products/{id}` | Soft delete |
| `GET` | `/api/vinted/analytics/summary` | Résumé analytics global |
| `GET` | `/api/vinted/errors` | Liste erreurs |
| `GET` | `/api/vinted/errors/summary` | Résumé erreurs |

---

## 🛠️ Implémentation côté Plugin

### Structure recommandée

```
src/
├── background/
│   ├── taskPoller.ts         # Poll /api/plugin/tasks toutes les 5s
│   ├── taskExecutor.ts       # Exécute les tâches selon type
│   └── taskResultSubmitter.ts # Soumet résultats au backend
├── content/
│   └── vinted/
│       ├── vintedPublisher.ts    # Logique publication Vinted
│       ├── vintedImageUploader.ts # Upload images
│       └── vintedApiClient.ts    # Wrapper API Vinted
└── types/
    └── tasks.ts              # Types TypeScript pour tasks
```

### Exemple d'implémentation (taskPoller.ts)

```typescript
// Polling toutes les 5s
setInterval(async () => {
  try {
    const tasks = await fetchPendingTasks();

    for (const task of tasks) {
      // Exécuter selon le type
      if (task.task_type === 'vinted_publish') {
        await executeVintedPublish(task);
      } else if (task.task_type === 'vinted_update') {
        await executeVintedUpdate(task);
      } else if (task.task_type === 'vinted_delete') {
        await executeVintedDelete(task);
      }
    }
  } catch (error) {
    console.error('Error polling tasks:', error);
  }
}, 5000); // 5 secondes
```

---

## ✅ Checklist d'implémentation Plugin

- [ ] **Authentification**
  - [ ] Récupérer access_token depuis SSO (localStorage)
  - [ ] Inclure Bearer token dans toutes les requêtes

- [ ] **Polling des tâches**
  - [ ] Implémenter polling GET /api/plugin/tasks (5s interval)
  - [ ] Parser les tâches VINTED_PUBLISH

- [ ] **Publication Vinted**
  - [ ] Upload images vers Vinted (/api/v2/photos)
  - [ ] Créer listing (/api/v2/items)
  - [ ] Mapper les IDs fournis par le backend

- [ ] **Soumission résultats**
  - [ ] Retourner vinted_id, url, image_ids en cas de succès
  - [ ] Retourner error_type, error_message en cas d'échec
  - [ ] POST /api/plugin/tasks/{id}/result

- [ ] **Gestion erreurs**
  - [ ] Capturer erreurs API Vinted
  - [ ] Typer les erreurs (mapping_error, api_error, image_error)
  - [ ] Retry automatique géré côté backend

---

## 📊 Monitoring et Debug

### Logs Backend

```bash
# Voir les tâches en cours
SELECT * FROM user_1.plugin_tasks WHERE status = 'pending';

# Voir les erreurs Vinted
SELECT * FROM user_1.vinted_error_logs ORDER BY created_at DESC LIMIT 10;

# Voir les produits publiés
SELECT * FROM user_1.vinted_products WHERE status = 'published';
```

### Endpoints de monitoring

```bash
# Résumé analytics
GET /api/vinted/analytics/summary

# Résumé erreurs
GET /api/vinted/errors/summary
```

---

## 🚀 Exemple complet de Test

```bash
# 1. Créer un produit
POST /api/products
{
  "title": "Jean Levi's 501",
  "brand": "Levi's",
  "category": "Jeans",
  "condition": "EXCELLENT",
  "price": 25.00,
  "size": "32",
  "color": "Blue",
  "stock_quantity": 1
}
# → product_id = 123

# 2. Demander publication Vinted
POST /api/vinted/publish
{
  "product_id": 123
}
# → Crée PluginTask #456

# 3. Plugin récupère la tâche
GET /api/plugin/tasks
# → Retourne task #456 avec payload

# 4. Plugin exécute et retourne résultat
POST /api/plugin/tasks/456/result
{
  "success": true,
  "result": {
    "vinted_id": 987654321,
    "url": "https://vinted.fr/items/987654321",
    "image_ids": "123,456"
  }
}

# 5. Vérifier le résultat
GET /api/vinted/products
# → VintedProduct status='published', vinted_id=987654321
```

---

## 📝 Notes importantes

- ✅ **Pas de stockage de cookies côté backend** - Restent uniquement dans le navigateur
- ✅ **Retry automatique** - Max 3 tentatives, timeout 1h
- ✅ **Multi-tenant** - Chaque utilisateur a ses propres tâches (schema user_{id})
- ✅ **Logs d'erreurs** - Toutes les erreurs sont tracées dans vinted_error_logs
- ✅ **Analytics** - Views, favourites, conversations synchronisables via PATCH endpoint

---

Pour toute question, consulter :
- API Docs : http://localhost:8000/docs
- Services : `/services/vinted/`
- Repositories : `/repositories/`

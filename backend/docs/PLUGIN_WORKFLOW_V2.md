# Plugin Workflow V2 - Architecture Step-by-Step

**Date:** 2025-12-10
**Version:** 2.0
**Status:** ✅ Implémenté

## 🎯 Vue d'Ensemble

Le nouveau système utilise une **génération dynamique step-by-step** des tasks pour publication sur les plateformes (Vinted, eBay, Etsy).

### Principe Clé

- **PluginQueue** : Blueprint de l'opération complète (ex: "publish product 123")
- **PluginTask** : Task courante générée dynamiquement step by step
- **Génération à la volée** : Le backend génère chaque step après le précédent
- **Une task à la fois par plateforme** : FIFO strict

---

## 📊 Architecture

```
┌──────────────┐
│   Frontend   │
│ POST /publish│
└──────┬───────┘
       │ Crée PluginQueue
       ▼
┌──────────────────────┐
│   PluginQueue        │
│  - platform: vinted  │
│  - operation: publish│
│  - status: processing│
│  - accumulated_data  │
└──────┬───────────────┘
       │ Génère Task 1
       ▼
┌──────────────────────┐      ┌─────────────┐
│   PluginTask #1      │◄─────│   Plugin    │
│  POST /api/v2/photos │      │  (Poll 5s)  │
│  payload: {image1}   │──────►             │
└──────┬───────────────┘      └─────────────┘
       │ Result: photo_id=123
       │ Accumule dans queue
       │ Génère Task 2
       ▼
┌──────────────────────┐
│   PluginTask #2      │
│  POST /api/v2/photos │
│  payload: {image2}   │
└──────┬───────────────┘
       │ Result: photo_id=456
       │ Génère Task 3
       ▼
┌──────────────────────┐
│   PluginTask #3      │
│  POST /api/v2/items  │
│  payload: {          │
│    photo_ids: [123,456]
│    title, price...   │
│  }                   │
└──────┬───────────────┘
       │ Result: vinted_id, url
       │ Queue COMPLETED
       ▼
   SUCCESS ✅
```

---

## 🗂️ Structure des Tables

### `plugin_queue`

```sql
CREATE TABLE plugin_queue (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,           -- 'vinted', 'ebay', 'etsy'
    operation VARCHAR(100) NOT NULL,         -- 'publish_product', 'update_listing'
    product_id INTEGER,
    status VARCHAR(20) DEFAULT 'queued',     -- 'queued', 'processing', 'completed', 'failed'
    current_step VARCHAR(100),               -- Pour monitoring (ex: 'upload_image_2')
    accumulated_data JSONB DEFAULT '{}',     -- Résultats accumulés
    context_data JSONB DEFAULT '{}',         -- Contexte additionnel
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Exemple `accumulated_data`** :
```json
{
  "photo_ids": [123, 456, 789],
  "vinted_id": 987654321,
  "url": "https://vinted.fr/items/987654321",
  "listing_created": true
}
```

### `plugin_tasks`

```sql
-- Nouvelles colonnes ajoutées
queue_id INTEGER,              -- FK vers plugin_queue
platform VARCHAR(50),          -- 'vinted'
http_method VARCHAR(10),       -- 'POST', 'PUT', 'DELETE'
path VARCHAR(500),             -- '/api/v2/photos', '/api/v2/items'
```

---

## 🔄 Workflow Complet

### **1. Frontend → POST /api/vinted/publish**

```json
POST /api/vinted/publish
{
  "product_id": 123
}
```

**Backend crée** :
1. `VintedProduct` (status='pending')
2. `PluginQueue` (platform='vinted', operation='publish_product')
3. **Première `PluginTask`** (upload_image_1)

**Réponse** :
```json
{
  "product_id": 123,
  "status": "pending",
  "message": "Demande de publication créée (queue #456, task #1001), en attente du plugin",
  "vinted_product_id": 789
}
```

---

### **2. Plugin → GET /api/plugin/tasks**

Plugin poll toutes les 5 secondes.

**Requête** :
```
GET /api/plugin/tasks?limit=10
```

**Réponse** :
```json
[
  {
    "id": 1001,
    "queue_id": 456,
    "platform": "vinted",
    "http_method": "POST",
    "path": "/api/v2/photos",
    "payload": {
      "photo": "https://stoflow.com/uploads/image1.jpg"
    },
    "created_at": "2025-12-10T14:00:00Z"
  }
]
```

**Important** :
- ✅ Une seule task par plateforme (FIFO)
- ✅ Payload déjà résolu (pas de placeholders)
- ✅ Plugin n'a besoin que de ces infos pour exécuter

---

### **3. Plugin Exécute**

```javascript
// Plugin code
const task = tasks[0];

// Construire la requête Vinted
const response = await fetch(`https://vinted.fr${task.path}`, {
  method: task.http_method,
  credentials: 'include', // Cookies browser
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(task.payload)
});

const data = await response.json();
// data = { photo: { id: 123 } }
```

---

### **4. Plugin → POST /api/plugin/tasks/{id}/result**

```json
POST /api/plugin/tasks/1001/result
{
  "success": true,
  "result": {
    "photo_id": 123
  }
}
```

**Backend automatiquement** :
1. Marque task #1001 comme SUCCESS
2. Accumule dans `queue.accumulated_data.photo_ids = [123]`
3. **Génère automatiquement task #1002** (upload_image_2)

**Réponse** :
```json
{
  "success": true,
  "task_id": 1001,
  "status": "success",
  "next_task_id": 1002,
  "queue_status": "processing",
  "message": "Task 1001 completed successfully"
}
```

---

### **5. Répétition Steps 2-4**

Le plugin continue de poll et reçoit task #1002, #1003...

Après toutes les images, il reçoit la task de création :

```json
{
  "id": 1004,
  "queue_id": 456,
  "platform": "vinted",
  "http_method": "POST",
  "path": "/api/v2/items",
  "payload": {
    "title": "Levi's 501 Jean...",
    "description": "✨ Découvrez...",
    "price_cents": 2790,
    "brand_id": 53,
    "size_id": 207,
    "status_id": 1,
    "color_ids": [12],
    "photo_ids": [123, 456, 789],  // ⬅️ Accumulés des steps précédents !
    "package_size_id": 1,
    "is_for_sell": true
  }
}
```

---

### **6. Plugin Soumet Résultat Final**

```json
POST /api/plugin/tasks/1004/result
{
  "success": true,
  "result": {
    "id": 987654321,
    "url": "https://vinted.fr/items/987654321"
  }
}
```

**Backend automatiquement** :
1. Accumule `vinted_id` et `url`
2. Tente de générer le step suivant → **AllStepsCompleted** exception
3. Marque `queue.status = 'completed'`
4. Marque `VintedProduct.status = 'published'`
5. Sauvegarde `vinted_id` et `url` dans `VintedProduct`

**Réponse** :
```json
{
  "success": true,
  "task_id": 1004,
  "status": "success",
  "next_task_id": null,
  "queue_status": "completed",
  "message": "Task 1004 completed successfully"
}
```

---

## 🔁 Gestion des Erreurs

### **Échec d'un Step**

Si le plugin retourne `success: false` :

```json
POST /api/plugin/tasks/1002/result
{
  "success": false,
  "error_message": "Network timeout"
}
```

**Backend** :
- Incrémente `task.retry_count`
- Si `retry_count < max_retries` (3) : status = PENDING (retry automatique)
- Si `retry_count >= 3` : status = FAILED, `queue.status = 'failed'`

**Plugin reçoit la même task au prochain poll** pour retry.

---

## ⚙️ Implémentation Côté Backend

### Service de Génération

**`services/vinted/vinted_publish_service.py`** :

```python
class VintedPublishService:
    def execute_next_step(self) -> PluginTask:
        """Détermine et génère le prochain step."""
        accumulated_data = self.queue.accumulated_data or {}
        photo_ids = accumulated_data.get('photo_ids', [])

        images = self.product.images.split(',')

        # Toutes les images uploadées ?
        if len(photo_ids) < len(images):
            return self.upload_next_image()
        elif not accumulated_data.get('listing_created'):
            return self.create_listing()
        else:
            raise AllStepsCompleted()

    def upload_next_image(self) -> PluginTask:
        """Génère task d'upload image."""
        task = PluginTask(
            queue_id=self.queue.id,
            platform='vinted',
            http_method='POST',
            path='/api/v2/photos',
            payload={'photo': next_image_url},
            status=TaskStatus.PENDING
        )
        return task

    def create_listing(self) -> PluginTask:
        """Génère task de création listing."""
        photo_ids = self.queue.accumulated_data['photo_ids']

        task = PluginTask(
            queue_id=self.queue.id,
            platform='vinted',
            http_method='POST',
            path='/api/v2/items',
            payload={
                'title': ...,
                'photo_ids': photo_ids,  # Résultats accumulés
                ...
            },
            status=TaskStatus.PENDING
        )
        return task
```

---

## 🚀 Implémentation Côté Plugin

### Structure Simplifiée

```typescript
// Plugin poll
setInterval(async () => {
  const tasks = await fetch('http://localhost:8000/api/plugin/tasks').then(r => r.json());

  for (const task of tasks) {
    // Exécuter la requête exactement comme spécifiée
    const result = await fetch(`https://vinted.fr${task.path}`, {
      method: task.http_method,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(task.payload)
    });

    const data = await result.json();

    // Retourner le résultat
    await fetch(`http://localhost:8000/api/plugin/tasks/${task.id}/result`, {
      method: 'POST',
      body: JSON.stringify({
        success: true,
        result: extractRelevantData(data)  // { photo_id } ou { id, url }
      })
    });
  }
}, 5000);
```

**Extraction des résultats** :

```typescript
function extractRelevantData(vintedResponse: any) {
  // Upload photo
  if (vintedResponse.photo) {
    return { photo_id: vintedResponse.photo.id };
  }

  // Create listing
  if (vintedResponse.item) {
    return {
      id: vintedResponse.item.id,
      url: vintedResponse.item.url
    };
  }

  return vintedResponse;
}
```

---

## ✅ Avantages de cette Architecture

✅ **Simplicité** : Queue générale + génération dynamique
✅ **Léger** : Pas besoin de stocker tous les steps à l'avance
✅ **Flexible** : Backend décide dynamiquement du prochain step
✅ **FIFO strict** : Une task par plateforme à la fois
✅ **Retry simple** : Step par step, pas besoin de tout refaire
✅ **État centralisé** : `accumulated_data` dans la queue
✅ **Plugin générique** : Juste exécute `http_method + path + payload`

---

## 📝 Migration Depuis V1

**V1 (Ancien)** :
- PluginTask avec payload complet stocké
- VintedTaskHandler gérait les résultats
- Pas de workflow multi-step

**V2 (Nouveau)** :
- PluginQueue + génération dynamique
- VintedPublishService génère les steps
- Workflow complet step-by-step

**Rétrocompatibilité** :
- `task_type` conservé mais DEPRECATED
- Ancien système (sans `queue_id`) continue de fonctionner
- Nouveau système filtre sur `queue_id IS NOT NULL`

---

## 🔍 Monitoring

### Vérifier l'état d'une queue

```sql
SELECT
  id, platform, operation, status, current_step,
  accumulated_data->>'photo_ids' as photo_ids,
  accumulated_data->>'vinted_id' as vinted_id
FROM plugin_queue
WHERE product_id = 123;
```

### Voir les tasks d'une queue

```sql
SELECT
  id, status, http_method, path,
  result->>'photo_id' as photo_id,
  created_at, completed_at
FROM plugin_tasks
WHERE queue_id = 456
ORDER BY created_at;
```

---

Pour plus d'infos :
- Code : `/services/vinted/vinted_publish_service.py`
- API : `/api/vinted.py` et `/api/plugin.py`
- Migration : `/migrations/versions/20251210_1400_add_plugin_queue_system.py`

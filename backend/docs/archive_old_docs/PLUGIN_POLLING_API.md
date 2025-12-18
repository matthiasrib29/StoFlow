# 🔄 API de Polling du Plugin StoFlow

Guide pour le backend : comment créer des tâches que le plugin exécutera.

---

## 🎯 Principe

Le plugin **interroge régulièrement** le backend (toutes les 5 secondes) pour savoir s'il y a des tâches à exécuter.

```
Plugin (toutes les 5s) → GET /api/plugin/tasks?user_id=42
                       ←  {"task_id": "abc123", "action": "get_all_products", ...}

Plugin exécute la tâche sur Vinted

Plugin → POST /api/plugin/tasks/abc123/result
       ←  {"success": true}
```

---

## 📡 Endpoints à Implémenter dans le Backend

### 1️⃣ **GET /api/plugin/tasks**

Retourne la prochaine tâche à exécuter pour un utilisateur.

**Requête** :
```http
GET /api/plugin/tasks?user_id=42
Authorization: Bearer <token>
```

**Réponse (si tâche disponible)** :
```json
{
  "task_id": "abc123",
  "action": "get_all_products",
  "params": {
    "user_id": 29535217
  },
  "priority": 1,
  "timeout": 60
}
```

**Réponse (si aucune tâche)** :
```json
{
  "task_id": null,
  "message": "No pending tasks"
}
```

---

### 2️⃣ **POST /api/plugin/tasks/{task_id}/result**

Reçoit le résultat d'une tâche exécutée.

**Requête** :
```http
POST /api/plugin/tasks/abc123/result
Content-Type: application/json
Authorization: Bearer <token>

{
  "success": true,
  "data": {
    "products": [...],
    "total": 1595
  },
  "execution_time_ms": 15000,
  "executed_at": "2024-12-07T10:00:15Z"
}
```

**Réponse** :
```json
{
  "status": "received",
  "message": "Task result saved successfully"
}
```

---

## 🎬 Actions Disponibles

### `get_user_data`

Extrait les données utilisateur depuis la page Vinted.

**Paramètres** : Aucun

**Résultat** :
```json
{
  "user_id": 29535217,
  "login": "shop.ton.outfit",
  "email": "user@example.com",
  "anon_id": "6f646e72-5010-4da3-8640-6c0cf62aa346",
  "csrf_token": "75f6c9fa-dc8e-4e52-a000-e09dd4084b3e",
  "real_name": "John Doe",
  "business_account": 23111
}
```

---

### `get_all_products`

Récupère tous les produits d'un utilisateur (pagination automatique).

**Paramètres** :
```json
{
  "user_id": 29535217
}
```

**Résultat** :
```json
{
  "products": [
    {
      "id": 123456,
      "title": "T-shirt Nike",
      "price": "15.00",
      "brand": {"title": "Nike"},
      "size_title": "M",
      ...
    },
    ...
  ],
  "total": 1595
}
```

---

### `create_product`

Crée un nouveau produit sur Vinted.

**Paramètres** :
```json
{
  "title": "T-shirt Nike Noir",
  "description": "T-shirt Nike en excellent état",
  "price": "15.00",
  "brand_id": 53,
  "size_id": 206,
  "catalog_id": 5,
  "color_ids": [1],
  "status_ids": [6]
}
```

**Résultat** :
```json
{
  "item": {
    "id": 789456,
    "title": "T-shirt Nike Noir",
    "price": "15.00",
    ...
  }
}
```

---

### `update_product`

Modifie un produit existant.

**Paramètres** :
```json
{
  "item_id": 123456,
  "price": "12.00",
  "description": "Prix réduit !"
}
```

**Résultat** :
```json
{
  "item": {
    "id": 123456,
    "price": "12.00",
    ...
  }
}
```

---

### `delete_product`

Supprime un produit.

**Paramètres** :
```json
{
  "item_id": 123456
}
```

**Résultat** :
```json
{
  "success": true
}
```

---

### `update_prices`

Modifie les prix de plusieurs produits en masse.

**Paramètres** :
```json
{
  "updates": [
    {"item_id": 123, "price": "10.00"},
    {"item_id": 456, "price": "15.00"},
    {"item_id": 789, "price": "20.00"}
  ]
}
```

**Résultat** :
```json
{
  "updated": 3,
  "failed": 0,
  "total": 3
}
```

---

### `get_stats`

Récupère les statistiques d'un produit.

**Paramètres** :
```json
{
  "item_id": 123456
}
```

**Résultat** :
```json
{
  "view_count": 125,
  "favourite_count": 8,
  "message_count": 3
}
```

---

### `upload_photo`

Upload une photo pour un produit.

**Paramètres** :
```json
{
  "item_id": 123456,
  "photo_url": "https://backend.com/photos/abc.jpg"
}
```

**Résultat** : *(À implémenter)*

---

## 💾 Modèle de Données Backend (Django/SQLAlchemy)

### Table `plugin_tasks`

```python
class PluginTask(Model):
    task_id = CharField(primary_key=True)  # UUID
    user_id = IntegerField()
    action = CharField(max_length=50)
    params = JSONField()
    status = CharField(max_length=20)  # pending, executing, completed, failed
    priority = IntegerField(default=1)
    timeout = IntegerField(default=60)

    created_at = DateTimeField(auto_now_add=True)
    started_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)

    result = JSONField(null=True)
    error = CharField(max_length=500, null=True)
    execution_time_ms = IntegerField(null=True)
```

---

## 📝 Exemple d'Implémentation FastAPI

### Créer une tâche

```python
from fastapi import APIRouter, Depends
from uuid import uuid4
from datetime import datetime

router = APIRouter()

@router.post("/tasks/create")
async def create_task(
    user_id: int,
    action: str,
    params: dict,
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle tâche pour le plugin
    """
    task = PluginTask(
        task_id=str(uuid4()),
        user_id=user_id,
        action=action,
        params=params,
        status="pending",
        created_at=datetime.utcnow()
    )

    db.add(task)
    db.commit()

    return {"task_id": task.task_id}
```

---

### Récupérer la prochaine tâche (GET /api/plugin/tasks)

```python
@router.get("/plugin/tasks")
async def get_next_task(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Retourne la prochaine tâche à exécuter
    Le plugin appelle cet endpoint toutes les 5 secondes
    """
    task = db.query(PluginTask)\
        .filter(
            PluginTask.user_id == user_id,
            PluginTask.status == "pending"
        )\
        .order_by(PluginTask.priority.desc(), PluginTask.created_at)\
        .first()

    if not task:
        return {
            "task_id": None,
            "message": "No pending tasks"
        }

    # Marquer comme en cours
    task.status = "executing"
    task.started_at = datetime.utcnow()
    db.commit()

    return {
        "task_id": task.task_id,
        "action": task.action,
        "params": task.params,
        "priority": task.priority,
        "timeout": task.timeout
    }
```

---

### Recevoir le résultat (POST /api/plugin/tasks/{task_id}/result)

```python
@router.post("/plugin/tasks/{task_id}/result")
async def save_task_result(
    task_id: str,
    result: dict,
    db: Session = Depends(get_db)
):
    """
    Reçoit le résultat d'une tâche exécutée par le plugin
    """
    task = db.query(PluginTask).filter(PluginTask.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "completed" if result["success"] else "failed"
    task.completed_at = datetime.utcnow()
    task.result = result.get("data")
    task.error = result.get("error")
    task.execution_time_ms = result.get("execution_time_ms")

    db.commit()

    # Traiter les données selon l'action
    if task.action == "get_all_products" and result["success"]:
        # Sauvegarder les produits en DB
        save_products_to_db(task.user_id, result["data"]["products"])

    return {
        "status": "received",
        "message": "Task result saved successfully"
    }
```

---

## 🎯 Cas d'Usage Complet

### Scénario : User clique "Synchroniser Vinted"

**1. Frontend envoie au backend**
```http
POST /api/sync/vinted
{
  "user_id": 42
}
```

**2. Backend crée une tâche**
```python
task_id = create_task(
    user_id=42,
    action="get_all_products",
    params={"user_id": 29535217}  # Vinted user_id
)

return {"message": "Sync started", "task_id": task_id}
```

**3. Plugin récupère la tâche (polling automatique)**
```http
GET /api/plugin/tasks?user_id=42

Response:
{
  "task_id": "abc123",
  "action": "get_all_products",
  "params": {"user_id": 29535217}
}
```

**4. Plugin exécute et renvoie**
```http
POST /api/plugin/tasks/abc123/result
{
  "success": true,
  "data": {
    "products": [...],
    "total": 1595
  },
  "execution_time_ms": 15000
}
```

**5. Backend stocke les produits**
```python
# Dans save_task_result()
if task.action == "get_all_products":
    for product in result["data"]["products"]:
        VintedProduct.objects.create(
            user_id=task.user_id,
            vinted_id=product["id"],
            title=product["title"],
            price=product["price"],
            ...
        )
```

**6. User voit les produits sur l'interface**

---

## ⚙️ Configuration du Plugin

Le plugin démarre automatiquement le polling au chargement.

**Paramètres modifiables** dans `src/background/task-poller.ts` :

```typescript
const BACKEND_URL = 'http://localhost:8000';  // URL du backend
const POLL_INTERVAL = 5000;  // 5 secondes
```

---

## 🐛 Debug

### Voir les logs du plugin

1. Ouvrir Firefox
2. `about:debugging` → This Firefox
3. Cliquer sur **Inspect** à côté de StoFlow Plugin
4. Onglet **Console**

Vous verrez :
```
[Task Poller] ✅ Démarrage polling (intervalle: 5000ms)
[Task Poller] ✅ Nouvelle tâche: get_all_products abc123
[Task Poller] 🚀 Exécution tâche abc123: get_all_products
[Task Poller] Total: 1595 produits, 80 pages
[Task Poller] Page 1/80: 20 produits
...
[Task Poller] ✅ Résultat envoyé pour abc123
```

---

### Problèmes courants

**❌ "Aucun onglet Vinted ouvert"**
- Ouvrir `https://www.vinted.fr` et se connecter

**❌ "User ID non disponible"**
- Le plugin n'a pas encore stocké l'user_id
- Appeler d'abord une action `get_user_data`

**❌ "CSRF token expired"**
- Recharger la page Vinted (F5)
- Le plugin extraira un nouveau token automatiquement

---

## ✅ Checklist Backend

- [ ] Créer table `plugin_tasks` en DB
- [ ] Implémenter `GET /api/plugin/tasks`
- [ ] Implémenter `POST /api/plugin/tasks/{id}/result`
- [ ] Créer fonction pour créer des tâches
- [ ] Gérer les résultats selon l'action
- [ ] Ajouter logs pour debug
- [ ] Tester avec le plugin chargé dans Firefox

---

**Version** : 1.0.0
**Dernière mise à jour** : 2024-12-07

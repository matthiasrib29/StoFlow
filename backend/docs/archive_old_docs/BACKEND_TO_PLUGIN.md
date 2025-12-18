# 🔌 Backend → Plugin Communication

Guide complet pour exécuter des requêtes Vinted depuis le backend Python via le plugin Firefox.

---

## 🎯 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  BACKEND PYTHON (FastAPI/Django)                            │
│  ├─ vinted_proxy_client.py                                  │
│  └─ Appelle: client.get_all_products(user_id, ...)         │
│                                                             │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP POST
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  API BRIDGE SERVER (FastAPI)                                │
│  ├─ api_bridge_server.py                                    │
│  ├─ Port: 8000                                              │
│  └─ Endpoint: POST /api/plugin/execute                      │
│                                                             │
└─────────────────┬───────────────────────────────────────────┘
                  │ Transmet à
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  PAGE WEB (api-bridge.html)                                 │
│  ├─ Ouverte dans Firefox                                    │
│  ├─ URL: http://localhost:8000                              │
│  └─ Communique avec le plugin via Chrome Extension API      │
│                                                             │
└─────────────────┬───────────────────────────────────────────┘
                  │ chrome.runtime.sendMessage()
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  PLUGIN FIREFOX (Content Script)                            │
│  ├─ src/content/vinted.ts                                   │
│  ├─ src/content/proxy.ts                                    │
│  └─ Injecté sur vinted.fr                                   │
│                                                             │
└─────────────────┬───────────────────────────────────────────┘
                  │ fetch() avec credentials: 'include'
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  VINTED API                                                 │
│  ├─ Reçoit la requête avec les cookies de l'utilisateur     │
│  └─ Retourne les données                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Installation et Setup

### 1. Prérequis

```bash
# Backend
pip install fastapi uvicorn requests

# Plugin Firefox déjà installé et chargé
```

### 2. Lancer le serveur API Bridge

```bash
cd Stoflow_BackEnd/scripts
python api_bridge_server.py
```

Vous devriez voir :
```
🚀 StoFlow API Bridge Server
📡 Endpoints:
  - http://localhost:8000/
  - http://localhost:8000/api/plugin/execute
  - http://localhost:8000/api/health
```

### 3. Ouvrir la page Bridge dans Firefox

1. Ouvrir Firefox
2. Aller sur `http://localhost:8000`
3. Vérifier que le status affiche : **✅ Plugin StoFlow connecté et prêt**

### 4. Ouvrir Vinted

1. Ouvrir un nouvel onglet
2. Aller sur `https://www.vinted.fr`
3. Se connecter avec votre compte

✅ **Tout est prêt !**

---

## 💻 Utilisation depuis le Backend

### Exemple Simple

```python
from vinted_proxy_client import VintedProxyClient

# 1. Créer le client
client = VintedProxyClient(frontend_url="http://localhost:8000")

# 2. Récupérer les données utilisateur
user_data = client.get_user_data()

print(f"User ID: {user_data['user_id']}")
print(f"Login: {user_data['login']}")
print(f"Email: {user_data['email']}")

# 3. Récupérer tous les produits
products = client.get_all_products(
    user_id=user_data['user_id'],
    csrf_token=user_data['csrf_token'],
    anon_id=user_data['anon_id']
)

print(f"Total: {len(products)} produits")
```

---

## 📚 API du Client Python

### `VintedProxyClient`

#### **`get_user_data()`**

Récupère les données utilisateur depuis la page Vinted.

```python
user_data = client.get_user_data()

# Retourne:
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

#### **`get_all_products(user_id, csrf_token, anon_id, throttle=0.1)`**

Récupère TOUS les produits avec pagination automatique.

```python
products = client.get_all_products(
    user_id=user_data['user_id'],
    csrf_token=user_data['csrf_token'],
    anon_id=user_data['anon_id'],
    throttle=0.1  # 100ms entre chaque requête
)

# Retourne: Liste de produits
[
    {
        "id": 123456,
        "title": "T-shirt Nike",
        "price": "15.00",
        "brand": "Nike",
        "size": "M",
        ...
    },
    ...
]
```

---

#### **`create_product(...)`**

Crée un nouveau produit sur Vinted.

```python
result = client.create_product(
    csrf_token=user_data['csrf_token'],
    anon_id=user_data['anon_id'],
    title="T-shirt Nike Noir",
    description="T-shirt Nike en excellent état",
    price="15.00",
    brand_id=53,  # Nike
    size_id=206,  # M
    catalog_id=5,  # Vêtements homme
    color_ids=[1],  # Noir
    status_ids=[6]  # Très bon état
)

if result["success"]:
    item_id = result["data"]["item"]["id"]
    print(f"✅ Produit créé: {item_id}")
```

---

#### **`update_product(item_id, csrf_token, anon_id, **updates)`**

Modifie un produit existant.

```python
result = client.update_product(
    item_id=123456,
    csrf_token=user_data['csrf_token'],
    anon_id=user_data['anon_id'],
    price="12.00",
    description="Prix réduit !"
)

if result["success"]:
    print("✅ Produit modifié")
```

---

#### **`delete_product(item_id, csrf_token, anon_id)`**

Supprime un produit.

```python
result = client.delete_product(
    item_id=123456,
    csrf_token=user_data['csrf_token'],
    anon_id=user_data['anon_id']
)

if result["success"] and result["status"] == 204:
    print("✅ Produit supprimé")
```

---

#### **`upload_photo(item_id, csrf_token, anon_id, photo_data, filename)`**

Upload une photo pour un produit.

```python
with open("photo.jpg", "rb") as f:
    photo_data = f.read()

result = client.upload_photo(
    item_id=123456,
    csrf_token=user_data['csrf_token'],
    anon_id=user_data['anon_id'],
    photo_data=photo_data,
    filename="photo.jpg"
)
```

---

#### **`get_item_stats(item_id, csrf_token, anon_id)`**

Récupère les statistiques d'un produit.

```python
stats = client.get_item_stats(
    item_id=123456,
    csrf_token=user_data['csrf_token'],
    anon_id=user_data['anon_id']
)

if stats["success"]:
    print(f"Vues: {stats['data']['view_count']}")
    print(f"Favoris: {stats['data']['favourite_count']}")
```

---

#### **`execute_request(url, method, headers, body, timeout)`**

Exécute une requête HTTP personnalisée.

```python
response = client.execute_request(
    url="https://www.vinted.fr/api/v2/users/current",
    method="GET",
    headers={
        "X-Custom-Header": "value"
    }
)

if response["success"]:
    data = response["data"]
```

---

#### **`execute_batch(requests_list, timeout)`**

Exécute plusieurs requêtes en parallèle.

```python
requests = [
    {"url": "https://www.vinted.fr/api/v2/.../page=1", "method": "GET"},
    {"url": "https://www.vinted.fr/api/v2/.../page=2", "method": "GET"},
    {"url": "https://www.vinted.fr/api/v2/.../page=3", "method": "GET"}
]

result = client.execute_batch(requests)

for i, response in enumerate(result["results"]):
    if response["success"]:
        print(f"Page {i+1}: {len(response['data']['items'])} produits")
```

---

## 📋 Cas d'Usage Complets

### 1. Synchronisation Complète

```python
def sync_vinted_to_backend(client):
    """Synchronise tous les produits Vinted vers le backend"""

    # 1. Récupérer les données utilisateur
    user_data = client.get_user_data()
    if not user_data:
        raise Exception("User data non disponible")

    # 2. Récupérer tous les produits
    products = client.get_all_products(
        user_id=user_data['user_id'],
        csrf_token=user_data['csrf_token'],
        anon_id=user_data['anon_id']
    )

    # 3. Sauvegarder en DB
    for product in products:
        save_product_to_db(product)

    print(f"✅ {len(products)} produits synchronisés")
```

---

### 2. Mise à Jour des Prix en Masse

```python
def update_all_prices(client, user_data, new_price):
    """Modifie le prix de tous les produits"""

    # 1. Récupérer tous les produits
    products = client.get_all_products(
        user_id=user_data['user_id'],
        csrf_token=user_data['csrf_token'],
        anon_id=user_data['anon_id']
    )

    # 2. Mettre à jour chaque produit
    for product in products:
        result = client.update_product(
            item_id=product['id'],
            csrf_token=user_data['csrf_token'],
            anon_id=user_data['anon_id'],
            price=new_price
        )

        if result["success"]:
            print(f"✅ Produit {product['id']} : {new_price}€")

        time.sleep(0.1)  # Throttling
```

---

### 3. Export vers CSV

```python
import csv

def export_products_to_csv(client, user_data, filename="products.csv"):
    """Exporte tous les produits vers un fichier CSV"""

    products = client.get_all_products(
        user_id=user_data['user_id'],
        csrf_token=user_data['csrf_token'],
        anon_id=user_data['anon_id']
    )

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'title', 'price', 'brand', 'size'])
        writer.writeheader()

        for product in products:
            writer.writerow({
                'id': product['id'],
                'title': product['title'],
                'price': product['price'],
                'brand': product.get('brand', {}).get('title', ''),
                'size': product.get('size_title', '')
            })

    print(f"✅ {len(products)} produits exportés vers {filename}")
```

---

## ⚠️ Limitations Actuelles

### 1. Page Bridge Obligatoire

**Problème** : Il faut garder `http://localhost:8000` ouvert dans Firefox.

**Solution** : Implémenter un WebSocket pour communication temps réel (voir code commenté dans `api_bridge_server.py`).

---

### 2. Communication HTTP Polling

**Problème** : Actuellement, la communication se fait via HTTP POST qui nécessite du polling.

**Solution** : Utiliser WebSocket pour communication bidirectionnelle instantanée.

---

### 3. Multi-Utilisateurs

**Problème** : Un seul utilisateur peut utiliser le pont à la fois.

**Solution** : Implémenter un système de sessions/tokens pour identifier les utilisateurs.

---

## 🚀 Prochaines Améliorations

### 1. WebSocket au lieu de HTTP

```python
# À implémenter dans api_bridge_server.py

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        # Recevoir commande du backend
        command = await websocket.receive_json()

        # TODO: Transmettre au plugin via la page HTML
        # TODO: Recevoir réponse du plugin
        # TODO: Renvoyer au backend

        await websocket.send_json(response)
```

---

### 2. Authentification Backend

```python
# Ajouter un token d'authentification
client = VintedProxyClient(
    frontend_url="http://localhost:8000",
    auth_token="YOUR_BACKEND_TOKEN"
)
```

---

### 3. Queue de Requêtes

```python
# Utiliser Redis pour une vraie queue
from redis import Redis
queue = Redis()

# Backend envoie
queue.rpush('plugin_commands', json.dumps(command))

# Plugin récupère
command = queue.blpop('plugin_commands', timeout=5)
```

---

## ✅ Checklist de Démarrage

- [ ] Serveur API Bridge lancé (`python api_bridge_server.py`)
- [ ] Page bridge ouverte dans Firefox (`http://localhost:8000`)
- [ ] Plugin StoFlow chargé dans Firefox
- [ ] Page Vinted ouverte et connecté
- [ ] Status de la page bridge = "✅ Plugin connecté"
- [ ] Test du client Python réussi

---

## 📞 Debug

### Problème : "Plugin non disponible"

**Vérifier** :
1. Le plugin est bien chargé (`about:debugging`)
2. La page `http://localhost:8000` est ouverte
3. F12 sur la page bridge → Console → Pas d'erreurs

---

### Problème : "Aucun onglet Vinted ouvert"

**Solution** :
1. Ouvrir `https://www.vinted.fr`
2. Se connecter
3. Réessayer la commande

---

### Problème : "CSRF token manquant"

**Solution** :
1. Recharger la page Vinted (F5)
2. Récupérer à nouveau les user data
3. Le token est extrait automatiquement

---

**Version** : 1.0.0
**Dernière mise à jour** : 2024-12-07
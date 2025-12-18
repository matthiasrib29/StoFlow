# Product API Documentation

Documentation complète de l'API Product pour Stoflow Backend.

**Date:** 2025-12-04
**Version:** 1.0.0
**Statut:** ✅ Opérationnel

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Modèle de données](#modèle-de-données)
3. [Endpoints disponibles](#endpoints-disponibles)
4. [Attributs produits](#attributs-produits)
5. [Gestion des images](#gestion-des-images)
6. [Règles métier](#règles-métier)
7. [Exemples d'utilisation](#exemples-dutilisation)

---

## 🎯 Vue d'ensemble

L'API Product permet de gérer le catalogue de produits dans un environnement multi-tenant. Chaque tenant a son propre catalogue isolé, tout en partageant les mêmes tables d'attributs (marques, catégories, etc.).

### Fonctionnalités principales

- ✅ CRUD complet sur les produits
- ✅ Gestion des images (max 20 par produit)
- ✅ Workflow de status (DRAFT → PUBLISHED → SOLD → ARCHIVED)
- ✅ Filtrage et pagination
- ✅ Validation automatique des attributs
- ✅ Soft delete
- ✅ Isolation multi-tenant

---

## 📊 Modèle de données

### Product Model

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `id` | Integer | ✓ (auto) | ID unique du produit |
| `sku` | String(100) | ✗ | SKU unique (optionnel) |
| `title` | String(500) | ✓ | Titre du produit |
| `description` | Text | ✓ | Description détaillée |
| `price` | Decimal | ✓ | Prix de vente |
| `category` | String(255) | ✓ | Catégorie (FK → public.categories) |
| `brand` | String(100) | ✗ | Marque (FK → public.brands) |
| `condition` | String(50) | ✓ | État (FK → public.conditions) |
| `label_size` | String(100) | ✗ | Taille étiquette (FK → public.sizes) |
| `color` | String(100) | ✗ | Couleur (FK → public.colors) |
| `material` | String(100) | ✗ | Matière (FK → public.materials) |
| `fit` | String(100) | ✗ | Coupe (FK → public.fits) |
| `gender` | String(100) | ✗ | Genre (FK → public.genders) |
| `season` | String(100) | ✗ | Saison (FK → public.seasons) |
| `status` | Enum | ✓ (auto: DRAFT) | Statut du produit |
| `stock_quantity` | Integer | ✓ (default: 0) | Quantité en stock |
| `dim1-dim6` | Integer | ✗ | Dimensions/mesures (cm) |
| `created_at` | DateTime | ✓ (auto) | Date de création |
| `updated_at` | DateTime | ✓ (auto) | Date de modification |
| `deleted_at` | DateTime | ✗ | Date de suppression (soft delete) |
| `published_at` | DateTime | ✗ (auto) | Date de publication |
| `sold_at` | DateTime | ✗ (auto) | Date de vente |

### ProductImage Model

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `id` | Integer | ✓ (auto) | ID unique de l'image |
| `product_id` | Integer | ✓ | ID du produit (FK) |
| `image_path` | String(1000) | ✓ | Chemin du fichier |
| `display_order` | Integer | ✓ (default: 0) | Ordre d'affichage |
| `created_at` | DateTime | ✓ (auto) | Date d'upload |

---

## 🔌 Endpoints disponibles

### 1. Créer un produit

```http
POST /api/products/
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Levi's 501 Vintage",
  "description": "Jean vintage en excellent état",
  "price": 45.99,
  "category": "Jeans",
  "brand": "Levi's",
  "condition": "EXCELLENT",
  "label_size": "W32L34",
  "color": "Blue",
  "material": "Denim",
  "fit": "Regular",
  "gender": "Men",
  "season": "All-Season",
  "stock_quantity": 1
}
```

**Réponse:** `201 Created`

### 2. Lister les produits

```http
GET /api/products/?skip=0&limit=20&status=PUBLISHED&brand=Nike
Authorization: Bearer {token}
```

**Paramètres de requête:**
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 20, max: 100): Nombre de résultats
- `status` (enum): Filtrer par status (DRAFT, PUBLISHED, SOLD, ARCHIVED)
- `category` (string): Filtrer par catégorie
- `brand` (string): Filtrer par marque

**Réponse:** `200 OK`

```json
{
  "products": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### 3. Récupérer un produit

```http
GET /api/products/{product_id}
Authorization: Bearer {token}
```

**Réponse:** `200 OK` ou `404 Not Found`

### 4. Mettre à jour un produit

```http
PUT /api/products/{product_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Nouveau titre",
  "price": 59.99
}
```

**Réponse:** `200 OK`

### 5. Supprimer un produit (soft delete)

```http
DELETE /api/products/{product_id}
Authorization: Bearer {token}
```

**Réponse:** `204 No Content`

### 6. Mettre à jour le status

```http
PATCH /api/products/{product_id}/status?new_status=PUBLISHED
Authorization: Bearer {token}
```

**Réponse:** `200 OK`

### 7. Récupérer par SKU

```http
GET /api/products/sku/{sku}
Authorization: Bearer {token}
```

**Réponse:** `200 OK` ou `404 Not Found`

---

## 🖼️ Gestion des images

### 8. Upload une image

```http
POST /api/products/{product_id}/images
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: (binary)
display_order: 0
```

**Contraintes:**
- Max 20 images par produit
- Formats: JPG, JPEG, PNG
- Taille max: 5MB
- Validation format (anti-spoofing)

**Réponse:** `201 Created`

### 9. Supprimer une image

```http
DELETE /api/products/{product_id}/images/{image_id}
Authorization: Bearer {token}
```

**Réponse:** `204 No Content`

### 10. Réordonner les images

```http
PUT /api/products/{product_id}/images/reorder
Authorization: Bearer {token}
Content-Type: application/json

{
  "1": 2,
  "2": 0,
  "3": 1
}
```

**Réponse:** `200 OK`

---

## 🏷️ Attributs produits

### Tables d'attributs partagés (schema public)

#### Brands (Marques)
Exemples: Levi's, Nike, Adidas, Zara, H&M, etc.

#### Categories (Catégories)
Hiérarchie parent-enfant:
- Clothing → Jeans, T-Shirts, Jackets, etc.
- Shoes → Sneakers, Boots, Sandals, etc.
- Accessories → Belts, Hats, Scarves, etc.

#### Conditions (États)
- `NEW`: Neuf avec étiquettes
- `EXCELLENT`: Excellent état
- `GOOD`: Bon état
- `SATISFACTORY`: Satisfaisant

#### Colors (Couleurs)
Black, White, Blue, Red, Green, etc.

#### Sizes (Tailles)
- Génériques: XXS, XS, S, M, L, XL, XXL
- Numériques: 34, 36, 38, 40, 42
- Jeans: W26L30, W28L32, W30L34, etc.
- Chaussures: 36, 37, 38, 39, 40, etc.

#### Materials (Matières)
Cotton, Polyester, Denim, Wool, Silk, Leather, etc.

#### Fits (Coupes)
Slim, Regular, Relaxed, Oversized, Tight, Loose

#### Genders (Genres)
Men, Women, Unisex, Kids

#### Seasons (Saisons)
Spring, Summer, Fall, Winter, All-Season

---

## 📏 Règles métier

### Statuts produit (MVP)

```
DRAFT → PUBLISHED → SOLD
           ↓          ↓
       ARCHIVED ← ARCHIVED
```

**Transitions autorisées:**
- DRAFT → PUBLISHED
- PUBLISHED → SOLD
- PUBLISHED → ARCHIVED
- SOLD → ARCHIVED

**Timestamps automatiques:**
- `published_at` rempli lors DRAFT → PUBLISHED
- `sold_at` rempli lors PUBLISHED → SOLD

### Validation FK

Tous les attributs (brand, category, condition, etc.) sont **automatiquement validés** avant création/modification. Si une valeur invalide est fournie, l'API retourne `400 Bad Request` avec un message explicite.

### Soft Delete

Les produits supprimés ne sont **pas effacés** de la base de données :
- `deleted_at` est rempli avec la date/heure actuelle
- Le produit disparaît des listes et recherches
- Les données restent accessibles pour historique/rapports

### Isolation Multi-Tenant

- Chaque tenant a son **propre schema** PostgreSQL (`client_{id}`)
- Les produits sont **totalement isolés** entre tenants
- Les attributs sont **partagés** (schema public)
- Pas de colonne `tenant_id` nécessaire

---

## 💡 Exemples d'utilisation

### Créer un produit complet

```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}

product_data = {
    "title": "Nike Air Max 90",
    "description": "Sneakers iconiques en excellent état",
    "price": 89.99,
    "category": "Sneakers",
    "brand": "Nike",
    "condition": "EXCELLENT",
    "label_size": "42",
    "color": "White",
    "material": "Leather",
    "gender": "Men",
    "season": "All-Season",
    "stock_quantity": 1
}

response = requests.post(
    "http://localhost:8000/api/products/",
    headers=headers,
    json=product_data
)

product = response.json()
print(f"Product created: ID {product['id']}")
```

### Publier un produit

```python
product_id = 123

response = requests.patch(
    f"http://localhost:8000/api/products/{product_id}/status",
    headers=headers,
    params={"new_status": "PUBLISHED"}
)

product = response.json()
print(f"Product published at: {product['published_at']}")
```

### Upload d'images

```python
with open("image1.jpg", "rb") as f:
    files = {"file": f}
    data = {"display_order": 0}

    response = requests.post(
        f"http://localhost:8000/api/products/{product_id}/images",
        headers=headers,
        files=files,
        data=data
    )

print(f"Image uploaded: {response.json()}")
```

### Recherche avec filtres

```python
params = {
    "skip": 0,
    "limit": 20,
    "status": "PUBLISHED",
    "category": "Jeans",
    "brand": "Levi's"
}

response = requests.get(
    "http://localhost:8000/api/products/",
    headers=headers,
    params=params
)

data = response.json()
print(f"Found {data['total']} products")
for product in data['products']:
    print(f"- {product['title']}: ${product['price']}")
```

---

## 🧪 Testing

Tests complets disponibles dans `tests/test_products.py` (37 tests):
- ProductService: 23 tests
- Product API: 13 tests
- Multi-tenant isolation: 1 test

```bash
# Run all product tests
pytest tests/test_products.py -v

# Run specific test class
pytest tests/test_products.py::TestProductService -v
```

---

## 📚 Ressources

- **Swagger UI:** http://localhost:8000/docs
- **Migration Alembic:** `migrations/versions/20251204_1619_add_product_attributes_and_images.py`
- **Seeding script:** `scripts/seed_product_attributes.py`
- **Tests:** `tests/test_products.py`

---

## 🚀 Quick Start

1. **Appliquer la migration:**
```bash
alembic upgrade head
```

2. **Seed les attributs:**
```bash
python scripts/seed_product_attributes.py
```

3. **Tester l'API:**
```bash
# Start server
python main.py

# Access Swagger UI
open http://localhost:8000/docs
```

---

**Dernière mise à jour:** 2025-12-04
**Auteur:** Claude Code
**Statut:** ✅ Production Ready

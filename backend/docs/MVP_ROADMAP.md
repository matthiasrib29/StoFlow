# Stoflow MVP Roadmap

**Version:** 1.0
**Durée:** 8 semaines
**Dernière mise à jour:** 2025-12-08

---

## 🎯 Objectif MVP

Lancer une plateforme fonctionnelle permettant aux vendeurs de:
1. ✅ Créer un compte avec onboarding complet
2. ✅ Gérer leurs produits dans un catalogue centralisé
3. ✅ Publier automatiquement sur Vinted via le plugin navigateur
4. ✅ Synchroniser les produits Vinted existants

**Cible:** 10 beta-testers actifs à la fin du MVP

---

## 📅 Planning Général

| Semaine | Thème | Livrable |
|---------|-------|----------|
| **Week 0** | Setup & Infrastructure | Base de données PostgreSQL multi-tenant fonctionnelle |
| **Week 1** | Authentification & Onboarding | Système d'inscription complet avec onboarding |
| **Week 2** | Gestion Produits (CRUD) | CRUD complet avec validation business logic |
| **Week 3** | Catégories & Attributs | Seed complet + Endpoints de lecture |
| **Week 4** | Upload Images | Stockage local + Association produits |
| **Week 5** | Plugin Navigateur Base | Extension Firefox/Chrome fonctionnelle |
| **Week 6** | Intégration Vinted | Import produits Vinted → Backend |
| **Week 7** | Publication Vinted | Publication Backend → Vinted via plugin |
| **Week 8** | Tests & Polish | Tests end-to-end + Corrections bugs |

---

## 📦 Week 0: Setup & Infrastructure

### Objectifs

- [x] Setup environnement de développement
- [x] Configuration PostgreSQL multi-tenant
- [x] Migrations Alembic initiales
- [x] Healthcheck endpoint

### Livrables

#### 1. Base de Données PostgreSQL

**Schema Public:**
```sql
-- Tables communes (partagées entre tenants)
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'trial',
    max_products INT DEFAULT 100,
    max_platforms INT DEFAULT 1,
    ai_credits_monthly INT DEFAULT 50,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE categories (
    name_en VARCHAR(100) PRIMARY KEY,
    name_fr VARCHAR(100) NOT NULL,
    parent_category VARCHAR(100) REFERENCES categories(name_en),
    gender VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Attributs partagés
CREATE TABLE brands (...);
CREATE TABLE colors (...);
CREATE TABLE sizes (...);
-- etc.
```

**Schema Tenant (client_1, client_2, ...):**
```sql
CREATE SCHEMA client_1;

CREATE TABLE client_1.products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(100) UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    cost_price NUMERIC(10, 2),
    stock_quantity INT DEFAULT 1,
    category VARCHAR(100),
    brand VARCHAR(100),
    size VARCHAR(50),
    color VARCHAR(50),
    material VARCHAR(50),
    fit VARCHAR(50),
    gender VARCHAR(20),
    season VARCHAR(50),
    condition VARCHAR(50),
    status VARCHAR(50) DEFAULT 'draft',
    published_at TIMESTAMPTZ,
    sold_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE client_1.product_images (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES client_1.products(id) ON DELETE CASCADE,
    image_path VARCHAR(500) NOT NULL,
    display_order INT NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE client_1.publications_history (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES client_1.products(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 2. Migrations Alembic

**Fichier:** `migrations/versions/20251207_0050_init_simplified_schema.py`

```python
def upgrade():
    # Créer schema public
    op.execute("CREATE SCHEMA IF NOT EXISTS public")

    # Créer tables public
    create_tenants_table()
    create_users_table()
    create_categories_table()
    create_brands_table()
    # ... autres tables attributs

def downgrade():
    # Supprimer tout
    op.execute("DROP SCHEMA public CASCADE")
```

#### 3. Healthcheck Endpoint

**Fichier:** `main.py`

```python
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }
```

### Validation Week 0

```bash
# Test base de données
psql -U postgres -d stoflow_db -c "\dt public.*"

# Test migration
alembic current

# Test healthcheck
curl http://localhost:8000/health
```

---

## 🔐 Week 1: Authentification & Onboarding

### Objectifs

- [x] Endpoint `/api/auth/register` complet
- [x] Endpoint `/api/auth/login` avec source tracking
- [x] Création automatique schema tenant
- [x] Onboarding enrichi (business info)

### Livrables

#### 1. Endpoint Register

**Route:** `POST /api/auth/register`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "business_name": "Mon Shop",
  "account_type": "business",
  "business_type": "reseller",
  "estimated_products": "100_500",
  "siret": "12345678901234",
  "vat_number": "FR12345678901",
  "phone": "+33612345678",
  "country": "FR",
  "language": "fr"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user_id": 1,
  "tenant_id": 1,
  "role": "admin"
}
```

**Business Logic:**
1. Valider email format
2. Valider password strength (min 8 chars, 1 majuscule, 1 chiffre)
3. Créer tenant dans table `tenants`
4. Créer schema PostgreSQL `client_{tenant.id}`
5. Créer tables dans le schema tenant
6. Créer user admin dans table `users`
7. Générer JWT tokens

#### 2. Endpoint Login

**Route:** `POST /api/auth/login?source=web|plugin|mobile`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user_id": 1,
  "tenant_id": 1,
  "role": "admin"
}
```

**Business Logic:**
1. Valider credentials
2. Vérifier tenant actif
3. Vérifier user actif
4. Logger source de connexion
5. Générer JWT tokens
6. Update last_login timestamp

#### 3. Migration Onboarding

**Fichier:** `migrations/versions/20251208_0949_add_onboarding_fields_to_users.py`

```sql
ALTER TABLE users ADD COLUMN business_name VARCHAR(255);
ALTER TABLE users ADD COLUMN account_type VARCHAR(50);
ALTER TABLE users ADD COLUMN business_type VARCHAR(50);
ALTER TABLE users ADD COLUMN estimated_products VARCHAR(50);
ALTER TABLE users ADD COLUMN siret VARCHAR(14);
ALTER TABLE users ADD COLUMN vat_number VARCHAR(20);
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
ALTER TABLE users ADD COLUMN country VARCHAR(2);
ALTER TABLE users ADD COLUMN language VARCHAR(2) DEFAULT 'en';
```

### Validation Week 1

```bash
# Test register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test1234!", "full_name": "Test User"}'

# Vérifier schema créé
psql -U postgres -d stoflow_db -c "\dn"

# Test login
curl -X POST http://localhost:8000/api/auth/login?source=web \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test1234!"}'
```

---

## 📦 Week 2: Gestion Produits (CRUD)

### Objectifs

- [ ] CRUD complet produits
- [ ] Validation business logic
- [ ] Soft delete
- [ ] Status transitions

### Livrables

#### 1. Endpoint Create Product

**Route:** `POST /api/products`

**Request:**
```json
{
  "sku": "TSHIRT-001",
  "title": "T-shirt Nike Noir",
  "description": "T-shirt Nike en excellent état",
  "price": 15.00,
  "cost_price": 8.00,
  "stock_quantity": 1,
  "category": "t-shirts",
  "brand": "Nike",
  "size": "M",
  "color": "black",
  "gender": "men",
  "condition": "very_good"
}
```

**Business Logic:**
- ✅ Valider tous les attributs existent (brand, color, size, etc.)
- ✅ Valider category existe
- ✅ Valider price > 0
- ✅ Valider stock_quantity >= 0
- ✅ Valider SKU unique (si fourni)
- ✅ Status initial = DRAFT

#### 2. Endpoint List Products

**Route:** `GET /api/products?status=draft&page=1&limit=20`

**Response:**
```json
{
  "products": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

**Business Logic:**
- ✅ Filtrer par status
- ✅ Exclure deleted_at IS NOT NULL
- ✅ Pagination
- ✅ Tri par created_at DESC

#### 3. Endpoint Update Product

**Route:** `PUT /api/products/{id}`

**Business Logic:**
- ✅ Vérifier produit existe et non deleted
- ✅ Vérifier produit non archived
- ✅ Valider transition status si changement
- ✅ Valider nouveaux attributs

#### 4. Endpoint Delete Product (Soft Delete)

**Route:** `DELETE /api/products/{id}`

**Business Logic:**
- ✅ Marquer deleted_at = NOW()
- ✅ Cascade sur images (marquer deleted_at)
- ✅ Ne pas supprimer physiquement

#### 5. Endpoint Publish Product

**Route:** `POST /api/products/{id}/publish`

**Business Logic:**
- ✅ Vérifier status = DRAFT
- ✅ Vérifier stock_quantity > 0
- ✅ Vérifier au moins 1 image
- ✅ Transition DRAFT → PUBLISHED
- ✅ Marquer published_at = NOW()

### Validation Week 2

```bash
# Créer produit
curl -X POST http://localhost:8000/api/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Product", "price": 10.00, "stock_quantity": 1}'

# Lister produits
curl http://localhost:8000/api/products?status=draft \
  -H "Authorization: Bearer $TOKEN"

# Publier produit
curl -X POST http://localhost:8000/api/products/1/publish \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎨 Week 3: Catégories & Attributs

### Objectifs

- [ ] Seed complet des catégories
- [ ] Seed complet des attributs (brands, colors, sizes, etc.)
- [ ] Endpoints de lecture

### Livrables

#### 1. Script Seed Catégories

**Fichier:** `scripts/seed_categories.py`

**Catégories à créer:**
```
Vêtements
├── Homme
│   ├── T-shirts
│   ├── Chemises
│   ├── Pantalons
│   ├── Jeans
│   ├── Vestes
│   └── Pulls
├── Femme
│   ├── Robes
│   ├── Jupes
│   ├── Chemisiers
│   ├── Pantalons
│   ├── Vestes
│   └── Pulls
└── Enfant
    ├── T-shirts
    └── Pantalons
```

#### 2. Script Seed Attributs

**Fichier:** `scripts/seed_product_attributes.py`

**Attributs à créer:**
- **Brands:** Nike, Adidas, Zara, H&M, Pull&Bear, etc. (top 50)
- **Colors:** Black, White, Blue, Red, Green, Yellow, Pink, etc.
- **Sizes:** XS, S, M, L, XL, XXL, 36, 38, 40, 42, 44, 46
- **Materials:** Cotton, Polyester, Wool, Leather, Denim, etc.
- **Fits:** Slim, Regular, Loose, Oversized
- **Seasons:** Spring, Summer, Autumn, Winter, All seasons
- **Conditions:** New with tags, Very good, Good, Satisfactory

#### 3. Endpoints de Lecture

**Routes:**
- `GET /api/categories` - Liste toutes les catégories
- `GET /api/categories?parent=t-shirts` - Sous-catégories
- `GET /api/brands` - Liste toutes les marques
- `GET /api/colors` - Liste toutes les couleurs
- `GET /api/sizes` - Liste toutes les tailles

### Validation Week 3

```bash
# Seed catégories
python scripts/seed_categories.py

# Seed attributs
python scripts/seed_product_attributes.py

# Vérifier données
psql -U postgres -d stoflow_db -c "SELECT COUNT(*) FROM categories;"
psql -U postgres -d stoflow_db -c "SELECT COUNT(*) FROM brands;"

# Test endpoint
curl http://localhost:8000/api/categories
```

---

## 📸 Week 4: Upload Images

### Objectifs

- [ ] Upload local images
- [ ] Association produits
- [ ] Gestion display_order
- [ ] Soft delete cascade

### Livrables

#### 1. Endpoint Upload Image

**Route:** `POST /api/products/{id}/images`

**Request:**
```
Content-Type: multipart/form-data

file: [binary]
```

**Response:**
```json
{
  "id": 1,
  "product_id": 1,
  "image_path": "uploads/1/1/photo_1234567890.jpg",
  "display_order": 1,
  "created_at": "2025-12-08T10:00:00Z"
}
```

**Business Logic:**
- ✅ Valider produit existe et non deleted
- ✅ Valider format image (jpg, png, webp)
- ✅ Valider taille max 5MB
- ✅ Calculer display_order automatiquement (max + 1)
- ✅ Stocker dans `uploads/{tenant_id}/{product_id}/{filename}`

#### 2. Endpoint List Images

**Route:** `GET /api/products/{id}/images`

**Response:**
```json
{
  "images": [
    {
      "id": 1,
      "image_path": "uploads/1/1/photo_1.jpg",
      "display_order": 1
    },
    {
      "id": 2,
      "image_path": "uploads/1/1/photo_2.jpg",
      "display_order": 2
    }
  ]
}
```

#### 3. Endpoint Delete Image

**Route:** `DELETE /api/products/{id}/images/{image_id}`

**Business Logic:**
- ✅ Soft delete (deleted_at = NOW())
- ✅ Réorganiser display_order des images restantes

### Validation Week 4

```bash
# Upload image
curl -X POST http://localhost:8000/api/products/1/images \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@photo.jpg"

# Lister images
curl http://localhost:8000/api/products/1/images \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔌 Week 5: Plugin Navigateur Base

### Objectifs

- [ ] Extension Firefox/Chrome fonctionnelle
- [ ] Authentification via backend
- [ ] Détection page Vinted
- [ ] Extraction données utilisateur

### Livrables

#### 1. Manifest Plugin

**Fichier:** `manifest.json` (Firefox)

```json
{
  "manifest_version": 2,
  "name": "Stoflow Plugin",
  "version": "1.0.0",
  "description": "Publier vos produits sur Vinted automatiquement",
  "permissions": [
    "storage",
    "tabs",
    "https://www.vinted.fr/*"
  ],
  "background": {
    "scripts": ["background.js"]
  },
  "content_scripts": [
    {
      "matches": ["https://www.vinted.fr/*"],
      "js": ["content.js"]
    }
  ],
  "browser_action": {
    "default_popup": "popup.html"
  }
}
```

#### 2. Popup Authentification

**Interface:**
- Formulaire email/password
- Bouton "Se connecter"
- Appel à `POST /api/auth/login?source=plugin`
- Stockage token dans `browser.storage.local`

#### 3. Content Script Vinted

**Fichier:** `content.js`

**Fonctionnalités:**
- Détecter si user connecté sur Vinted
- Extraire user_id, csrf_token, anon_id depuis `window.vinted`
- Envoyer au background script

#### 4. Background Script

**Fichier:** `background.js`

**Fonctionnalités:**
- Recevoir messages depuis content script
- Communiquer avec backend
- Gérer authentification

### Validation Week 5

```bash
# Charger extension dans Firefox
about:debugging → This Firefox → Load Temporary Add-on

# Tester popup
Cliquer sur icône extension → Formulaire s'affiche

# Tester connexion
Se connecter → Token stocké → Popup affiche "Connecté"
```

---

## 📥 Week 6: Intégration Vinted (Import)

### Objectifs

- [ ] Import produits Vinted → Backend
- [ ] Mapping données Vinted → Stoflow
- [ ] Synchronisation initiale

### Livrables

#### 1. Endpoint Import Vinted

**Route:** `POST /api/integrations/vinted/import`

**Request:**
```json
{
  "user_id": 29535217
}
```

**Response:**
```json
{
  "status": "completed",
  "products_imported": 150,
  "products_updated": 20,
  "products_failed": 5,
  "duration_seconds": 45
}
```

**Business Logic:**
1. Récupérer tous les produits Vinted via plugin
2. Mapper chaque produit Vinted → format Stoflow
3. Créer ou mettre à jour produits dans DB
4. Logger historique dans `publications_history`

#### 2. Service Vinted Mapper

**Fichier:** `services/vinted/vinted_mapper.py`

**Mapping:**
```python
def map_vinted_to_stoflow(vinted_product: dict) -> dict:
    """
    Convertit un produit Vinted → format Stoflow

    Mapping:
    - vinted.id → sku (format: VINTED-{id})
    - vinted.title → title
    - vinted.description → description
    - vinted.price → price (string to Decimal)
    - vinted.brand.title → brand
    - vinted.size_title → size
    - vinted.color → color
    - vinted.status → 'published'
    """
    return {
        "sku": f"VINTED-{vinted_product['id']}",
        "title": vinted_product["title"],
        "description": vinted_product.get("description", ""),
        "price": Decimal(vinted_product["price"]),
        "stock_quantity": 1,
        "brand": vinted_product.get("brand", {}).get("title"),
        "size": vinted_product.get("size_title"),
        "color": map_color(vinted_product.get("color")),
        "status": "published"
    }
```

#### 3. Plugin Task: Get All Products

**Action:** `get_all_products`

**Fonctionnalité:**
- Pagination automatique (20 produits/page)
- Récupération de TOUS les produits (peut prendre plusieurs minutes)
- Retry automatique en cas d'erreur

### Validation Week 6

```bash
# Déclencher import
curl -X POST http://localhost:8000/api/integrations/vinted/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 29535217}'

# Vérifier produits importés
curl http://localhost:8000/api/products?status=published \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📤 Week 7: Publication Vinted

### Objectifs

- [ ] Publication Backend → Vinted
- [ ] Création produit sur Vinted
- [ ] Upload images
- [ ] Mise à jour produit

### Livrables

#### 1. Endpoint Publish to Vinted

**Route:** `POST /api/integrations/vinted/publish`

**Request:**
```json
{
  "product_id": 1
}
```

**Response:**
```json
{
  "status": "completed",
  "vinted_id": 4567890,
  "vinted_url": "https://www.vinted.fr/items/4567890",
  "message": "Product published successfully"
}
```

**Business Logic:**
1. Récupérer produit depuis DB
2. Valider que status = PUBLISHED
3. Valider que produit a au moins 1 image
4. Mapper produit Stoflow → format Vinted
5. Créer produit sur Vinted via plugin
6. Upload images sur Vinted
7. Sauvegarder vinted_id dans DB
8. Logger dans publications_history

#### 2. Service Vinted Publisher

**Fichier:** `services/vinted/vinted_publisher.py`

```python
async def publish_product_to_vinted(
    db: Session,
    product_id: int,
    tenant_id: int
) -> dict:
    """
    Publie un produit sur Vinted.

    Steps:
    1. Get product from DB
    2. Map to Vinted format
    3. Create product via plugin
    4. Upload images via plugin
    5. Save vinted_id
    6. Log publication
    """
    product = get_product_by_id(db, product_id, tenant_id)

    # Valider
    if product.status != "published":
        raise HTTPException(400, "Product must be published")

    if not product.images:
        raise HTTPException(400, "Product must have at least 1 image")

    # Mapper
    vinted_data = vinted_adapter.to_vinted_format(product)

    # Créer via plugin
    result = await plugin_client.create_product(vinted_data)

    if not result["success"]:
        raise HTTPException(500, f"Vinted API error: {result['error']}")

    # Upload images
    for image in product.images:
        await plugin_client.upload_photo(
            item_id=result["data"]["item"]["id"],
            photo_path=image.image_path
        )

    # Sauvegarder
    product.vinted_id = result["data"]["item"]["id"]
    db.commit()

    # Logger
    log_publication(db, product_id, "vinted", "create", "completed")

    return {
        "status": "completed",
        "vinted_id": product.vinted_id
    }
```

#### 3. Plugin Task: Create Product

**Action:** `create_product`

**Parameters:**
```json
{
  "title": "T-shirt Nike",
  "description": "...",
  "price": "15.00",
  "brand_id": 53,
  "size_id": 206,
  "catalog_id": 5,
  "color_ids": [1],
  "status_ids": [6]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "item": {
      "id": 4567890,
      "title": "T-shirt Nike",
      "url": "https://www.vinted.fr/items/4567890"
    }
  }
}
```

### Validation Week 7

```bash
# Publier produit
curl -X POST http://localhost:8000/api/integrations/vinted/publish \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1}'

# Vérifier sur Vinted
# → Ouvrir URL du produit dans navigateur
```

---

## ✅ Week 8: Tests & Polish

### Objectifs

- [ ] Tests end-to-end complets
- [ ] Corrections bugs critiques
- [ ] Documentation API
- [ ] Préparation beta

### Livrables

#### 1. Tests End-to-End

**Scénario 1: Cycle Complet Utilisateur**
```python
def test_full_user_journey():
    """
    Test du cycle complet:
    1. Register
    2. Login
    3. Create product
    4. Upload image
    5. Publish product
    6. Publish to Vinted
    """
    # Register
    response = client.post("/api/auth/register", json={...})
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create product
    response = client.post(
        "/api/products",
        json={...},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    product_id = response.json()["id"]

    # Upload image
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            f"/api/products/{product_id}/images",
            files={"file": f},
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 201

    # Publish product
    response = client.post(
        f"/api/products/{product_id}/publish",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Publish to Vinted
    response = client.post(
        "/api/integrations/vinted/publish",
        json={"product_id": product_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

**Scénario 2: Import Vinted**
```python
def test_vinted_import():
    """
    Test import produits Vinted
    """
    # Import
    response = client.post(
        "/api/integrations/vinted/import",
        json={"user_id": 29535217},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["products_imported"] > 0

    # Vérifier produits
    response = client.get(
        "/api/products?status=published",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(response.json()["products"]) > 0
```

#### 2. Corrections Bugs Critiques

**Checklist:**
- [x] ✅ P0-1: Produits supprimés non modifiables
- [x] ✅ P0-2: Images orphelines interdites
- [x] ✅ P0-3: Circularité catégories bloquée
- [x] ✅ P0-4: Publication stock=0 interdite
- [x] ✅ P0-5: État ARCHIVED terminal
- [ ] ✅ P1-1: Validation FK complète
- [ ] ✅ P1-2: Race condition images
- [ ] ✅ P1-3: SKU unique par tenant

#### 3. Documentation API

**Swagger/OpenAPI:**
- Tous les endpoints documentés
- Schémas request/response complets
- Exemples pour chaque endpoint
- Codes erreur documentés

**Fichiers Markdown:**
- `docs/ARCHITECTURE.md` ✅
- `docs/README.md` ✅
- `docs/BUSINESS_LOGIC.md` ✅
- `docs/API.md` (à créer)
- `docs/PLUGIN_INTEGRATION.md` (existe)

#### 4. Préparation Beta

**Checklist Déploiement:**
- [ ] Variables environnement configurées
- [ ] Base de données production créée
- [ ] Migrations appliquées
- [ ] Seed catégories & attributs exécuté
- [ ] Monitoring logs configuré
- [ ] Health check fonctionnel
- [ ] Rate limiting activé
- [ ] CORS configuré pour frontend
- [ ] HTTPS activé
- [ ] Backup automatique configuré

### Validation Week 8

```bash
# Lancer tous les tests
pytest

# Coverage
pytest --cov=. --cov-report=html

# Test end-to-end manuel
# → Suivre le scénario complet dans un navigateur
```

---

## 📊 Métriques de Succès MVP

### KPIs Week 8

| Métrique | Objectif |
|----------|----------|
| **Users inscrits** | 10 beta-testers |
| **Produits créés** | 500+ |
| **Produits publiés sur Vinted** | 100+ |
| **Imports Vinted réussis** | 10+ |
| **Coverage tests** | 80%+ |
| **Bugs critiques** | 0 |
| **Uptime** | 99%+ |

---

## 🚀 Post-MVP (Semaines 9-12)

### Features Additionnelles

1. **eBay Integration**
   - Import produits eBay
   - Publication vers eBay

2. **AI Description Generator**
   - Génération descriptions automatiques
   - Optimisation SEO

3. **Bulk Operations**
   - Mise à jour prix en masse
   - Publication batch

4. **Analytics Dashboard**
   - Vues par produit
   - Taux de conversion
   - Revenus par marketplace

5. **Mobile App**
   - React Native
   - Gestion produits mobile

---

## 📚 Références

- **Architecture:** `docs/ARCHITECTURE.md`
- **Business Logic:** `docs/BUSINESS_LOGIC.md`
- **Plugin Integration:** `docs/PLUGIN_INTEGRATION.md`
- **Onboarding:** `ONBOARDING_IMPLEMENTATION.md`

---

**Version:** 1.0
**Dernière mise à jour:** 2025-12-08

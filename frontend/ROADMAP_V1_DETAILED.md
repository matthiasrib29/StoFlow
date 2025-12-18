# 🎯 ROADMAP V1 DÉTAILLÉE - Stoflow
## Cahier des Charges Complet

**Date** : 5 décembre 2024
**Propriétaire** : Matheus Ribeiro
**Type** : Beta privée gratuite
**Cible** : 1-10 utilisateurs early adopters

---

## 📊 RÉSUMÉ EXÉCUTIF

### Vision Produit
Stoflow V1 permet aux vendeurs de **centraliser leurs produits** et **publier sur multiples plateformes en 1 clic**, avec **synchronisation automatique des stocks** lors des ventes.

### Parcours Utilisateur Principal
1. **Import** : J'importe mes produits actifs depuis Vinted
2. **Ou Création** : Je crée manuellement de nouveaux produits
3. **Publication** : Je sélectionne 2-3 plateformes et publie en 1 clic
4. **Synchronisation** : Quand vendu → statut mis à jour + retrait autres plateformes + email

### Plateformes V1
1. **Vinted** (priorité #1) : Import + Publication complète
2. **eBay** : Publication basique
3. **Etsy** : Publication basique

---

## 🎯 FONCTIONNALITÉS V1 (MUST HAVE)

### 1. 🔐 Authentification & Multi-Tenant

#### Frontend ✅ FAIT
- [x] Login/Register
- [x] JWT storage
- [x] Auth middleware

#### Backend 🔨 À FAIRE
```python
# Endpoints
POST /api/auth/register
  ├─ email, password, tenant_name, full_name
  ├─ Créer tenant + premier utilisateur (role: admin)
  └─ Return JWT token

POST /api/auth/login
  ├─ email, password
  └─ Return JWT + user data

GET /api/auth/me
  ├─ Header: Authorization Bearer {token}
  └─ Return current user

# Business Rules
- Email unique par tenant
- Password min 8 caractères
- JWT expire après 7 jours
- Refresh token (optionnel V1.1)
```

**Temps estimé** : 2 jours

---

### 2. 📦 Gestion Produits (CRUD Complet)

#### Modèle Produit
```python
class Product:
    # Identifiants
    id: UUID (PK)
    sku: str (auto-généré, unique par tenant)
    tenant_id: UUID (FK)

    # Infos basiques
    title: str (max 100 chars, required)
    description: str (max 5000 chars, required)
    price: Decimal (required, min 0.01)

    # Infos détaillées
    brand: str (optional)
    category: str (required) # Liste prédéfinie
    size: str (optional)
    color: str (optional)
    condition: str (required) # ["Neuf", "Très bon état", "Bon état", "Satisfaisant"]

    # Photos
    images: List[str] # URLs S3/Cloudinary (min 1, max 10)

    # Stock & logistique
    stock_quantity: int (default 1)
    weight: Decimal (optional, en kg)
    dimensions: str (optional, format "LxlxH")
    location: str (optional, ville de stockage)

    # Statut
    is_active: bool (default true)
    is_sold: bool (default false)
    sold_at: DateTime (nullable)
    sold_on_platform: str (nullable)

    # Meta
    created_at: DateTime
    updated_at: DateTime
```

#### API Endpoints
```python
# Liste avec filtres
GET /api/products
  ├─ Query params: page, limit, search, category, is_sold, is_active
  ├─ Return: {products: [], total, page, pages}
  └─ Sorting: created_at DESC

# Détail
GET /api/products/{sku}
  └─ Return: product + publications

# Créer
POST /api/products
  ├─ Body: product data
  ├─ Upload images to S3/Cloudinary
  └─ Return: product created

# Modifier
PUT /api/products/{sku}
  ├─ Body: partial product data
  └─ Return: product updated

# Supprimer
DELETE /api/products/{sku}
  ├─ Check: Retirer de toutes les plateformes d'abord
  └─ Soft delete (is_active = false)
```

#### Upload Photos
```python
# Service photo
- Resize: 1200x1200 max
- Compress: quality 85%
- Format: WebP ou JPEG
- Storage: Cloudinary (recommandé) ou S3
- URL: https://cdn.stoflow.com/{tenant_id}/{product_id}/{index}.webp

# Business Rules
- Min 1 photo, max 10 photos
- Max 5MB par photo
- Formats acceptés: JPG, PNG, WebP
- Ordre des photos important (première = photo principale)
```

**Temps estimé** : 4 jours

---

### 3. 🔌 Import depuis Vinted

#### Fonctionnalité
```python
# Endpoint
POST /api/integrations/vinted/import
  ├─ Filter: only active products (not sold)
  ├─ Fetch via Vinted API ou scraping
  └─ Create products in Stoflow

# Mapping Vinted → Stoflow
{
  "title": vinted.title,
  "description": vinted.description,
  "price": vinted.price,
  "brand": vinted.brand_title,
  "category": map_vinted_category(vinted.category_id),
  "size": vinted.size_title,
  "color": vinted.color,
  "condition": map_vinted_status(vinted.status),
  "images": vinted.photos[].url,
  "vinted_id": vinted.id, # Stocker pour éviter duplicatas
  "vinted_url": vinted.url
}

# Business Rules
- Ignorer produits déjà importés (check vinted_id)
- Télécharger et re-upload images sur notre CDN
- Créer produit avec is_active = true
- Ajouter metadata: imported_from = "vinted", imported_at
```

**Temps estimé** : 5-6 jours (dépend disponibilité API Vinted)

---

### 4. 🚀 Publication Multi-Plateformes

#### Architecture
```python
# Modèle Publication
class Publication:
    id: UUID
    product_id: UUID (FK)
    platform: str # "vinted", "ebay", "etsy"
    platform_listing_id: str # ID sur la plateforme
    platform_url: str # URL publique
    status: str # "draft", "active", "sold", "error"
    published_at: DateTime
    error_message: str (nullable)

# Adapter Pattern
class PlatformAdapter(ABC):
    @abstractmethod
    def connect(credentials) -> bool

    @abstractmethod
    def publish(product) -> listing_id

    @abstractmethod
    def update(listing_id, product)

    @abstractmethod
    def delete(listing_id)

    @abstractmethod
    def sync_status(listing_id) -> status

# Implémentations
- VintedAdapter (complet)
- EbayAdapter (basique)
- EtsyAdapter (basique)
```

#### Workflow Publication
```python
# Endpoint
POST /api/publications
  {
    "product_id": UUID,
    "platforms": ["vinted", "ebay", "etsy"],
    "platform_configs": {
      "vinted": {"category_id": 123},
      "ebay": {"duration": 7, "listing_type": "FixedPrice"},
      "etsy": {"shop_section_id": 456}
    }
  }

# Process (Async avec Celery)
1. Validate product exists
2. Check platforms connected
3. For each platform:
   a. Transform product data
   b. Upload images to platform
   c. Create listing
   d. Store publication record
   e. Update product.is_active = true
4. Return results

# Business Rules
- 1 produit peut être publié sur plusieurs plateformes
- Si échec sur 1 plateforme, continuer les autres
- Stocker error_message pour debugging
- Retry 3 fois en cas d'erreur API temporaire
```

**Temps estimé** : 7-8 jours (toutes plateformes)

---

### 5. 🔄 Synchronisation Ventes

#### Workflow
```python
# Webhook Listener
POST /api/webhooks/{platform}
  ├─ Verify signature
  ├─ Parse event
  └─ Process action

# Event: Produit vendu
1. Webhook reçu (Vinted/eBay/Etsy)
2. Find product by platform_listing_id
3. Update product:
   - is_sold = true
   - sold_at = now
   - sold_on_platform = "vinted"
   - stock_quantity = 0
4. For each other publication:
   - Call adapter.delete(listing_id)
   - Update publication.status = "removed"
5. Send email notification to user

# Email Template
Subject: ✅ Produit vendu sur {platform}!

Bonjour {user.full_name},

Votre produit "{product.title}" a été vendu sur {platform} pour {product.price}€.

✓ Stock mis à jour automatiquement
✓ Produit retiré des autres plateformes:
  - eBay
  - Etsy

Voir le détail: {app_url}/dashboard/products/{sku}

Bien cordialement,
L'équipe Stoflow
```

**Temps estimé** : 3-4 jours

---

### 6. 📧 Notifications Email

#### Service Email
```python
# Provider: SendGrid (gratuit jusqu'à 100 emails/jour)
# Ou: Brevo (ex-Sendinblue) - 300 emails/jour gratuit

# Templates
1. Welcome email (après inscription)
2. Product sold notification
3. Publication success/error
4. Weekly summary (optionnel V1.1)

# Configuration
SENDGRID_API_KEY=xxx
FROM_EMAIL=noreply@stoflow.com
FROM_NAME=Stoflow

# Async avec Celery
send_email.delay(to, template, context)
```

**Temps estimé** : 1 jour

---

### 7. 🔐 Connexion aux Plateformes

#### Vinted
```python
# Option 1: OAuth (si disponible)
GET /api/integrations/vinted/auth
  └─ Redirect to Vinted OAuth

GET /api/integrations/vinted/callback
  ├─ Exchange code for token
  └─ Store encrypted token

# Option 2: Cookie/Session (via extension)
POST /api/integrations/vinted/connect
  ├─ Body: { cookies: "..." }
  └─ Store encrypted cookies
```

#### eBay
```python
# OAuth eBay (complexe mais officiel)
1. Register app on eBay Developer Portal
2. Get Client ID + Client Secret
3. Implement OAuth 2.0 flow
4. Store access_token + refresh_token

# Scopes nécessaires
- sell.inventory
- sell.marketing
- sell.account
```

#### Etsy
```python
# OAuth Etsy v3
1. Register app on Etsy Developer
2. OAuth 2.0 flow
3. Store access_token + refresh_token

# Scopes
- listings_w (write listings)
- shops_r (read shop info)
```

**Temps estimé** : 4-5 jours (OAuth complexe)

---

## 🗺️ MODÈLE DE DONNÉES COMPLET

```sql
-- Tenants (entreprises)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user', -- 'admin' ou 'user'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id),
    sku VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    brand VARCHAR(100),
    category VARCHAR(50),
    size VARCHAR(20),
    color VARCHAR(50),
    condition VARCHAR(50),
    images JSONB, -- ["url1", "url2", ...]
    stock_quantity INT DEFAULT 1,
    weight DECIMAL(10, 2),
    dimensions VARCHAR(50),
    location VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_sold BOOLEAN DEFAULT FALSE,
    sold_at TIMESTAMP,
    sold_on_platform VARCHAR(50),
    metadata JSONB, -- Pour import Vinted, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Platform Integrations
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id),
    platform VARCHAR(50) NOT NULL, -- vinted, ebay, etsy
    credentials JSONB, -- Encrypted tokens/cookies
    is_connected BOOLEAN DEFAULT FALSE,
    connected_at TIMESTAMP,
    last_sync TIMESTAMP,
    UNIQUE(tenant_id, platform)
);

-- Publications
CREATE TABLE publications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    platform_listing_id VARCHAR(255),
    platform_url TEXT,
    status VARCHAR(20), -- draft, active, sold, removed, error
    published_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Activity Log
CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id),
    type VARCHAR(50), -- product_created, product_sold, publication_created
    title VARCHAR(255),
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📅 PLANNING DE DÉVELOPPEMENT

### Phase 1 : Fondations Backend (Semaine 1-2)
**Objectif** : API fonctionnelle pour produits

- [ ] Jour 1-2 : Setup projet backend
  - FastAPI + PostgreSQL + SQLAlchemy
  - Docker compose
  - Migrations Alembic
  - Auth JWT

- [ ] Jour 3-5 : API Produits
  - CRUD complet
  - Filtres et pagination
  - Validation Pydantic

- [ ] Jour 6-8 : Upload photos
  - Intégration Cloudinary
  - Resize + compress
  - Tests

- [ ] Jour 9-10 : Tests + Documentation
  - Tests unitaires
  - OpenAPI/Swagger
  - Connexion frontend-backend

**Livrable** : Frontend peut créer/lister/modifier produits

---

### Phase 2 : Import Vinted (Semaine 3)
**Objectif** : Importer produits Vinted actifs

- [ ] Jour 1-2 : Analyse API Vinted
  - Documentation officielle ou reverse engineering
  - Test connexion et authentification

- [ ] Jour 3-4 : Import basique
  - Fetch liste produits actifs
  - Mapping vers modèle Stoflow
  - Téléchargement images

- [ ] Jour 5 : Tests et edge cases
  - Gestion duplicatas
  - Produits sans photo
  - Erreurs API

**Livrable** : Import Vinted fonctionnel

---

### Phase 3 : Publication Vinted (Semaine 4)
**Objectif** : Publier sur Vinted depuis Stoflow

- [ ] Jour 1-2 : VintedAdapter
  - Méthode publish()
  - Mapping catégories
  - Upload photos vers Vinted

- [ ] Jour 3-4 : Tests publication
  - Création listing réel
  - Vérification sur Vinted
  - Gestion erreurs

- [ ] Jour 5 : UI Frontend
  - Bouton "Publier sur Vinted"
  - Feedback utilisateur
  - Error handling

**Livrable** : Publication Vinted opérationnelle

---

### Phase 4 : eBay + Etsy Basique (Semaine 5-6)
**Objectif** : Publication basique sur eBay et Etsy

- [ ] Semaine 5 : eBay
  - OAuth implementation
  - EbayAdapter basique
  - Publication simple (fixed price, 7 days)

- [ ] Semaine 6 : Etsy
  - OAuth implementation
  - EtsyAdapter basique
  - Publication simple

**Livrable** : Publication multi-plateformes

---

### Phase 5 : Synchronisation Ventes (Semaine 7)
**Objectif** : Auto-sync quand vendu

- [ ] Jour 1-2 : Webhooks
  - Endpoint listener
  - Signature verification
  - Event parsing

- [ ] Jour 3-4 : Logique sync
  - Update product status
  - Retrait autres plateformes
  - Email notification

- [ ] Jour 5 : Tests
  - Simuler vente
  - Vérifier sync
  - Test email

**Livrable** : Sync automatique fonctionnel

---

### Phase 6 : Polish & Déploiement (Semaine 8)
**Objectif** : Production-ready

- [ ] Jour 1-2 : Tests complets
  - Tests e2e
  - Fix bugs
  - Performance

- [ ] Jour 3-4 : Déploiement
  - Setup serveur (VPS ou PaaS)
  - CI/CD pipeline
  - Monitoring

- [ ] Jour 5 : Documentation
  - Guide utilisateur
  - Vidéo démo
  - Onboarding

**Livrable** : V1 déployée en production

---

## ✅ CRITÈRES DE SUCCÈS V1

La V1 est considérée comme réussie si :

### Critères Fonctionnels
1. ✅ Un utilisateur peut importer ses produits Vinted actifs
2. ✅ Un utilisateur peut créer un nouveau produit avec 5 photos
3. ✅ Un utilisateur peut publier sur Vinted + eBay + Etsy en 1 clic
4. ✅ Quand vendu sur une plateforme → retrait automatique des autres
5. ✅ Email de notification reçu dans les 5 minutes

### Critères Techniques
1. ✅ API response time < 500ms (p95)
2. ✅ Uptime > 99% sur 30 jours
3. ✅ Upload photo < 5 secondes
4. ✅ Publication multi-plateformes < 30 secondes
5. ✅ 0 données perdues (backups quotidiens)

### Critères Business
1. ✅ 5-10 utilisateurs beta actifs
2. ✅ Feedback positif (NPS > 8/10)
3. ✅ Au moins 50 produits publiés sur toutes plateformes
4. ✅ Taux de synchronisation > 95%

---

## 🚨 RISQUES & MITIGATION

### Risque #1 : API Vinted non documentée
**Impact** : Haut
**Probabilité** : Moyenne
**Mitigation** :
- Reverse engineering via DevTools
- Utiliser extension browser comme proxy
- Solution de secours : scraping HTML

### Risque #2 : OAuth eBay/Etsy complexe
**Impact** : Moyen
**Probabilité** : Haute
**Mitigation** :
- Utiliser SDKs officiels (python-ebay, python-etsy)
- Prévoir 2-3 jours de plus si blocage
- Community support (forums eBay/Etsy developers)

### Risque #3 : Volume photos trop élevé
**Impact** : Faible (beta limitée)
**Probabilité** : Faible
**Mitigation** :
- Limite 100 produits par user en beta
- Compression agressive (quality 80%)
- Utiliser Cloudinary free tier (25GB)

### Risque #4 : Webhooks non supportés
**Impact** : Moyen
**Probabilité** : Moyenne
**Mitigation** :
- Solution de secours : polling toutes les 15 min
- Vinted : check via API polling
- eBay/Etsy : webhooks normalement dispos

---

## 💰 BUDGET INFRASTRUCTURE (Beta Gratuite)

| Service | Plan | Coût |
|---------|------|------|
| Backend Hosting | Railway/Render free tier | 0€ |
| Base de données | PostgreSQL Render free | 0€ |
| Photos | Cloudinary free (25GB, 25k imgs) | 0€ |
| Email | Brevo free (300/jour) | 0€ |
| Domain | stoflow.com | ~12€/an |
| SSL | Let's Encrypt | 0€ |
| **TOTAL** | | **~12€/an** |

---

## 📞 PROCHAINES ÉTAPES

1. **Maintenant** :
   - ✅ Valider cette roadmap
   - ✅ Prioriser Vinted > eBay > Etsy

2. **Cette semaine** :
   - [ ] Setup backend FastAPI + PostgreSQL
   - [ ] Connecter frontend au backend
   - [ ] API Produits v1

3. **Semaine prochaine** :
   - [ ] Upload photos Cloudinary
   - [ ] Commencer analyse API Vinted

---

**Questions ouvertes** :
1. Préférence hébergement ? (Railway, Render, DigitalOcean, OVH)
2. Besoin d'aide sur OAuth eBay/Etsy ?
3. Stocker photos Cloudinary OK ? Ou AWS S3 ?

---

**Document créé le** : 5 décembre 2024
**Dernière mise à jour** : 5 décembre 2024
**Status** : ✅ Validé et prêt pour implémentation

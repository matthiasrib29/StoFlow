# Business Plan - Stoflow

## 📋 Vision du Projet

**Nom :** Stoflow
**Domaine :** stoflow.io
**Tagline :** "Flow your products everywhere"

**Concept :** Plateforme SaaS permettant aux vendeurs (B2B et B2C) de publier leurs produits simultanément sur plusieurs plateformes de vente (Vinted, eBay, Etsy, Facebook Marketplace, etc.) avec génération automatique de descriptions par IA.

**Problème résolu :**
- Publication manuelle chronophage sur chaque plateforme
- Descriptions non optimisées pour chaque marketplace
- Gestion complexe des attributs différents par plateforme
- Risque de blocages (403) avec les outils existants

**Cible client :**
- Revendeurs mode/luxe (seconde main)
- Créateurs/artisans
- Petites boutiques physiques souhaitant vendre en ligne
- **Exclu :** Dropshippers (pour éviter abus et mauvaise réputation)

---

## 🎯 Modèle Commercial

### Dual Model : B2B + B2C

#### B2C (Particuliers / Revendeurs individuels)
```
Starter    : 9.90€/mois   - 50 produits max, 2 plateformes
Standard   : 19.90€/mois  - 200 produits, 5 plateformes, IA descriptions
Premium    : 39.90€/mois  - Illimité produits/plateformes, support prioritaire
```

#### B2B (Boutiques / Professionnels)
```
Business   : 99€/mois     - Multi-utilisateurs, API access, white-label partiel
Enterprise : Sur devis    - Infrastructure dédiée, SLA 99.9%, account manager
```

### Options de facturation (à finaliser)
- [ ] Par nombre de produits actifs
- [ ] Par nombre de publications/mois
- [ ] Par plateforme connectée
- [ ] Crédit publications (ex: 500 pubs/mois incluses, puis 0.10€/pub)

**Recommandation :** Facturation hybride
- Base fixe selon tier (9.90€, 19.90€, etc.)
- Limites de produits et plateformes par tier
- Crédit publications inclus, puis pay-per-use au-delà

---

## 🛠️ Stack Technique

### Architecture : Hybride (Core Monolithique + Workers Asynchrones)

**Backend Core (FastAPI + PostgreSQL)**
- API REST pour dashboard
- Authentification JWT
- Gestion multi-tenant
- Rate limiting centralisé

**Workers Asynchrones (RQ + Redis)**
- Publications vers plateformes (tâches longues)
- Génération descriptions IA
- Import produits WooCommerce/Shopify
- Retry automatique en cas d'erreur

**Avantages :**
✅ Simple à démarrer (monolithique)
✅ Scalable (ajout de workers)
✅ Séparation tâches lourdes
✅ Monitoring facile (RQ Dashboard)

---

## 🎨 Frontend : Vue.js + Nuxt 4 ✅ (CHOISI)

### Stack Frontend Sélectionnée

**Framework :** Vue.js 3.5 + Nuxt 4 (Release juin 2025)
**UI Library :** PrimeVue ou Vuetify (à définir selon design)
**State Management :** Pinia (intégré Nuxt)
**Data Fetching :** Nuxt useAsyncData + useFetch
**Auth :** @sidebase/nuxt-auth
**PWA :** @vite-pwa/nuxt (Phase 2)

### Pourquoi Vue/Nuxt ?

**✅ Avantages décisifs :**
- **Connaissance existante** : Maîtrise Vue.js déjà acquise
- **Productivité immédiate** : Pas de courbe d'apprentissage
- **Nuxt 4 moderne** : Performance +30%, 200+ modules, Nitro engine
- **Écosystème mature** : Solutions SaaS établies (auth, multi-tenant)
- **Documentation française** : Support communauté francophone
- **Recrutement raisonnable** : Devs Vue disponibles (2-4 semaines)

**⚠️ Trade-offs acceptés :**
- Écosystème plus petit que React (mais suffisant pour SaaS)
- Moins de libs UI que React (mais PrimeVue/Vuetify excellent)

### Stack Technique Complète

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: [
    '@sidebase/nuxt-auth',      // Authentification
    '@pinia/nuxt',               // State management
    '@vite-pwa/nuxt',            // PWA (Phase 2)
    'nuxt-icon',                 // Icons
  ],

  // Multi-tenant header injection
  auth: {
    provider: {
      type: 'local',
      endpoints: {
        signIn: { path: '/api/auth/login', method: 'post' },
        signOut: { path: '/api/auth/logout', method: 'post' },
        getSession: { path: '/api/auth/session', method: 'get' }
      }
    }
  },

  // Rate limiting via middleware
  routeRules: {
    '/api/**': {
      headers: { 'X-Tenant-ID': '{{ tenant_id }}' }
    }
  }
})
```

### UI Component Library (À choisir)

**Option A : PrimeVue** ⭐ (Recommandé Dashboard B2B)
- 80+ composants
- DataTable avancée (sort, filter, pagination)
- Thèmes professionnels
- Documentation excellente

**Option B : Vuetify**
- Material Design
- 100+ composants
- Plus orienté mobile
- Grande communauté

### PWA Support (Phase 2)

```typescript
// Configuration PWA simple
pwa: {
  manifest: {
    name: 'Stoflow',
    short_name: 'Stoflow',
    description: 'Flow your products everywhere'
  },
  workbox: {
    navigateFallback: '/'
  }
}
```

---

## 📚 Ressources Vue/Nuxt

**Comparatif complet :** Voir `FRONTEND_COMPARISON_2025.md`
**Limitations SvelteKit :** Voir `SVELTEKIT_VS_VUE_DETAILED.md`
**Guide PWA :** Voir `WEB_TO_APP_OPTIONS_2025.md`

---

## 💾 Base de Données Multi-Tenant : Comparatif

### Option 1 : Shared Database + tenant_id ⚠️

**Structure :**
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL,  -- Client ID
    sku VARCHAR(50),
    title TEXT,
    ...
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Index obligatoire sur TOUTES les tables
CREATE INDEX idx_products_tenant ON products(tenant_id);
```

**Pour :**
- Simple à mettre en place
- Migrations faciles (1 seule BDD)
- Backup/restore simplifié
- Coûts infrastructure bas

**Contre :**
- ⚠️ Risque fuite données entre clients (bug = catastrophe)
- ⚠️ Performances dégradées si 1 client fait beaucoup de requêtes
- ⚠️ Impossible d'isoler un client problématique
- Tous les clients impactés si BDD down

**Sécurité :** 🌟🌟 (1 oubli de WHERE tenant_id = X = leak)

**Requêtes :**
```python
# TOUTES les requêtes doivent filtrer par tenant
products = db.query(Product).filter(Product.tenant_id == current_user.tenant_id).all()

# ⚠️ Risque d'oubli = bug critique
products = db.query(Product).all()  # ❌ TOUS LES CLIENTS !
```

---

### Option 2 : Database par Client 🔒

**Structure :**
```
PostgreSQL Server
├── db_client_1
│   ├── products
│   ├── vinted_products
│   └── ...
├── db_client_2
│   ├── products
│   └── ...
└── db_client_N
```

**Pour :**
- 🔒 Isolation maximale (sécurité top)
- Performance client indépendante
- Facilité scale horizontal (sharding naturel)
- Backup/restore par client
- Conformité RGPD facilitée

**Contre :**
- ⚠️ Gestion complexe (N databases)
- Migrations = boucle sur chaque BDD
- Coût infra élevé (ressources x N)
- Requêtes cross-tenant impossibles (analytics globaux)

**Sécurité :** 🌟🌟🌟🌟🌟

**Code :**
```python
def get_db(tenant_id: int):
    db_name = f"db_client_{tenant_id}"
    engine = create_engine(f"postgresql:///{db_name}")
    return engine
```

---

### Option 3 : Schema par Client ✅ (CHOISI)

**Structure PostgreSQL Retenue :**
```
PostgreSQL Database: stoflow_db
├── schema: public (tables communes)
│   ├── tenants
│   ├── users
│   ├── subscriptions
│   ├── platform_mappings      -- Templates mapping partagés
│   └── ai_prompts_templates   -- Templates IA partagés
├── schema: client_1
│   ├── products
│   ├── vinted_products
│   ├── ebay_products
│   ├── publications_history
│   └── ai_generations_log
├── schema: client_2
│   ├── products
│   └── ...
└── schema: client_N
```

### Pourquoi Schema par Client ?

**✅ Avantages décisifs :**
- **Isolation données** : Sécurité maximale (données client séparées)
- **Performances indépendantes** : 1 client lent n'impacte pas les autres
- **1 seule connexion PostgreSQL** : Simplicité infrastructure
- **Analytics possibles** : Requêtes cross-tenant via `public` schema
- **Migrations simplifiées** : Script Alembic sur tous schemas
- **Backup sélectif** : Possibilité backup par client

**⚠️ Complexité gérée :**
- Gestion schemas dynamiques (via middleware FastAPI)
- Limite PostgreSQL : ~10k schemas (largement suffisant)

**Sécurité :** 🌟🌟🌟🌟 (Isolation forte)

### Implémentation FastAPI

```python
# Middleware multi-tenant
from fastapi import Request, Depends
from sqlalchemy import text

def get_tenant_id(request: Request) -> int:
    """Extrait tenant_id depuis JWT token"""
    token = request.headers.get("Authorization")
    # Décode JWT et retourne tenant_id
    return decoded_token["tenant_id"]

def get_db(tenant_id: int = Depends(get_tenant_id)):
    """Retourne session avec search_path isolé"""
    schema = f"client_{tenant_id}"
    session = SessionLocal()

    # Isolation automatique via search_path
    session.execute(text(f"SET search_path TO {schema}, public"))

    try:
        yield session
    finally:
        session.close()

# Usage dans routes
@app.get("/api/products")
def get_products(db: Session = Depends(get_db)):
    # ✅ Requête automatiquement isolée au client
    return db.query(Product).all()
```

### Migration Alembic Multi-Schema

```python
# alembic/env.py
def get_all_client_schemas():
    """Retourne tous les schemas clients"""
    conn = connection.execute(text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'client_%'
    """))
    return [row[0] for row in conn.fetchall()]

def run_migrations_online():
    # Migration sur schema public
    context.configure(target_metadata=public_metadata)
    context.run_migrations()

    # Migration sur tous les schemas clients
    client_schemas = get_all_client_schemas()
    for schema in client_schemas:
        context.configure(
            target_metadata=tenant_metadata,
            version_table_schema=schema
        )
        connection.execute(text(f"SET search_path TO {schema}"))
        context.run_migrations()
```

### Tables Public vs Client Schema

**Schema `public` (partagé) :**
```python
class Tenant(Base):
    __tablename__ = 'tenants'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    subscription_tier = Column(String)
    created_at = Column(DateTime)

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('public.tenants.id'))
    email = Column(String)
    hashed_password = Column(String)

class PlatformMapping(Base):
    """Templates mapping réutilisables"""
    __tablename__ = 'platform_mappings'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True)
    platform = Column(String)  # vinted, ebay, etsy
    brand_name = Column(String)
    brand_id_platform = Column(Integer)
```

**Schema `client_X` (isolé) :**
```python
class Product(Base):
    """Produits du client (isolés par schema)"""
    __tablename__ = 'products'
    # Pas de __table_args__ = utilise search_path dynamique

    sku = Column(Integer, primary_key=True)
    title = Column(String)
    price = Column(Float)
    stock_quantity = Column(Integer)

class VintedProduct(Base):
    __tablename__ = 'vinted_products'

    sku = Column(Integer, primary_key=True)
    id_vinted = Column(BigInteger)
    statut = Column(String)
    price = Column(Float)

class PublicationHistory(Base):
    __tablename__ = 'publications_history'

    id = Column(Integer, primary_key=True)
    sku = Column(Integer)
    platform = Column(String)
    status = Column(String)
    error_message = Column(Text)
    created_at = Column(DateTime)
```

### Migration depuis BDD Actuelle

```sql
-- 1. Créer schema pour vos données existantes
CREATE SCHEMA client_demo;

-- 2. Migrer tables métier vers schema client
ALTER TABLE product.products SET SCHEMA client_demo;
ALTER TABLE vinted.vinted_products SET SCHEMA client_demo;
ALTER TABLE ebay.ebay_products SET SCHEMA client_demo;

-- 3. Créer tables public multi-tenant
CREATE TABLE public.tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE public.users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES public.tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL
);

-- 4. Insérer tenant demo
INSERT INTO public.tenants (id, name, subscription_tier)
VALUES (1, 'Demo Account', 'premium');

-- 5. Tester isolation
SET search_path TO client_demo, public;
SELECT * FROM products; -- ✅ Seulement client_demo.products
```

---

### 🏆 Décision Finalisée : Schema par Client

**Justification :**
1. **Sécurité** : Isolation forte entre clients
2. **Performance** : Clients indépendants
3. **Simplicité infra** : 1 seule BDD PostgreSQL
4. **Analytics** : Tables `public` pour stats globales
5. **Migration facile** : Depuis votre BDD actuelle

**Prochaine étape :** Créer scripts Alembic migration multi-schema

---

## 🚀 Plateformes Supportées

### Phase 1 (MVP) : Vinted Uniquement
- Réutiliser votre code Python existant
- Valider le concept avec 1 plateforme
- Affiner l'IA génération descriptions

### Phase 2 : Ajout progressif
1. **eBay** (API officielle OAuth2)
2. **Etsy** (API officielle, bonne doc)
3. **Leboncoin** (scraping/cookies comme Vinted)
4. **Facebook Marketplace** (via Graph API)

### Phase 3 : E-commerce propriétaire
- **WooCommerce** (API REST, facile)
- **Shopify** (API GraphQL, excellente)
- **PrestaShop** (API REST)

### Intégrations Futures
- Instagram Shopping
- TikTok Shop
- Vestiaire Collective
- Depop

---

## 🤖 Intelligence Artificielle

### Génération Descriptions : Hybride Caching

**Stack :**
- **API principale :** OpenAI GPT-4 Turbo (ou Claude 3.5)
- **Caching intelligent :** Redis + PostgreSQL

**Workflow :**
```python
1. User demande génération description pour produit SKU#12345

2. Check cache :
   - Hash attributs : hash(marque + catégorie + couleur + état)
   - Si hash existe en cache → retourner description (0€)

3. Si pas en cache :
   - Appel API GPT-4 (~0.03$/requête)
   - Stocker résultat avec hash
   - Template par plateforme :
     * Vinted : 300 chars max, keywords SEO Vinted
     * eBay : 5000 chars, style formel, bullet points
     * Etsy : storytelling, émotionnel, 200 chars

4. Personnalisation post-cache :
   - Remplacer variables : {brand}, {price}, {condition}
   - Ajuster selon préférences user (ton, émojis, etc.)
```

**Économie :**
```
Scenario : 1000 produits à publier sur 3 plateformes

Sans cache :
- 3000 appels API × 0.03$ = 90$

Avec cache (taux hit 70%) :
- 900 appels API × 0.03$ = 27$ (économie 70%)
```

**Prompt Template (exemple Vinted) :**
```
Tu es un expert en vente de vêtements d'occasion sur Vinted.

Produit :
- Marque : {brand}
- Catégorie : {category}
- Taille : {size}
- Couleur : {color}
- État : {condition}
- Matériau : {material}

Crée une description de 200-300 caractères :
- Accrocheuse et naturelle
- Met en avant les points forts
- Utilise keywords SEO Vinted (vintage, tendance, état neuf, etc.)
- Ton amical mais professionnel
- Pas d'émojis excessifs

Description :
```

### Détourage Images (Phase 2)

**Options :**
1. **remove.bg API** : 0.20$/image, qualité top
2. **Cloudinary AI Background Removal** : Inclus dans leur plan
3. **Modèle local (RMBG-v1.4)** : Gratuit, besoin GPU

**Recommandation MVP :** Pas de détourage pour Phase 1 (focus publication)

---

## 🔐 Authentification Plateformes : Hybride Intelligent

### Stratégie par Plateforme

| Plateforme | Méthode | Difficulté |
|------------|---------|------------|
| **eBay** | OAuth2 officiel | ✅ Facile |
| **Etsy** | OAuth2 officiel | ✅ Facile |
| **Shopify** | OAuth2 officiel | ✅ Facile |
| **Vinted** | Extension navigateur (cookies) | ⚠️ Moyen |
| **Leboncoin** | Extension navigateur (cookies) | ⚠️ Moyen |
| **Facebook Marketplace** | Graph API Token | ✅ Facile |

### Extension Navigateur (Chrome/Firefox)

**Fonctionnement :**
1. User installe extension Stoflow
2. User se connecte sur Vinted dans son navigateur
3. Extension capture automatiquement :
   - Cookies d'authentification
   - CSRF Token
   - Session ID
4. Extension envoie à votre API via HTTPS
5. Backend stocke dans PostgreSQL (encrypted)

**Sécurité :**
```python
from cryptography.fernet import Fernet

# Chiffrer les cookies avant stockage
def encrypt_cookies(cookies: str, tenant_id: int):
    key = get_tenant_encryption_key(tenant_id)  # Unique par client
    f = Fernet(key)
    return f.encrypt(cookies.encode())
```

**Refresh automatique :**
- Extension détecte changement de cookies
- Update automatique en background
- User n'a rien à faire

---

## 📊 MVP (Version 1) : Scope

### Features Incluses

#### 1. Dashboard Client (Nuxt 4 + PrimeVue)
- ✅ Inscription / Login (email/password) → @sidebase/nuxt-auth
- ✅ Wizard onboarding :
  1. Connecter Vinted (via extension)
  2. Importer produits WooCommerce (optionnel)
  3. Publier 1er produit test
- ✅ Liste produits avec :
  - Miniature image
  - SKU, Titre, Prix
  - Statut : À publier / Publié / Erreur
  - Actions : Modifier, Publier, Supprimer
  - **Composant :** PrimeVue DataTable (sort, filter, pagination)
- ✅ Vue détail produit avec preview
- ✅ Statistiques session :
  - X produits publiés aujourd'hui
  - Y en attente
  - Z erreurs
  - Rate limit Vinted : 15/40 utilisées
  - **Composants :** PrimeVue Charts + Cards

#### 2. Backend (FastAPI + RQ)
- ✅ API REST :
  - `GET /api/products` : Liste produits
  - `POST /api/products` : Créer produit
  - `PUT /api/products/{id}` : Modifier
  - `POST /api/products/{id}/publish` : Publier sur Vinted
  - `GET /api/publications/status` : Statut publications en cours
  - `POST /api/ai/generate-description` : Générer description IA
- ✅ Worker RQ :
  - Task : `publish_to_vinted(product_id, tenant_id)`
  - Task : `generate_ai_description(product_id, platform)`
  - Retry automatique (3 tentatives)
- ✅ Rate limiting par compte Vinted :
  - Redis : `vinted:{cookies_hash}:rate_limit`
  - 40 requêtes / 2h

#### 3. IA Génération Descriptions
- ✅ Intégration OpenAI API
- ✅ Cache intelligent (hash attributs)
- ✅ Templates par plateforme (Vinted uniquement pour MVP)
- ✅ Personnalisation : ton, longueur, émojis

#### 4. Extension Navigateur
- ✅ Capture cookies Vinted automatique
- ✅ Upload vers API backend (HTTPS)
- ✅ Icon toolbar : statut connexion (vert/rouge)
- ✅ Popup : "Connecté à Vinted en tant que @username"

### Features EXCLUES du MVP (Phase 2+)
- ❌ Autres plateformes (eBay, Etsy, etc.)
- ❌ Détourage images IA
- ❌ Import Shopify/PrestaShop
- ❌ Analytics avancés (graphiques ventes)
- ❌ Multi-utilisateurs (équipes)
- ❌ API publique pour intégrations

---

## 💰 Coûts Estimés

### Infrastructure (Début)

**Serveur Backend (Hetzner VPS) :** 10€/mois
- 4 vCPU, 8GB RAM, 160GB SSD
- Suffisant pour 100 premiers clients

**Base de Données (PostgreSQL) :** Inclus dans VPS

**Redis (Rate limiting + Cache) :** Inclus dans VPS

**Stockage Images (500GB) :** 5€/mois
- Hetzner Storage Box

**Frontend (Vercel) :** 0€/mois (plan gratuit)
- Jusqu'à 100GB bandwidth

**Total infra :** ~15€/mois

### IA (Variable selon usage)

**OpenAI API :**
- GPT-4 Turbo : 0.01$/1k tokens input, 0.03$/1k tokens output
- Moyenne : 500 tokens par description = ~0.02$ par génération

**Estimations :**
```
10 clients × 50 produits × 3 plateformes = 1500 descriptions
Avec cache 70% : 450 appels API × 0.02$ = 9$/mois

100 clients : ~90$/mois
```

**Total coûts :** ~25-125€/mois (selon usage IA)

### Break-even

**Tier Standard (19.90€/mois) :**
- 2 clients = 39.80€ → Rentable dès le début

---

## 📅 Roadmap

### Phase 0 : Préparation (2 semaines)
- [ ] Créer architecture multi-tenant (schemas PostgreSQL)
- [ ] Migrer code Vinted actuel en API REST
- [ ] Setup Redis + RQ workers
- [ ] Tests rate limiting

### Phase 1 : MVP (6-8 semaines)
- [ ] Backend API (FastAPI) multi-tenant - 2 semaines
- [ ] Dashboard Nuxt 4 + PrimeVue - 3 semaines
- [ ] Extension navigateur (Firefox/Chrome) - 1 semaine
- [ ] Intégration IA descriptions - 1 semaine
- [ ] Tests alpha avec 5 beta-testers - 1 semaine

### Phase 2 : Ajout Plateformes (3 mois)
- [ ] eBay (OAuth2 + API) - 3 semaines
- [ ] Etsy (OAuth2 + API) - 3 semaines
- [ ] Leboncoin (extension cookies) - 2 semaines
- [ ] Facebook Marketplace - 2 semaines

### Phase 3 : Features Avancées (3 mois)
- [ ] Détourage images IA
- [ ] Analytics avancés (graphiques ventes)
- [ ] Import Shopify automatique
- [ ] Multi-utilisateurs (équipes B2B)
- [ ] API publique

---

## ⚠️ Risques et Mitigation

### Risque 1 : Blocages API Vinted (403)

**Probabilité :** Moyenne
**Impact :** Critique (utilisateurs bloqués)

**Mitigation :**
- Extension navigateur = requêtes depuis vrai Firefox
- Rate limiting strict par compte
- Monitoring temps réel des erreurs 403
- Backup : ralentir automatiquement si détection
- Communication proactive aux users

### Risque 2 : Changement API Plateformes

**Probabilité :** Élevée (Vinted change souvent)
**Impact :** Élevé

**Mitigation :**
- Abstraire chaque plateforme (pattern Adapter)
- Tests automatisés quotidiens
- Monitoring alertes si échecs
- Communication aux users + ETA fix

### Risque 3 : Coûts IA explosent

**Probabilité :** Faible (avec cache)
**Impact :** Moyen

**Mitigation :**
- Cache intelligent (hit rate >70%)
- Limites par tier (ex: 100 générations/mois en Starter)
- Monitoring coûts OpenAI quotidien
- Option fallback : templates sans IA

### Risque 4 : Concurrence

**Probabilité :** Élevée
**Impact :** Moyen

**Mitigation :**
- Focus niche mode/vintage (vs généraliste)
- Qualité IA descriptions (vs templates basiques)
- UX simplifiée (vs outils complexes)
- Support réactif (vs self-service only)

---

## 🎯 Prochaines Étapes

### Décisions à Prendre

1. **Nom de la plateforme** ✅
   - **FINALISÉ :** Stoflow
   - **Domaine :** stoflow.io (acquis)

2. **Pricing définitif**
   - Valider les tiers (9.90€, 19.90€, 39.90€)
   - Définir limites exactes par tier

3. **Stack frontend finalisée** ✅
   - **CHOISI :** Nuxt 4 (Vue.js) + PrimeVue
   - Raison : Maîtrise Vue existante

4. **Stratégie BDD multi-tenant** ✅
   - **CHOISI :** Schema par Client
   - Prochaine étape : Scripts Alembic migration

### Actions Immédiates

1. **Setup infrastructure de dev :**
   ```bash
   # Architecture projet
   stoflow/
   ├── backend/          # FastAPI + multi-tenant
   ├── frontend/         # Nuxt 4 + PrimeVue
   ├── extension/        # Firefox/Chrome WebExtension
   ├── workers/          # RQ workers
   └── shared/           # Types/models partagés
   ```

2. **Créer architecture multi-tenant PostgreSQL (Schema par client)**
   - Scripts Alembic migration multi-schema
   - Middleware FastAPI isolation tenant
   - Tables `public` + `client_X`

3. **Migrer code Vinted actuel en API REST réutilisable**

4. **Prototype Nuxt 4 dashboard**
   - Page login (@sidebase/nuxt-auth)
   - Liste produits (PrimeVue DataTable)
   - Intégration API FastAPI

5. **Tester intégration OpenAI pour générations descriptions**

---

## 📝 Notes Finales

Ce business plan est évolutif. Les décisions finalisées :
- ✅ **Frontend :** Nuxt 4 (Vue.js) + PrimeVue
- ✅ **BDD Multi-tenant :** Schema par Client (PostgreSQL)
- ✅ **Backend :** FastAPI + RQ workers + Redis
- ✅ **Application mobile :** PWA (Phase 2)

**Choix basés sur :**
- Maîtrise Vue.js existante → productivité immédiate
- Architecture multi-tenant sécurisée → isolation forte
- Code Python existant → réutilisation maximale
- Scalabilité 100-1000 clients → architecture éprouvée

**Prochaine étape prioritaire :** Créer architecture multi-tenant PostgreSQL

---

**Document créé le :** 2025-12-03
**Dernière mise à jour :** 2025-12-04
**Version :** 2.0 (Frontend + BDD finalisés)

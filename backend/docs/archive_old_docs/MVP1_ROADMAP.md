# Stoflow - MVP 1 Roadmap Complète

**Projet :** Stoflow - SaaS Multi-Canal (Publication Vinted)
**Domaine :** stoflow.io
**Tagline :** "Flow your products everywhere"
**Objectif MVP1 :** Dashboard client fonctionnel avec publication Vinted
**Durée estimée :** 6-8 semaines
**Date création :** 2025-12-04

---

## 🎯 Objectifs MVP1

### Fonctionnalités Cibles

**✅ Ce qui DOIT fonctionner :**
1. Inscription/login utilisateur (multi-tenant)
2. Dashboard liste produits
3. Publication produit sur Vinted (1 plateforme)
4. Génération description IA (OpenAI)
5. Gestion rate limiting (40 req/2h)
6. Extension navigateur (capture cookies Vinted)

**❌ Ce qui est EXCLU du MVP1 :**
- Autres plateformes (eBay, Etsy, etc.)
- Détourage images IA
- Analytics avancés
- Multi-utilisateurs (équipes)
- API publique
- PWA (Phase 2)

---

## 📅 Planning Détaillé (8 Semaines)

### Week 0 : Setup Infrastructure (5 jours)

**Jour 1-2 : Setup Projet**
```bash
# Créer structure projet
mkdir stoflow
cd stoflow

# Backend
mkdir -p backend/{api,models,services,repositories,workers,migrations}
python -m venv backend/venv
source backend/venv/bin/activate
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary redis rq python-jose passlib

# Frontend
npx nuxi@latest init frontend
cd frontend
npm install @sidebase/nuxt-auth primevue primeicons @pinia/nuxt

# Extension
mkdir extension
cd extension
# Structure WebExtension Firefox
```

**Jour 3-4 : Configuration Base**
- [ ] Setup PostgreSQL database `stoflow_db`
- [ ] Configuration Alembic
- [ ] Setup Redis (Docker compose)
- [ ] Configuration Nuxt (modules, primevue)
- [ ] Git repo + .gitignore

**Jour 5 : Tests Infrastructure**
- [ ] Test connexion PostgreSQL
- [ ] Test Redis connection
- [ ] Test build Frontend
- [ ] Documentation setup dans README.md

---

### Week 1-2 : Architecture Multi-Tenant (10 jours)

#### Week 1 : Backend Multi-Tenant Base

**Jour 1-2 : Models SQLAlchemy**
```python
# Models à créer :

# Schema public
- models/public/tenant.py
- models/public/user.py
- models/public/subscription.py
- models/public/platform_mapping.py

# Schema client (dynamique)
- models/tenant/product.py
- models/tenant/vinted_product.py
- models/tenant/publication_history.py
```

**Jour 3-4 : Migrations Alembic**
```bash
# À créer :
- alembic/env.py (multi-schema support)
- alembic/versions/001_create_public_schema.py
  * Table tenants
  * Table users
  * Table subscriptions
  * Table platform_mappings

- alembic/versions/002_create_client_schema_template.py
  * products
  * vinted_products
  * publication_history
  * ai_generations_log
```

**Jour 5 : Middleware Multi-Tenant**
```python
# backend/api/middleware/tenant.py
- get_tenant_id(request) -> int
- get_db(tenant_id) -> Session  # avec search_path
- verify_tenant_access(tenant_id, user_id) -> bool
```

#### Week 2 : API Authentification

**Jour 1-2 : Auth Backend**
```python
# backend/api/routes/auth.py
- POST /api/auth/register
  * Créer tenant
  * Créer schema client_{id}
  * Créer user admin
  * Retourner JWT

- POST /api/auth/login
  * Vérifier credentials
  * Retourner JWT avec tenant_id

- GET /api/auth/session
  * Vérifier JWT
  * Retourner user + tenant info
```

**Jour 3-4 : Services Auth**
```python
# backend/services/auth_service.py
- create_tenant(name, email, password)
- authenticate_user(email, password)
- create_access_token(data)
- verify_token(token)

# backend/services/tenant_service.py
- create_client_schema(tenant_id)
- migrate_client_schema(tenant_id)
```

**Jour 5 : Tests Auth + Documentation**
- [ ] Tests unitaires auth
- [ ] Tests création tenant
- [ ] Tests isolation schemas
- [ ] Documentation API (Swagger)

---

### Week 3 : API Produits + Frontend Base (7 jours)

#### Jour 1-2 : API Produits

```python
# backend/api/routes/products.py
- GET /api/products
  * Liste produits du tenant
  * Filtres : status, search
  * Pagination

- GET /api/products/{sku}
  * Détails produit

- POST /api/products
  * Créer produit (pour test)

- PUT /api/products/{sku}
  * Modifier produit

- DELETE /api/products/{sku}
  * Supprimer produit
```

#### Jour 3-4 : Frontend Nuxt - Pages Base

```vue
<!-- frontend/pages/index.vue -->
Landing page simple

<!-- frontend/pages/login.vue -->
Formulaire login avec @sidebase/nuxt-auth

<!-- frontend/pages/register.vue -->
Formulaire inscription

<!-- frontend/pages/dashboard/index.vue -->
Layout dashboard avec sidebar

<!-- frontend/pages/dashboard/products/index.vue -->
Liste produits (table PrimeVue)

<!-- frontend/pages/dashboard/products/[sku].vue -->
Détail produit
```

#### Jour 5-7 : Composants UI

```vue
<!-- frontend/components/ProductTable.vue -->
DataTable PrimeVue avec :
- Colonnes : Image, SKU, Titre, Prix, Statut, Actions
- Filtres, tri, pagination
- Actions : Voir, Publier, Supprimer

<!-- frontend/components/ProductCard.vue -->
Card produit avec preview image

<!-- frontend/components/StatsCards.vue -->
Cards statistiques dashboard
```

---

### Week 4 : Intégration Vinted (7 jours)

#### Jour 1-2 : Migration Code Vinted Existant

```python
# backend/services/vinted/
- vinted_client.py (réutiliser code actuel)
- vinted_product_converter.py
- vinted_mapping_service.py
- vinted_pricing_service.py
- vinted_validator.py

# Adapter pour multi-tenant :
- Cookies stockés par tenant
- Rate limiting par tenant
```

#### Jour 3-4 : API Publication Vinted

```python
# backend/api/routes/vinted.py
- POST /api/vinted/publish/{sku}
  * Valider produit
  * Mapper attributs
  * Calculer prix
  * Publier sur Vinted (async via RQ)
  * Retourner job_id

- GET /api/vinted/status/{job_id}
  * Statut publication (pending/success/error)

- GET /api/vinted/rate-limit
  * Retourner rate limit status
  * X/40 requêtes utilisées
  * Temps avant reset
```

#### Jour 5 : RQ Worker Publication

```python
# backend/workers/vinted_worker.py
@job('default', timeout=300)
def publish_product_to_vinted(tenant_id, sku, user_id):
    """
    1. Set search_path to client_{tenant_id}
    2. Récupérer produit
    3. Upload images
    4. Créer listing Vinted
    5. Sauvegarder vinted_product
    6. Log publication_history
    """
    pass
```

#### Jour 6-7 : Frontend Publication

```vue
<!-- frontend/pages/dashboard/products/[sku].vue -->
- Bouton "Publier sur Vinted"
- Modal confirmation avec preview
- Progress bar pendant publication
- Affichage résultat (success/error)

<!-- frontend/components/PublishModal.vue -->
- Preview produit
- Prix calculé Vinted
- Description générée (statique pour l'instant)
- Bouton confirmer
```

---

### Week 5 : Extension Navigateur (7 jours)

#### Jour 1-2 : Structure Extension

```
extension/
├── manifest.json (Firefox + Chrome compatible)
├── background.js (service worker)
├── content.js (inject dans vinted.fr)
├── popup/
│   ├── popup.html
│   ├── popup.js
│   └── popup.css
├── icons/
│   ├── icon-16.png
│   ├── icon-48.png
│   └── icon-128.png
└── README.md
```

#### Jour 3-4 : Capture Cookies Vinted

```javascript
// content.js
// Détecte connexion Vinted
// Extrait cookies + CSRF token + X-Anon-Id
// Envoie à background.js

// background.js
// Reçoit cookies depuis content.js
// Envoie à API backend (HTTPS)
// POST /api/vinted/cookies
```

#### Jour 5-6 : Popup Extension

```javascript
// popup.html/js
// Affiche statut connexion Vinted
// "Connecté en tant que @username"
// Bouton "Actualiser cookies"
// Bouton "Configurer API URL"
```

#### Jour 7 : Tests Extension
- [ ] Test installation Firefox
- [ ] Test capture cookies après login Vinted
- [ ] Test envoi API backend
- [ ] Test reconnexion automatique

---

### Week 6 : Intégration IA Descriptions (7 jours)

#### Jour 1-2 : Service OpenAI

```python
# backend/services/ai/openai_service.py
- generate_description(product, platform, tenant_id)
  * Hash attributs (cache key)
  * Check Redis cache
  * Si pas en cache → call OpenAI
  * Store in cache + PostgreSQL
  * Return description

# backend/services/ai/prompt_templates.py
- VINTED_PROMPT = """..."""
- EBAY_PROMPT = """...""" (Phase 2)
```

#### Jour 3-4 : API IA

```python
# backend/api/routes/ai.py
- POST /api/ai/generate-description
  * Body: { sku, platform, tone?, length? }
  * Return: { description, cached, cost }

- GET /api/ai/cache-stats
  * Hit rate, économies, etc.
```

#### Jour 5-6 : Frontend Génération IA

```vue
<!-- frontend/components/AIDescriptionGenerator.vue -->
- Textarea description
- Bouton "Générer avec IA"
- Loading state
- Sélecteur ton (friendly/formal/fun)
- Sélecteur longueur (short/medium/long)
- Preview temps réel
```

#### Jour 7 : Cache Redis + Tests
- [ ] Setup cache Redis avec TTL
- [ ] Tests hit rate
- [ ] Tests coûts OpenAI
- [ ] Monitoring logs

---

### Week 7 : Rate Limiting + Monitoring (7 jours)

#### Jour 1-2 : Rate Limiting Global

```python
# backend/services/rate_limiter.py
- check_rate_limit(tenant_id, platform)
- increment_counter(tenant_id, platform)
- get_remaining(tenant_id, platform)
- get_reset_time(tenant_id, platform)

# Redis keys:
# rate_limit:vinted:{tenant_id}:mutating
# rate_limit:vinted:{tenant_id}:timestamps
```

#### Jour 3-4 : Frontend Rate Limit Display

```vue
<!-- frontend/components/RateLimitBadge.vue -->
- Badge "15/40 requêtes" avec couleur
  * Vert : < 30
  * Orange : 30-38
  * Rouge : 38-40
- Tooltip "Reset dans 1h32"

<!-- frontend/components/RateLimitWarning.vue -->
- Alerte si proche limite
- Compte à rebours avant reset
```

#### Jour 5-6 : Logging & Monitoring

```python
# backend/services/monitoring/
- log_publication(tenant_id, sku, platform, status)
- log_error(tenant_id, operation, error)
- get_tenant_stats(tenant_id)

# Tables :
- publication_history (already created)
- error_logs
```

#### Jour 7 : Dashboard Stats

```vue
<!-- frontend/pages/dashboard/stats.vue -->
- Cards :
  * Produits publiés aujourd'hui
  * Taux succès
  * Rate limit status
  * Erreurs récentes
- Charts PrimeVue :
  * Publications par jour (7 derniers jours)
  * Plateformes utilisées
```

---

### Week 8 : Tests + Documentation + Polish (7 jours)

#### Jour 1-2 : Tests Backend

```python
# tests/test_auth.py
- test_register_creates_tenant_and_schema()
- test_login_returns_jwt()
- test_jwt_contains_tenant_id()

# tests/test_products.py
- test_list_products_isolated_by_tenant()
- test_create_product()
- test_update_product()

# tests/test_vinted.py
- test_publish_product_to_vinted()
- test_rate_limiting()

# tests/test_ai.py
- test_generate_description()
- test_cache_hit()
```

#### Jour 3-4 : Tests Frontend

```typescript
// tests/auth.spec.ts
- test login flow
- test registration flow
- test JWT storage

// tests/products.spec.ts
- test product list display
- test product detail view
- test publish button

// tests/extension.spec.ts
- test cookie capture
- test API sending
```

#### Jour 5 : Documentation

```markdown
# À créer :
- README.md (setup projet)
- DEPLOYMENT.md (déploiement production)
- API_DOCS.md (endpoints API)
- EXTENSION_INSTALL.md (installer extension)
- USER_GUIDE.md (guide utilisateur)
```

#### Jour 6-7 : Polish UI + Fixes

- [ ] Responsive design mobile
- [ ] Loading states partout
- [ ] Error handling UX
- [ ] Messages success/error
- [ ] Animations transitions
- [ ] Performance audit
- [ ] Accessibility (a11y)
- [ ] Derniers bugs fixes

---

## 📂 Structure Finale du Projet

```
stoflow/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py              # Multi-tenant middleware
│   │   │   └── auth.py                # JWT verification
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py                # POST /auth/register, /auth/login
│   │       ├── products.py            # CRUD produits
│   │       ├── vinted.py              # POST /vinted/publish
│   │       └── ai.py                  # POST /ai/generate-description
│   ├── models/
│   │   ├── __init__.py
│   │   ├── public/                    # Models schema public
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py
│   │   │   ├── user.py
│   │   │   └── platform_mapping.py
│   │   └── tenant/                    # Models schema client_X
│   │       ├── __init__.py
│   │       ├── product.py
│   │       ├── vinted_product.py
│   │       └── publication_history.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── tenant_service.py
│   │   ├── rate_limiter.py
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── openai_service.py
│   │   │   └── prompt_templates.py
│   │   └── vinted/
│   │       ├── __init__.py
│   │       ├── vinted_client.py       # Réutilisé depuis code actuel
│   │       ├── vinted_converter.py
│   │       ├── vinted_mapping.py
│   │       ├── vinted_pricing.py
│   │       └── vinted_validator.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── tenant_repository.py
│   │   ├── user_repository.py
│   │   ├── product_repository.py
│   │   └── vinted_repository.py
│   ├── workers/
│   │   ├── __init__.py
│   │   └── vinted_worker.py           # RQ worker publication
│   ├── migrations/                    # Alembic
│   │   ├── alembic.ini
│   │   ├── env.py                     # Multi-schema support
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 001_create_public_schema.py
│   │       └── 002_create_client_schema_template.py
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── config.py                  # Configuration env vars
│   │   ├── db.py                      # Database session
│   │   └── logging_setup.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_products.py
│   │   ├── test_vinted.py
│   │   └── test_ai.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── pages/
│   │   ├── index.vue                  # Landing page
│   │   ├── login.vue
│   │   ├── register.vue
│   │   └── dashboard/
│   │       ├── index.vue              # Dashboard home
│   │       ├── products/
│   │       │   ├── index.vue          # Liste produits
│   │       │   └── [sku].vue          # Détail produit
│   │       └── stats.vue              # Statistiques
│   ├── components/
│   │   ├── ProductTable.vue
│   │   ├── ProductCard.vue
│   │   ├── PublishModal.vue
│   │   ├── AIDescriptionGenerator.vue
│   │   ├── RateLimitBadge.vue
│   │   ├── RateLimitWarning.vue
│   │   └── StatsCards.vue
│   ├── composables/
│   │   ├── useAuth.ts
│   │   ├── useProducts.ts
│   │   ├── useVinted.ts
│   │   └── useAI.ts
│   ├── layouts/
│   │   ├── default.vue
│   │   └── dashboard.vue
│   ├── middleware/
│   │   └── auth.ts                    # Route protection
│   ├── stores/
│   │   ├── auth.ts                    # Pinia store
│   │   └── products.ts
│   ├── nuxt.config.ts
│   ├── package.json
│   └── README.md
│
├── extension/
│   ├── manifest.json                  # Firefox + Chrome
│   ├── background.js                  # Service worker
│   ├── content.js                     # Inject vinted.fr
│   ├── popup/
│   │   ├── popup.html
│   │   ├── popup.js
│   │   └── popup.css
│   ├── icons/
│   │   ├── icon-16.png
│   │   ├── icon-48.png
│   │   └── icon-128.png
│   └── README.md
│
├── docker-compose.yml                 # PostgreSQL + Redis
├── .gitignore
└── README.md                          # Documentation projet global
```

---

## 🔧 Configuration Requise

### Services Infrastructure

**PostgreSQL 14+**
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: stoflow_db
      POSTGRES_USER: stoflow
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

**Redis 7+**
```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

### Variables d'Environnement

**Backend (.env)**
```bash
# Database
DATABASE_URL=postgresql://stoflow:password@localhost:5432/stoflow_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# OpenAI
OPENAI_API_KEY=sk-...

# Vinted (defaults)
VINTED_RATE_LIMIT_MAX=40
VINTED_RATE_LIMIT_WINDOW_HOURS=2
VINTED_REQUEST_DELAY_MIN=20
VINTED_REQUEST_DELAY_MAX=50
```

**Frontend (.env)**
```bash
NUXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 Démarrage Développement

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

pip install -r requirements.txt

# Setup database
docker-compose up -d postgres redis

# Migrations
alembic upgrade head

# Créer tenant demo
python scripts/create_demo_tenant.py

# Run API
uvicorn api.main:app --reload --port 8000

# Run RQ worker (autre terminal)
rq worker --url redis://localhost:6379
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Ouvre http://localhost:3000
```

### Extension

```bash
# Firefox
1. about:debugging
2. "This Firefox" → "Load Temporary Add-on"
3. Sélectionner extension/manifest.json

# Chrome
1. chrome://extensions
2. Mode développeur ON
3. "Load unpacked"
4. Sélectionner dossier extension/
```

---

## ✅ Critères d'Acceptation MVP1

### Fonctionnalités Obligatoires

**Auth Multi-Tenant**
- [ ] Inscription crée tenant + schema client_X
- [ ] Login retourne JWT avec tenant_id
- [ ] Isolation données entre tenants garantie

**Dashboard Produits**
- [ ] Liste produits avec filtres/tri/pagination
- [ ] Vue détail produit avec toutes infos
- [ ] Responsive mobile

**Publication Vinted**
- [ ] Bouton publier déclenche worker RQ
- [ ] Upload images automatique
- [ ] Mapping attributs correct
- [ ] Prix calculé selon algorithme
- [ ] Affichage résultat (success/erreur)

**Extension Navigateur**
- [ ] Capture cookies après login Vinted
- [ ] Envoi automatique à API
- [ ] Popup affiche statut connexion

**IA Descriptions**
- [ ] Génération description via OpenAI
- [ ] Cache Redis fonctionnel (hit >70%)
- [ ] Preview temps réel
- [ ] Personnalisation ton/longueur

**Rate Limiting**
- [ ] Respect limite 40 req/2h par compte Vinted
- [ ] Affichage compteur temps réel
- [ ] Warning proche limite
- [ ] Blocage si limite atteinte

### Performance

- [ ] Page load <2s (dashboard)
- [ ] API response <500ms (liste produits)
- [ ] Publication Vinted <60s (si tout OK)

### Sécurité

- [ ] JWT expiration fonctionnelle
- [ ] Passwords hashés (bcrypt)
- [ ] CORS configuré correctement
- [ ] SQL injection impossible (parameterized queries)
- [ ] Cookies Vinted chiffrés en BDD

---

## 📊 Métriques Succès MVP1

### KPIs Techniques

| Métrique | Target | Mesure |
|----------|--------|--------|
| **Uptime API** | >99% | Monitoring |
| **Response time** | <500ms | Logs API |
| **Rate limit respect** | 100% | Redis logs |
| **Cache hit rate** | >70% | Redis stats |
| **Publications réussies** | >95% | BDD |

### KPIs Business

| Métrique | Target | Mesure |
|----------|--------|--------|
| **Beta-testers inscrits** | 5-10 | BDD tenants |
| **Produits publiés** | 50+ | BDD publications |
| **Taux satisfaction** | >4/5 | Feedback form |
| **Bugs critiques** | 0 | GitHub issues |

---

## 🐛 Gestion Bugs & Issues

### Priorités

**P0 - Bloquant (Fix <24h)**
- Connexion impossible
- Publications échouent toutes
- Perte de données

**P1 - Majeur (Fix <3 jours)**
- Feature principale cassée
- Performance dégradée
- Bug impactant UX

**P2 - Mineur (Fix <1 semaine)**
- UI glitch
- Feature secondaire
- Edge case

**P3 - Nice-to-have (Backlog)**
- Améliorations UI
- Optimisations
- Features futures

### Process

1. Bug reporté → GitHub issue
2. Label priorité (P0/P1/P2/P3)
3. Assign développeur
4. Fix → PR → Review
5. Merge → Deploy
6. Vérifier fix → Close issue

---

## 🎓 Documentation à Créer

### Développeur

- [ ] **README.md** - Setup projet
- [ ] **CONTRIBUTING.md** - Guidelines contribution
- [ ] **API_DOCS.md** - Documentation API complète
- [ ] **DATABASE.md** - Schéma BDD + migrations
- [ ] **DEPLOYMENT.md** - Déploiement production

### Utilisateur

- [ ] **USER_GUIDE.md** - Guide utilisateur complet
- [ ] **EXTENSION_INSTALL.md** - Installer extension
- [ ] **QUICKSTART.md** - Démarrage rapide (5min)
- [ ] **FAQ.md** - Questions fréquentes
- [ ] **TROUBLESHOOTING.md** - Résolution problèmes

### Business

- [ ] **PRODUCT_SPEC.md** - Spécifications produit
- [ ] **ROADMAP.md** - Roadmap Phase 2+
- [ ] **PRICING.md** - Stratégie pricing finalisée

---

## 🚦 Go/No-Go Checklist Final

### Avant Beta-Test

**Technique**
- [ ] Tous les tests unitaires passent
- [ ] Tests end-to-end passent
- [ ] Aucun bug P0 ouvert
- [ ] Performance conforme aux targets
- [ ] Sécurité auditée

**Produit**
- [ ] Toutes les features MVP1 fonctionnelles
- [ ] UX validée en interne
- [ ] Documentation utilisateur complète
- [ ] Extension installable facilement

**Business**
- [ ] 5 beta-testers identifiés
- [ ] Process feedback en place
- [ ] Support email configuré
- [ ] Metrics tracking configuré

### Avant Production (Post-Beta)

- [ ] Feedback beta intégré
- [ ] Bugs critiques fixés
- [ ] Infrastructure production ready
- [ ] Monitoring/alerting configuré
- [ ] Backup strategy en place
- [ ] Plan rollback défini

---

## 📈 Après MVP1 : Prochaines Étapes

### Phase 2 (Mois 3-5)

**Plateformes**
1. eBay (OAuth2 + API)
2. Etsy (OAuth2 + API)
3. Leboncoin (extension cookies)

**Features**
- Import WooCommerce automatique
- Analytics avancés
- PWA mobile

### Phase 3 (Mois 6-9)

**Advanced Features**
- Détourage images IA
- Multi-utilisateurs (équipes B2B)
- API publique
- Webhooks
- White-label partiel

---

## 💡 Conseils Développement

### Best Practices

**Code Quality**
- ✅ Type hints Python partout
- ✅ TypeScript strict mode
- ✅ Linting (black, eslint)
- ✅ Pre-commit hooks
- ✅ Code review obligatoire

**Git Workflow**
```bash
main (production)
├── develop (staging)
│   ├── feature/auth-multi-tenant
│   ├── feature/vinted-publish
│   └── feature/ai-descriptions
```

**Commit Messages**
```
feat: add vinted publication endpoint
fix: rate limiting not working correctly
docs: update API documentation
test: add unit tests for auth service
```

**Tests**
- Minimum 80% coverage backend
- Tests E2E pour flows critiques
- Tests manuels avant chaque release

### Éviter les Pièges

**❌ À NE PAS FAIRE**
- Optimiser prématurément
- Ajouter features hors MVP1
- Ignorer les tests
- Négliger la documentation
- Coder sans comprendre le besoin

**✅ À FAIRE**
- Itérer rapidement
- Tester souvent
- Documenter au fur et à mesure
- Demander feedback tôt
- Garder le code simple

---

## 📞 Support & Communication

### Canaux

- **GitHub Issues** : Bugs & features requests
- **Email** : support@stoflow.io (à créer)
- **Discord** : Serveur communauté beta (optionnel)

### Réunions

**Daily Standup (si équipe)**
- Hier : quoi fait ?
- Aujourd'hui : quoi prévu ?
- Blocages ?

**Weekly Review**
- Demo features terminées
- Review roadmap
- Priorisation semaine suivante

---

## ✨ Conclusion

**MVP1 = 8 semaines pour :**
- ✅ Dashboard multi-tenant fonctionnel
- ✅ Publication Vinted automatisée
- ✅ IA génération descriptions
- ✅ Extension navigateur
- ✅ 5-10 beta-testers validant le concept

**Après MVP1 :**
→ Feedback beta
→ Itération features
→ Ajout plateformes (eBay, Etsy)
→ Préparation lancement commercial

**Succès si :**
- 95%+ publications réussies
- 4/5+ satisfaction beta-testers
- 0 bugs critiques
- Architecture scalable validée

---

**Document créé le :** 2025-12-04
**Durée estimée :** 8 semaines (56 jours)
**Équipe recommandée :** 1-2 devs full-stack
**Budget infra :** ~15€/mois (dev), ~50€/mois (prod)

🚀 **Ready to build !**

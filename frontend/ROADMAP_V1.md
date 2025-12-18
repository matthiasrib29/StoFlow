# 🚀 Roadmap V1 - Stoflow

## 🎯 Vision V1
**Objectif** : Permettre aux vendeurs de gérer leurs produits depuis un seul endroit et de les publier rapidement sur plusieurs plateformes (Vinted + 1 autre plateforme au choix).

**Priorités business** :
1. ⏱️ Gagner du temps sur la publication multi-plateformes
2. 📦 Centraliser la gestion des produits
3. 🔄 Synchroniser les stocks automatiquement

---

## ✅ Fonctionnalités Essentielles (MUST HAVE)

### 1. 👤 Authentification & Multi-Tenant
**Status** : ✅ Déjà implémenté (frontend)
- [x] Login / Register
- [x] JWT Authentication
- [x] Isolation par tenant
- [ ] **À FAIRE** : Connexion backend API réelle (actuellement mock)
- [ ] **À FAIRE** : Gestion des rôles (admin/utilisateur)

**Estimation** : 2-3 jours backend

---

### 2. 📦 Gestion des Produits (CRUD)

#### Frontend ✅ Déjà fait
- [x] Liste des produits avec filtres
- [x] Création de produit avec formulaire complet
- [x] Upload de photos
- [x] Édition de produit
- [x] Suppression de produit
- [x] Vue détaillée produit

#### Backend ⚠️ À faire
- [ ] **API Produits** :
  - `POST /api/products` - Créer un produit
  - `GET /api/products` - Liste avec pagination + filtres
  - `GET /api/products/{sku}` - Détail d'un produit
  - `PUT /api/products/{sku}` - Modifier un produit
  - `DELETE /api/products/{sku}` - Supprimer un produit

- [ ] **Gestion des photos** :
  - Upload vers S3/Cloudinary/stockage local
  - Redimensionnement automatique
  - Compression d'images

- [ ] **Champs produit** :
  ```python
  {
    "title": str,
    "description": str,
    "price": float,
    "stock_quantity": int,
    "sku": str (auto-généré),
    "category": str,
    "brand": str,
    "size": str (optionnel),
    "color": str (optionnel),
    "condition": str,
    "images": List[str],  # URLs
    "is_active": bool,
    "tenant_id": str
  }
  ```

**Estimation** : 3-4 jours

---

### 3. 🔌 Intégrations Plateformes

#### 3.1 Architecture d'intégration
- [ ] **Système de connexion OAuth** :
  - Stocker tokens par tenant et plateforme
  - Refresh automatique des tokens
  - Gestion des erreurs d'authentification

- [ ] **Abstraction plateforme** :
  ```python
  class PlatformAdapter:
      def connect(credentials) -> bool
      def publish_product(product) -> publication_id
      def update_product(publication_id, product)
      def delete_product(publication_id)
      def sync_stock(publication_id, quantity)
      def get_stats() -> dict
  ```

**Estimation** : 2-3 jours

#### 3.2 Plateforme #1 : Vinted 🛍️
- [ ] **Connexion Vinted** :
  - Authentification via API Vinted
  - Stockage sécurisé des credentials

- [ ] **Publication sur Vinted** :
  - Créer une annonce depuis un produit Stoflow
  - Mapper les champs (titre, description, prix, photos, taille, marque)
  - Gérer les catégories Vinted

- [ ] **Synchronisation** :
  - Mettre à jour le stock quand vendu sur Vinted
  - Webhook pour notifications de vente
  - Statut de publication (actif/vendu/supprimé)

**Estimation** : 5-7 jours (dépend de la complexité de l'API Vinted)

#### 3.3 Plateforme #2 : eBay ou Facebook Marketplace
**À décider** : Quelle plateforme prioriser après Vinted ?

**eBay** :
- ✅ API bien documentée
- ✅ SDK officiel Python
- ⚠️ Processus OAuth complexe
- Estimation : 5-7 jours

**Facebook Marketplace** :
- ✅ Large audience
- ⚠️ API limitée / instable
- ⚠️ Risque de changements fréquents
- Estimation : 7-10 jours

**Recommandation** : eBay pour la stabilité et la documentation

---

### 4. 📊 Publications Multi-Plateformes

#### Frontend ✅ Partiellement fait
- [x] Page liste des publications
- [ ] **À améliorer** : Formulaire de publication multi-plateformes
- [ ] **À créer** : Sélection des plateformes cibles
- [ ] **À créer** : Prévisualisation avant publication

#### Backend
- [ ] **API Publications** :
  - `POST /api/publications` - Publier sur une/plusieurs plateformes
  - `GET /api/publications` - Liste des publications
  - `PUT /api/publications/{id}` - Modifier une publication
  - `DELETE /api/publications/{id}` - Supprimer d'une plateforme

- [ ] **Logique de publication** :
  ```python
  {
    "product_id": str,
    "platforms": ["vinted", "ebay"],
    "platform_specific_data": {
      "vinted": {"category_id": 123, "color_id": 5},
      "ebay": {"listing_type": "FixedPrice", "duration": 7}
    }
  }
  ```

- [ ] **Job asynchrone** :
  - File d'attente (Celery/RQ) pour publications
  - Retry en cas d'échec
  - Notifications de succès/échec

**Estimation** : 4-5 jours

---

### 5. 🔄 Synchronisation des Stocks

- [ ] **Webhook listener** :
  - Endpoint pour recevoir notifications des plateformes
  - Vérification signature/authenticité

- [ ] **Logique de sync** :
  - Quand vendu sur une plateforme → décrémenter stock Stoflow
  - Si stock = 0 → retirer automatiquement des autres plateformes
  - Si stock mis à jour manuellement → sync vers toutes les plateformes

- [ ] **Historique** :
  - Log de toutes les synchronisations
  - Détection de conflits (vente simultanée sur 2 plateformes)

**Estimation** : 3-4 jours

---

### 6. 📱 Dashboard & Vue d'ensemble

#### Frontend ✅ Fait
- [x] Stats globales (produits, publications, ventes)
- [x] Vue d'ensemble des plateformes
- [x] Quick actions
- [x] Recent activity

#### Backend
- [ ] **API Stats** :
  - `GET /api/stats/overview` - Stats globales
  - `GET /api/stats/platforms` - Stats par plateforme
  - `GET /api/stats/products` - Top produits

- [ ] **Calculs** :
  - Nombre total de publications actives
  - Nombre de ventes ce mois
  - Chiffre d'affaires
  - Taux de conversion par plateforme

**Estimation** : 2-3 jours

---

## 🎨 Features Nice-to-Have (V1.1 ou V2)

Ces fonctionnalités ne sont PAS critiques pour la V1 mais peuvent être ajoutées rapidement après :

- [ ] **Notifications** :
  - Email quand produit vendu
  - Push notification pour vente

- [ ] **Templates de description** :
  - Sauvegarder des templates réutilisables
  - Variables dynamiques (marque, taille, etc.)

- [ ] **Import en masse** :
  - CSV upload pour créer plusieurs produits
  - Import depuis une plateforme existante

- [ ] **Analytics avancés** :
  - Graphiques de ventes
  - Performances par catégorie
  - Comparaison plateformes

- [ ] **Gestion des commandes** :
  - Statut d'expédition
  - Numéro de tracking
  - Communication acheteur

---

## 📋 Checklist Technique

### Backend (FastAPI)
- [ ] Connexion base de données PostgreSQL
- [ ] Migrations Alembic
- [ ] Authentification JWT complète
- [ ] Tests unitaires (coverage > 70%)
- [ ] Documentation API (OpenAPI/Swagger)
- [ ] Rate limiting
- [ ] CORS configuration
- [ ] Logging (Sentry ou équivalent)
- [ ] Variables d'environnement (.env)

### Frontend (Nuxt 4)
- [ ] Connexion API backend (remplacer mocks)
- [ ] Gestion d'erreurs globale
- [ ] Loading states
- [ ] Validation formulaires
- [ ] Upload fichiers
- [ ] Tests e2e (Playwright)
- [ ] SEO basique
- [ ] Performance optimization

### DevOps
- [ ] Docker compose pour dev
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Deployment staging
- [ ] Deployment production
- [ ] Monitoring (uptime, performance)
- [ ] Backups base de données

---

## 🗓️ Planning Suggéré (Sans Deadline Stricte)

### Phase 1 : Fondations (Semaines 1-2)
1. ✅ Setup projet (fait)
2. Connexion backend-frontend
3. API Produits complète
4. Upload photos

### Phase 2 : Première Intégration (Semaines 3-4)
1. Architecture abstraction plateformes
2. Intégration Vinted complète
3. Publication basique

### Phase 3 : Sync & Multi-Plateformes (Semaines 5-6)
1. Système de synchronisation stocks
2. Deuxième plateforme (eBay)
3. Publication multi-plateformes

### Phase 4 : Polish & Tests (Semaine 7)
1. Tests complets
2. Fix bugs
3. Documentation
4. Déploiement

---

## ❓ Questions à Résoudre

Avant de commencer le développement, il faut clarifier :

1. **🤔 QUESTION IMPORTANTE - Plateforme #2** :
   - eBay (API stable, bien documentée) ?
   - Facebook Marketplace (grande audience, API limitée) ?
   - Etsy (marché de niche, bon pour artisanat) ?

2. **🤔 QUESTION - Stockage photos** :
   - AWS S3 (payant, scalable) ?
   - Cloudinary (payant, features image) ?
   - Stockage local (gratuit, limité) ?

3. **🤔 QUESTION - Base de données** :
   - PostgreSQL (recommandé pour prod) ?
   - SQLite (suffisant pour début) ?

4. **🤔 QUESTION - Hébergement** :
   - VPS (OVH, DigitalOcean) ?
   - PaaS (Heroku, Railway, Render) ?
   - Serverless (Vercel + Supabase) ?

5. **🤔 QUESTION - Tarification V1** :
   - Gratuit pendant beta ?
   - Freemium (limite publications) ?
   - Abonnement dès le début ?

---

## 📊 Estimation Totale V1

**Backend** : ~20-25 jours de dev
**Frontend** : ~5-7 jours de dev (déjà bien avancé)
**Tests & Polish** : ~5 jours
**DevOps** : ~3 jours

**TOTAL** : ~35-40 jours de développement effectif

Avec une personne à temps plein : **7-8 semaines**
Avec travail partiel (50%) : **3-4 mois**

---

## 🎯 Critères de Succès V1

La V1 est prête quand :

✅ Un utilisateur peut :
1. Créer un compte et se connecter
2. Ajouter un produit avec photos
3. Connecter son compte Vinted
4. Publier le produit sur Vinted en 1 clic
5. Voir le produit publié sur Vinted
6. Quand vendu sur Vinted → stock mis à jour automatiquement dans Stoflow

✅ Technique :
1. API backend fonctionne en production
2. Frontend déployé et accessible
3. Base de données backupée
4. Monitoring en place
5. Documentation basique disponible

---

**Date de création** : 5 décembre 2024
**Dernière mise à jour** : 5 décembre 2024
**Propriétaire** : Matheus Ribeiro
